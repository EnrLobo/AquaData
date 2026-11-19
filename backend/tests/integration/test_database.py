"""Regras garantidas pelo próprio banco PostgreSQL e migrations (AQ-24).

Aqui os dados vão direto pelo SQLAlchemy, sem a API, para confirmar que o banco
recusa o que a API já recusa (defesa em profundidade) e que as chaves
estrangeiras se comportam como na modelagem (AQ-7).
"""

from datetime import date
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import Athlete, Coach, Sex, SessionType, Stroke, TrainingSession

BACKEND_DIR = Path(__file__).resolve().parents[2]


def treinador_e_atleta(db):
    coach = Coach(name="Treinador", email="banco@teste.com", password_hash="x")
    db.add(coach)
    db.flush()
    athlete = Athlete(coach_id=coach.id, name="Atleta", birth_date=date(2009, 1, 1), sex=Sex.MALE)
    db.add(athlete)
    db.flush()
    return coach, athlete


def treino(athlete_id: int, **extra) -> TrainingSession:
    dados = dict(
        athlete_id=athlete_id, session_date=date(2026, 11, 1), session_type=SessionType.TRAINING,
        stroke=Stroke.FREESTYLE, pool_length_m=25, distance_m=100, total_time_s=60,
        stroke_count=40, total_cycle_count=50, swim_distance_m=60, swim_time_s=40,
    )
    dados.update(extra)
    return TrainingSession(**dados)


def test_migrations_estao_na_ultima_versao(engine):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    head = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect() as connection:
        versao = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert versao == head


@pytest.mark.parametrize(
    "invalido",
    [{"pool_length_m": 30}, {"distance_m": 0}, {"total_time_s": 0}, {"total_cycle_count": 0}],
)
def test_banco_recusa_valores_invalidos(db, invalido):
    _, athlete = treinador_e_atleta(db)
    db.add(treino(athlete.id, **invalido))
    with pytest.raises(IntegrityError):
        db.flush()


def test_enum_e_gravado_pelo_valor(db):
    _, athlete = treinador_e_atleta(db)
    db.add(treino(athlete.id, stroke=Stroke.BREASTSTROKE))
    db.flush()
    valor = db.execute(text("SELECT stroke FROM training_sessions")).scalar_one()
    assert valor == "breaststroke"  # não "BREASTSTROKE" (correção do AQ-7)


def test_apagar_atleta_apaga_os_treinos_e_treinador_com_atletas_nao_pode_ser_apagado(db):
    coach, athlete = treinador_e_atleta(db)
    db.add(treino(athlete.id))
    db.commit()

    # CASCADE: direto no SQL, sem a ajuda do ORM
    db.execute(text("DELETE FROM athletes WHERE id = :id"), {"id": athlete.id})
    db.commit()
    assert db.execute(text("SELECT count(*) FROM training_sessions")).scalar_one() == 0

    # RESTRICT: treinador com atleta não pode ser apagado
    outro = Athlete(coach_id=coach.id, name="Outro", birth_date=date(2010, 1, 1), sex=Sex.FEMALE)
    db.add(outro)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text("DELETE FROM coaches WHERE id = :id"), {"id": coach.id})
        db.commit()