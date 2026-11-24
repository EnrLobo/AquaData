"""Resumo dos cartões de "Meus atletas" pela API (AQ-26)."""

import pytest


def test_listagem_sem_resumo_por_padrao(api, client):
    headers = api.coach()
    api.athlete(headers)
    atletas = client.get("/athletes", headers=headers).json()
    assert atletas[0]["summary"] is None  # só a tela "Meus atletas" pede o resumo


def test_resumo_com_ultimo_treino_e_selo(api, client):
    headers = api.coach()
    api.athlete(headers, name="Sem Treino")
    poucos = api.athlete(headers, name="Poucos Registros")
    com_selo = api.athlete(headers, name="Com Selo")
    api.series(headers, poucos["id"], [61 - 0.5 * o for o in range(1, 8)])
    api.series(headers, com_selo["id"], [61 - 0.5 * o for o in range(1, 13)])

    resposta = client.get("/athletes", params={"summary": "true"}, headers=headers)
    assert resposta.status_code == 200
    resumos = {a["name"]: a["summary"] for a in resposta.json()}

    assert resumos["Sem Treino"] == {"sessions_count": 0, "last_session": None, "main_trend": None}

    ultimo = resumos["Com Selo"]["last_session"]
    assert resumos["Com Selo"]["sessions_count"] == 12
    assert ultimo["total_time_s"] == pytest.approx(55.0)  # 12º registro: 61 − 0,5 × 12
    assert ultimo["cb"] == pytest.approx(1.5)
    assert ultimo["vn"] == pytest.approx(1.5)
    assert ultimo["swolf"] == pytest.approx(155.0)  # 55 s + 100 braçadas (50 ciclos × 2)
    assert resumos["Com Selo"]["main_trend"]["status"] == "improving"

    assert resumos["Poucos Registros"]["main_trend"]["n_records"] == 7
    assert resumos["Poucos Registros"]["main_trend"]["status"] is None
    assert resumos["Poucos Registros"]["main_trend"]["min_records"] == 10


def test_resumo_respeita_o_isolamento_entre_treinadores(api, client):
    a = api.coach(email="a@teste.com")
    b = api.coach(email="b@teste.com")
    atleta = api.athlete(a)
    api.series(a, atleta["id"], [60.0, 59.0])
    assert client.get("/athletes", params={"summary": "true"}, headers=b).json() == []