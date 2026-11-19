"""Previsão, painel e desempenho de ponta a ponta, com séries gravadas no banco (AQ-24)."""

import pytest


def serie_exata(n: int) -> list[float]:
    """Tempo = 61 − 0,5·ordem (sem ruído): 60,5; 60,0; 59,5..."""
    return [61 - 0.5 * ordem for ordem in range(1, n + 1)]


PROVA = {"stroke": "freestyle", "distance_m": 100, "pool_length_m": 25}


def test_previsao_com_historico_suficiente(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    api.series(headers, atleta["id"], serie_exata(12))

    response = client.get(
        f"/athletes/{atleta['id']}/prediction", params=PROVA, headers=headers
    )
    assert response.status_code == 200
    previsao = response.json()
    assert previsao["available"] is True
    assert previsao["n_records"] == 12
    assert previsao["training_s"] == pytest.approx(61 - 0.5 * 13)  # 54,5 s no 13º registro
    assert previsao["model"]["coef_order"] == pytest.approx(-0.5)
    assert previsao["evaluation"]["mae_s"] == pytest.approx(0, abs=0.01)  # reta exata
    assert len(previsao["path"]) == 12 + 3  # histórico + 3 registros futuros


def test_previsao_com_historico_curto_avisa_o_minimo(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    api.series(headers, atleta["id"], serie_exata(5))

    previsao = client.get(
        f"/athletes/{atleta['id']}/prediction", params=PROVA, headers=headers
    ).json()
    assert previsao["available"] is False
    assert previsao["min_records"] == 6
    assert "6" in previsao["message"]


def test_painel_mostra_selo_so_a_partir_de_10_registros(api, client):
    headers = api.coach()
    com_selo = api.athlete(headers, name="Com Selo")
    sem_selo = api.athlete(headers, name="Poucos Registros")
    sem_previsao = api.athlete(headers, name="Sem Previsao")
    api.series(headers, com_selo["id"], serie_exata(12))
    api.series(headers, sem_selo["id"], serie_exata(7))
    api.series(headers, sem_previsao["id"], serie_exata(5))

    painel = client.get("/dashboard", headers=headers).json()
    assert painel["active_athletes"] == 3
    assert painel["sessions_total"] == 12 + 7 + 5
    assert painel["min_trend_records"] == 10
    previsoes = {p["athlete_name"]: p for p in painel["predictions"]}
    assert set(previsoes) == {"Com Selo", "Poucos Registros"}  # 5 registros: sem previsão
    # −0,5 s por registro ÷ último tempo (55 s) = −0,91% → Melhorando
    assert previsoes["Com Selo"]["status"] == "improving"
    assert previsoes["Poucos Registros"]["status"] is None  # 7 de 10: sem selo
    assert painel["predictions"][-1]["athlete_name"] == "Poucos Registros"  # sem selo por último
    assert painel["athletes_without_prediction"] == 1


def test_desempenho_indica_tendencia_conclusiva_com_10_treinos(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    api.series(headers, atleta["id"], serie_exata(12))

    desempenho = client.get(f"/athletes/{atleta['id']}/performance", headers=headers).json()
    assert desempenho["total"] == 12
    assert desempenho["min_conclusive_points"] == 10
    vm = desempenho["summary"]["vm"]
    assert vm["count"] == 12
    assert vm["conclusive"] is True
    assert vm["improved"] is True  # tempo caindo → velocidade média subindo