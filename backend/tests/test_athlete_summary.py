"""Resumo dos cartões da tela "Meus atletas" (AQ-26)."""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.services.athlete_summary import summarize_athlete
from app.services.prediction import TrendStatus

INICIO = date(2026, 3, 1)


def registro(ordem, tempo, distancia=100, nado="freestyle", tipo="training"):
    """Registro como o do banco (100 m livre, piscina de 25 m, valores de referência)."""
    return SimpleNamespace(
        session_date=INICIO + timedelta(days=ordem),
        session_type=tipo,
        stroke=nado,
        distance_m=distancia,
        pool_length_m=25,
        total_time_s=tempo,
        stroke_count=40,
        total_cycle_count=50,
        swim_distance_m=60,
        swim_time_s=40,
    )


def serie(n, distancia=100):
    """Tempo = 61 − 0,5·ordem: −0,5 s por registro (cerca de −0,9% do último tempo)."""
    return [registro(o, 61 - 0.5 * o, distancia) for o in range(1, n + 1)]


def test_atleta_sem_registros():
    resumo = summarize_athlete([])
    assert resumo.sessions_count == 0
    assert resumo.last_session is None and resumo.main_trend is None


def test_metricas_do_registro_mais_recente():
    registros = serie(3)
    registros[-1] = registro(3, 60.0)
    resumo = summarize_athlete(registros)
    ultimo = resumo.last_session
    assert resumo.sessions_count == 3
    assert ultimo.session_date == INICIO + timedelta(days=3)
    # 100 m em 60 s; trecho de 60 m em 40 s com 40 ciclos; 50 ciclos na prova
    assert ultimo.swolf == pytest.approx(160.0)
    assert ultimo.cb == pytest.approx(1.5)
    assert ultimo.vn == pytest.approx(1.5)
    assert resumo.main_trend is None  # 3 registros: sem previsão, sem selo


def test_selo_so_a_partir_de_10_registros_na_prova_principal():
    com_poucos = summarize_athlete(serie(7))
    assert com_poucos.main_trend.n_records == 7
    assert com_poucos.main_trend.min_records == 10
    assert com_poucos.main_trend.status is None  # "Poucos registros (7 de 10)"

    com_selo = summarize_athlete(serie(12))
    assert com_selo.main_trend.status == TrendStatus.IMPROVING


def test_prova_principal_e_a_mais_registrada():
    # 6 registros de 50 m e 8 de 100 m: a principal é a de 100 m
    registros = [registro(o, 30.0 - 0.1 * o, distancia=50) for o in range(1, 7)]
    registros += [registro(10 + o, 61 - 0.5 * o) for o in range(1, 9)]
    registros.sort(key=lambda r: r.session_date)
    resumo = summarize_athlete(registros)
    assert (resumo.main_trend.distance_m, resumo.main_trend.n_records) == (100, 8)


def test_medley_nao_tem_swolf():
    resumo = summarize_athlete([registro(1, 70.0, nado="medley")])
    assert resumo.last_session.swolf is None
    assert resumo.last_session.cb == pytest.approx(1.5)