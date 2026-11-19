"""Relatório e exportação em planilha de ponta a ponta (AQ-24)."""

from datetime import date, timedelta

import pytest


def test_relatorio_consolida_as_provas_do_atleta(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    api.series(headers, atleta["id"], [60.5, 60.0, 59.5, 59.0, 58.5, 58.0], competitions=(6,))
    resposta = api.session(
        headers, atleta["id"], days_ago=20, distance_m=50, total_time_s=35.0,
        swim_distance_m=30.0, swim_time_s=20.0, stroke_count=20, total_cycle_count=25,
    )
    assert resposta.status_code == 201

    relatorio = client.get(f"/athletes/{atleta['id']}/report", headers=headers).json()
    assert relatorio["totals"] == {"records": 7, "trainings": 6, "competitions": 1, "events": 2}
    primeira, segunda = relatorio["events"]
    assert (primeira["distance_m"], primeira["n_records"]) == (100, 6)  # mais registros primeiro
    assert primeira["best"]["time_s"] == 58.0
    assert primeira["best"]["session_type"] == "competition"
    assert primeira["prediction"]["available"] is True
    assert len(primeira["chart"]) == 6 + 3  # registros + 3 futuros
    assert (segunda["distance_m"], segunda["prediction"]["available"]) == (50, False)


def test_periodo_filtra_os_registros_mas_a_previsao_usa_todo_o_historico(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    api.series(headers, atleta["id"], [61 - 0.5 * o for o in range(1, 13)])  # 12 dias seguidos
    url = f"/athletes/{atleta['id']}/report"

    completo = client.get(url, headers=headers).json()
    inicio = (date.today() - timedelta(days=3)).isoformat()  # só os 3 últimos registros
    filtrado = client.get(url, params={"date_from": inicio}, headers=headers).json()

    assert filtrado["totals"]["records"] == 3
    assert filtrado["events"][0]["n_history"] == 12
    previsao_completa = completo["events"][0]["prediction"]["training_s"]
    assert filtrado["events"][0]["prediction"]["training_s"] == pytest.approx(previsao_completa)


def test_periodo_invertido_e_recusado(api, client):
    headers = api.coach()
    atleta = api.athlete(headers)
    params = {"date_from": "2026-02-01", "date_to": "2026-01-01"}
    for sufixo in ("", "/csv"):
        response = client.get(f"/athletes/{atleta['id']}/report{sufixo}", params=params,
                              headers=headers)
        assert response.status_code == 422, sufixo


def test_planilha_traz_os_registros_do_periodo_no_padrao_brasileiro(api, client):
    headers = api.coach()
    atleta = api.athlete(headers, name="João da Silva")
    api.series(headers, atleta["id"], [60.0, 59.5, 59.0])
    assert api.session(headers, atleta["id"], days_ago=40, notes="antigo; fora").status_code == 201

    inicio = (date.today() - timedelta(days=10)).isoformat()
    response = client.get(
        f"/athletes/{atleta['id']}/report/csv", params={"date_from": inicio}, headers=headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "relatorio-joao-da-silva-" in response.headers["content-disposition"]

    texto = response.content.decode("utf-8")
    assert texto.startswith("\ufeff")  # BOM para o Excel
    linhas = texto.lstrip("\ufeff").strip().split("\r\n")
    assert linhas[0].startswith("Data;Tipo;Nado;")
    assert len(linhas) == 1 + 3  # cabeçalho + 3 registros do período (o antigo fica de fora)
    assert ";60,00;1:00,00;" in linhas[1]  # vírgula decimal e tempo m:ss,cc
    assert "antigo" not in texto