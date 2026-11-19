"""Funções de apoio do relatório por atleta (AQ-22)."""

from datetime import date

import pytest

from app.services.prediction import PathPoint, Record, predict_next
from app.services.report import (
    ReportRecord,
    chart_points,
    event_sort_key,
    event_times,
    filter_period,
    in_period,
)


def registros(tempos, competicoes=(), inicio=date(2026, 3, 1)):
    """Um registro por dia a partir de `inicio`; `competicoes` lista as ordens (a partir de 1)."""
    return [
        ReportRecord(
            order=i + 1,
            session_id=100 + i,
            session_date=date(inicio.year, inicio.month, inicio.day + i),
            is_competition=(i + 1) in competicoes,
            time_s=t,
        )
        for i, t in enumerate(tempos)
    ]


def test_periodo_com_limites_abertos_e_fechados():
    dia = date(2026, 3, 10)
    assert in_period(dia, None, None)
    assert in_period(dia, date(2026, 3, 10), date(2026, 3, 10))  # limites inclusivos
    assert not in_period(dia, date(2026, 3, 11), None)
    assert not in_period(dia, None, date(2026, 3, 9))


def test_filtra_os_registros_do_periodo_mantendo_a_ordem_do_historico():
    todos = registros([60, 59.5, 59, 58.5, 58])  # 1 a 5 de março
    periodo = filter_period(todos, date(2026, 3, 3), None)
    assert [r.order for r in periodo] == [3, 4, 5]  # a ordem continua a do histórico


def test_tempos_da_prova_no_periodo():
    t = event_times(registros([60.0, 58.5, 59.0, 58.5, 59.2], competicoes=(2,)))
    assert t.n_records == 5
    assert t.n_competitions == 1
    assert t.n_trainings == 4
    assert t.best.time_s == 58.5 and t.best.order == 2  # empate: o mais antigo
    assert t.last.order == 5
    assert t.summary.first == 60.0
    assert t.summary.best == 58.5  # menor tempo = melhor
    assert t.summary.change == pytest.approx(-0.8)
    assert t.summary.improved is True  # reta descendo
    assert t.summary.conclusive is False  # menos de 10 registros


def test_periodo_vazio_nao_tem_resumo():
    assert event_times([]) is None


def test_grafico_usa_a_reta_do_historico_e_projeta_os_proximos():
    # tempo = 61 − 0,5·ordem (sem ruído): reta exata, previsão do 7º = 57,5 s
    todos = registros([60.5, 60.0, 59.5, 59.0, 58.5, 58.0])
    resultado = predict_next([Record(value=r.time_s, is_competition=False) for r in todos])
    periodo = todos[3:]  # só os 3 últimos no período
    pontos = chart_points(periodo, resultado.path, n_history=len(todos))
    assert [p.order for p in pontos] == [4, 5, 6, 7, 8, 9]  # 3 do período + 3 futuros
    assert pontos[0].time_s == 59.0
    assert pontos[0].model_training_s == pytest.approx(59.0)  # reta na ordem 4
    assert pontos[3].time_s is None and pontos[3].session_date is None  # futuro sem data
    assert pontos[3].model_training_s == pytest.approx(57.5)
    assert all(p.model_competition_s is None for p in pontos)  # só treinos


def test_grafico_sem_previsao_mostra_so_os_registros():
    periodo = registros([40.0, 39.8, 39.7])
    pontos = chart_points(periodo, path=[], n_history=3)
    assert [p.time_s for p in pontos] == [40.0, 39.8, 39.7]
    assert all(p.model_training_s is None for p in pontos)


def test_grafico_ignora_reta_fora_do_periodo():
    path = [PathPoint(order=o, training_s=60.0 - o, competition_s=None) for o in range(1, 6)]
    periodo = [ReportRecord(3, 1, date(2026, 3, 3), False, 57.0)]
    pontos = chart_points(periodo, path, n_history=3)
    assert [p.order for p in pontos] == [3, 4, 5]  # ordens 1 e 2 (fora do período) não entram
    assert pontos[0].model_training_s == 57.0


def test_ordem_das_provas_no_relatorio():
    provas = {
        "50 livre": (8, date(2026, 3, 1)),
        "100 livre": (12, date(2026, 2, 1)),
        "50 peito": (8, date(2026, 3, 5)),
    }
    ordem = sorted(provas, key=lambda k: event_sort_key(*provas[k]))
    assert ordem == ["100 livre", "50 peito", "50 livre"]  # mais registros; empate: mais recente