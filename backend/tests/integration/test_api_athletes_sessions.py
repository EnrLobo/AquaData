"""Atletas e treinos de ponta a ponta: API, validação, banco e métricas (AQ-24)."""

import pytest

from app.models import TrainingSession


def test_cadastro_e_busca_de_atletas(api, client):
    headers = api.coach()
    api.athlete(headers, name="  Maria   da Silva ")  # espaços normalizados
    api.athlete(headers, name="João Pedro")
    response = client.get("/athletes", params={"search": "mar"}, headers=headers)
    assert response.status_code == 200
    assert [a["name"] for a in response.json()] == ["Maria da Silva"]  # ILIKE do PostgreSQL


def test_atleta_duplicado_e_recusado(api, client):
    headers = api.coach()
    api.athlete(headers, name="Carla Dias")
    response = client.post(
        "/athletes",
        json={"name": "carla dias", "birth_date": "2009-05-10", "sex": "M"},
        headers=headers,
    )
    assert response.status_code == 409  # mesmo nome (sem diferenciar maiúsculas) e nascimento


def test_um_treinador_nao_ve_os_dados_de_outro(api, client):
    a = api.coach(email="a@teste.com")
    b = api.coach(email="b@teste.com")
    atleta = api.athlete(a)
    assert api.session(a, atleta["id"]).status_code == 201

    assert client.get("/athletes", headers=b).json() == []
    for path in (
        f"/athletes/{atleta['id']}",
        f"/athletes/{atleta['id']}/sessions",
        f"/athletes/{atleta['id']}/performance",
        f"/athletes/{atleta['id']}/report",
    ):
        assert client.get(path, headers=b).status_code == 404, path  # 404, não 403
    assert client.get("/sessions", headers=b).json()["total"] == 0
    assert api.session(b, atleta["id"]).status_code == 404  # não grava no atleta de outro


def test_treino_e_gravado_e_as_metricas_sao_calculadas_na_consulta(api, client, db):
    headers = api.coach()
    atleta = api.athlete(headers)
    # 100 m em 60 s; trecho de nado puro de 60 m em 40 s com 40 ciclos; 50 ciclos na prova
    response = api.session(headers, atleta["id"], notes="treino de teste")
    assert response.status_code == 201
    criado = response.json()

    gravado = db.get(TrainingSession, criado["id"])
    assert float(gravado.total_time_s) == 60.0
    assert gravado.total_cycle_count == 50
    assert gravado.notes == "treino de teste"

    metricas = client.get(
        f"/athletes/{atleta['id']}/sessions/{criado['id']}", headers=headers
    ).json()["metrics"]
    assert metricas["vm"] == pytest.approx(100 / 60, abs=0.01)  # 1,67 m/s
    assert metricas["vn"] == pytest.approx(1.5)  # 60 ÷ 40
    assert metricas["cb"] == pytest.approx(1.5)  # 60 ÷ 40
    assert metricas["cn"] == pytest.approx(60.0)  # 40 ÷ 40 × 60
    assert metricas["swim_index"] == pytest.approx(2.25)  # 1,5 × 1,5
    assert metricas["swolf"] == pytest.approx(160.0)  # 60 s + 100 braçadas (50 ciclos × 2)
    assert metricas["swolf_25"] == pytest.approx(40.0)  # 160 × 25 ÷ 100


@pytest.mark.parametrize(
    "dados",
    [
        {"distance_m": 110},  # não é múltipla da piscina de 25 m
        {"total_time_s": 20.0},  # 5 m/s: rápido demais
        {"swim_distance_m": 120.0},  # trecho maior que a prova
        {"total_cycle_count": 30},  # menos ciclos na prova que no trecho
        {"pool_length_m": 30},  # piscina inválida
    ],
)
def test_treino_invalido_e_recusado_e_nada_e_gravado(api, client, dados):
    headers = api.coach()
    atleta = api.athlete(headers)
    assert api.session(headers, atleta["id"], **dados).status_code == 422
    assert client.get(f"/athletes/{atleta['id']}/sessions", headers=headers).json() == []


def test_atleta_inativo_nao_recebe_treino_mas_continua_no_historico(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    assert api.session(headers, atleta["id"]).status_code == 201
    response = client.patch(f"/athletes/{atleta['id']}", json={"active": False}, headers=headers)
    assert response.status_code == 200

    assert api.session(headers, atleta["id"], days_ago=2).status_code == 409
    assert len(client.get(f"/athletes/{atleta['id']}/sessions", headers=headers).json()) == 1
    inativos = client.get("/athletes", params={"active": False}, headers=headers).json()
    assert [a["id"] for a in inativos] == [atleta["id"]]


def test_edicao_recalcula_as_metricas_e_exclusao_remove(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    criado = api.session(headers, atleta["id"]).json()
    url = f"/athletes/{atleta['id']}/sessions/{criado['id']}"

    corpo = {k: criado[k] for k in (
        "session_date", "session_type", "stroke", "pool_length_m", "distance_m",
        "stroke_count", "total_cycle_count", "swim_distance_m", "notes",
    )}
    corpo.update(total_time_s=50.0, swim_time_s=30.0)
    response = client.put(url, json=corpo, headers=headers)
    assert response.status_code == 200
    assert response.json()["metrics"]["vn"] == pytest.approx(2.0)  # 60 ÷ 30

    assert client.delete(url, headers=headers).status_code == 204
    assert client.get(url, headers=headers).status_code == 404


def test_lista_geral_de_treinos_com_paginacao(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    for dias in range(1, 13):
        assert api.session(headers, atleta["id"], days_ago=dias).status_code == 201
    pagina = client.get("/sessions", params={"limit": 10, "offset": 10}, headers=headers).json()
    assert pagina["total"] == 12
    assert len(pagina["items"]) == 2  # a segunda página tem os 2 restantes
    assert pagina["items"][0]["athlete_name"] == "Atleta Teste"