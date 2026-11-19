"""Testes de integração (AQ-24): API (FastAPI) + banco PostgreSQL de teste.

As requisições passam pela API de verdade (rotas, validação, autenticação JWT,
isolamento por treinador) e gravam num banco PostgreSQL separado, criado pelas
próprias migrations do Alembic.

Precisam da variável TEST_DATABASE_URL (no ambiente ou no backend/.env)
apontando para um banco cujo nome termina em "_test"
(ex.: postgresql+psycopg://aquadata:SENHA@localhost:5432/aquadata_test). Sem ela,
estes testes são pulados localmente e os testes unitários rodam normalmente; no
CI (GitHub Actions), a falta dela é erro. O banco de teste é apagado e recriado a
cada execução: nunca aponte para o banco de desenvolvimento.
"""

import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
PASSWORD = "senha-de-teste-123"


def _env_file_value(name: str) -> str | None:
    """Lê uma variável do backend/.env (o mesmo arquivo da aplicação), se existir."""
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key.strip() == name:
            return value.strip().strip('"').strip("'") or None
    return None


def _test_database_url() -> str | None:
    url = os.getenv("TEST_DATABASE_URL") or _env_file_value("TEST_DATABASE_URL")
    if not url:
        return None
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg://" + url[len(prefix):]
    return url


def _alembic_config(connection) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.attributes["connection"] = connection
    return config


@pytest.fixture(scope="session")
def engine():
    """Banco de teste recriado pelas migrations (base → head → base → head)."""
    url = _test_database_url()
    if url is None:
        if os.getenv("CI"):  # no GitHub Actions, pular seria esconder uma falha
            pytest.fail("TEST_DATABASE_URL não definida no CI")
        pytest.skip("TEST_DATABASE_URL não definida: testes de integração pulados")
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        pytest.exit(
            f'O banco de teste precisa terminar em "_test" (recebido: "{database}"); '
            "ele é apagado a cada execução.",
            returncode=1,
        )

    engine = create_engine(url)
    # começa do zero e confere que as migrations sobem e descem sem erro (reversíveis)
    for target, step in (("base", "downgrade"), ("head", "upgrade"),
                         ("base", "downgrade"), ("head", "upgrade")):
        with engine.begin() as connection:
            getattr(command, step)(_alembic_config(connection), target)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(engine):
    """Cada teste começa com as tabelas vazias."""
    yield
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE training_sessions, athletes, coaches RESTART IDENTITY CASCADE")
        )


@pytest.fixture
def db(engine):
    """Sessão do SQLAlchemy no banco de teste (para conferir o que foi gravado)."""
    session = sessionmaker(bind=engine, autoflush=False)()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(engine):
    """Cliente HTTP da API, com o banco trocado pelo banco de teste."""
    from app.core.database import get_db
    from app.main import app

    testing_session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class Api:
    """Atalhos para montar os cenários pela própria API."""

    password = PASSWORD

    def __init__(self, client: TestClient):
        self.client = client

    def coach(self, email: str = "treinador@teste.com", name: str = "Treinador Teste") -> dict:
        """Cadastra um treinador, faz login e devolve o cabeçalho com o token."""
        response = self.client.post(
            "/auth/register", json={"name": name, "email": email, "password": PASSWORD}
        )
        assert response.status_code == 201, response.text
        response = self.client.post(
            "/auth/login", data={"username": email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def athlete(self, headers: dict, name: str = "Atleta Teste", **extra) -> dict:
        body = {"name": name, "birth_date": "2009-05-10", "sex": "M", **extra}
        response = self.client.post("/athletes", json=body, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    def session(self, headers: dict, athlete_id: int, days_ago: int = 1, **extra):
        """Registra um treino (100 m livre, piscina de 25 m) e devolve a resposta."""
        body = {
            "session_date": (date.today() - timedelta(days=days_ago)).isoformat(),
            "session_type": "training",
            "stroke": "freestyle",
            "pool_length_m": 25,
            "distance_m": 100,
            "total_time_s": 60.0,
            "stroke_count": 40,
            "total_cycle_count": 50,
            "swim_distance_m": 60.0,
            "swim_time_s": 40.0,
            **extra,
        }
        return self.client.post(f"/athletes/{athlete_id}/sessions", json=body, headers=headers)

    def series(self, headers: dict, athlete_id: int, times: list[float], competitions=()):
        """Registra uma série em dias seguidos, terminando ontem.

        `competitions` lista as ordens (1, 2...) que são competição.
        """
        n = len(times)
        for order, time_s in enumerate(times, start=1):
            response = self.session(
                headers,
                athlete_id,
                days_ago=n - order + 1,
                total_time_s=time_s,
                session_type="competition" if order in competitions else "training",
            )
            assert response.status_code == 201, response.text


@pytest.fixture
def api(client) -> Api:
    return Api(client)