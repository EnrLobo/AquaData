"""Funções de apoio do relatório por atleta (AQ-22) e da exportação em planilha (AQ-23)."""

from datetime import date

import pytest

from app.services.prediction import PathPoint, Record, predict_next
from app.services.report import (
    CSV_COLUMNS,
    ReportRecord,
    chart_points,
    csv_filename,
    event_sort_key,
    event_times,
    filter_period,
    format_decimal,
    format_time,
    in_period,
    report_csv,
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


# --- Exportação em planilha (AQ-23) ---


def linha(**extra):
    """Registro de 100 m livre em 64,62 s, com métricas (valores de exemplo)."""
    base = {
        "session_date": date(2026, 11, 3),
        "session_type": "training",
        "stroke": "freestyle",
        "distance_m": 100,
        "pool_length_m": 25,
        "total_time_s": 64.62,
        "swim_distance_m": 60.0,
        "swim_time_s": 40.0,
        "stroke_count": 40,
        "total_cycle_count": 50,
        "vm": 1.5475,
        "vn": 1.5,
        "cb": 1.5,
        "cn": 60.0,
        "swim_index": 2.25,
        "swolf": 164.62,
        "swolf_25": 41.155,
        "notes": None,
    }
    return {**base, **extra}


def test_numeros_e_tempo_no_padrao_brasileiro():
    assert format_decimal(1.5475, 2) == "1,55"
    assert format_decimal(60.0, 1) == "60,0"
    assert format_time(64.62) == "1:04,62"
    assert format_time(29.38) == "0:29,38"
    assert format_time(59.999) == "1:00,00"  # arredonda para o centésimo


def test_planilha_com_cabecalho_bom_e_separador_ponto_e_virgula():
    texto = report_csv([linha()])
    assert texto.startswith("\ufeff")  # BOM: o Excel reconhece os acentos
    linhas = texto.lstrip("\ufeff").split("\r\n")
    assert linhas[0].split(";") == [titulo for _, titulo, _ in CSV_COLUMNS]
    celulas = linhas[1].split(";")
    valores = dict(zip([chave for chave, _, _ in CSV_COLUMNS], celulas, strict=True))
    assert valores["session_date"] == "03/11/2026"
    assert valores["session_type"] == "Treino"
    assert valores["stroke"] == "Livre"
    assert valores["total_time_s"] == "64,62"
    assert valores["total_time"] == "1:04,62"
    assert valores["vm"] == "1,55"
    assert valores["cn"] == "60,0"
    assert valores["swolf_25"] == "41,2"
    assert valores["notes"] == ""  # sem observação


def test_planilha_deixa_metrica_ausente_vazia_e_protege_observacao():
    texto = report_csv(
        [linha(stroke="medley", swolf=None, swolf_25=None, notes="cansado; dormiu mal")]
    )
    dados = texto.lstrip("\ufeff").split("\r\n")[1]
    assert ";Medley;" in dados
    assert ';"cansado; dormiu mal"' in dados  # o ";" do texto não quebra a coluna
    assert ";;" in dados  # SWOLF vazio no medley


def test_planilha_sem_registros_tem_so_o_cabecalho():
    linhas = report_csv([]).lstrip("\ufeff").split("\r\n")
    assert linhas[0].startswith("Data;Tipo;Nado")
    assert linhas[1:] == [""]


def test_nome_do_arquivo_sem_acentos_nem_espacos():
    assert csv_filename("João Henrique Souza", date(2026, 11, 18)) == (
        "relatorio-joao-henrique-souza-2026-11-18.csv"
    )
    assert csv_filename("  ", date(2026, 11, 18)) == "relatorio-atleta-2026-11-18.csv"