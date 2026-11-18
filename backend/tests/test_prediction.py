from datetime import date

import pytest

from app.services.prediction import (
    FUTURE_STEPS,
    MIN_RECORDS,
    MIN_TREND_RECORDS,
    STABLE_BAND_PCT,
    InsufficientDataError,
    Record,
    TrendStatus,
    classify_trend,
    evaluate,
    fit,
    pick_main_event,
    predict_next,
    project_series,
    split_sizes,
    trend_status,
)


def serie(tempos, competicoes=()):
    """Monta registros; `competicoes` lista as posições (a partir de 1) que são competição."""
    return [Record(value=t, is_competition=(i + 1) in competicoes) for i, t in enumerate(tempos)]


def test_divisao_temporal_ultimos_20_por_cento():
    assert split_sizes(6) == (4, 2)  # 20% de 6 = 1,2 → mínimo de 2 no teste
    assert split_sizes(10) == (8, 2)
    assert split_sizes(11) == (8, 3)  # 20% de 11 = 2,2 → arredonda para cima
    assert split_sizes(20) == (16, 4)


def test_historico_curto_nao_tem_predicao():
    assert MIN_RECORDS == 6
    with pytest.raises(InsufficientDataError):
        split_sizes(5)
    with pytest.raises(InsufficientDataError):
        predict_next(serie([60, 59, 58, 57, 56]))


def test_recupera_coeficientes_de_uma_serie_exata():
    # tempo = 62 − 0,5 · ordem − 2 · competição (sem ruído)
    competicoes = (3, 6)
    tempos = [62 - 0.5 * o - (2 if o in competicoes else 0) for o in range(1, 9)]
    _, modelo = fit(serie(tempos, competicoes))
    assert modelo.intercept == pytest.approx(62)
    assert modelo.coef_order == pytest.approx(-0.5)
    assert modelo.coef_competition == pytest.approx(-2)
    assert modelo.r2 == pytest.approx(1)
    assert modelo.n == 8


def test_serie_exata_tem_erro_zero_e_preve_o_proximo():
    competicoes = (2, 5)
    tempos = [62 - 0.5 * o - (2 if o in competicoes else 0) for o in range(1, 9)]
    p = predict_next(serie(tempos, competicoes))
    assert p.next_order == 9
    assert p.training_s == pytest.approx(62 - 0.5 * 9)  # 57,5
    assert p.competition_s == pytest.approx(62 - 0.5 * 9 - 2)  # 55,5
    assert p.evaluation.mae_s == pytest.approx(0, abs=1e-9)
    assert p.evaluation.mape_pct == pytest.approx(0, abs=1e-9)


def test_so_treinos_nao_estima_competicao():
    p = predict_next(serie([60, 59.5, 59, 58.5, 58, 57.5]))
    assert p.model.coef_competition is None
    assert p.competition_s is None
    assert p.training_s == pytest.approx(57)
    assert p.model.coef_order == pytest.approx(-0.5)


def test_competicao_so_no_teste_e_ignorada_no_ajuste():
    # o conjunto de treino (4 primeiros) só tem treinos: a avaliação ajusta sem a variável
    registros = serie([60, 59, 58, 57, 54, 53], competicoes=(5,))
    avaliacao = evaluate(registros)
    assert avaliacao.n_train == 4
    assert [p.order for p in avaliacao.points] == [5, 6]
    assert avaliacao.points[0].predicted_s == pytest.approx(56)  # reta 61 − 1 · ordem
    # no histórico completo há os dois tipos: a previsão final estima a competição
    assert predict_next(registros).competition_s is not None


def test_erros_calculados_a_mao():
    # treino (4 registros): 60, 59, 58, 57 → reta 61 − ordem; prevê 56 e 55
    # teste real: 57 e 54 → erros 1 e −1
    avaliacao = evaluate(serie([60, 59, 58, 57, 57, 54]))
    assert [p.predicted_s for p in avaliacao.points] == pytest.approx([56, 55])
    assert avaliacao.mae_s == pytest.approx(1.0)  # (|57−56| + |54−55|) ÷ 2
    assert avaliacao.rmse_s == pytest.approx(1.0)  # √((1² + 1²) ÷ 2)
    assert avaliacao.mape_pct == pytest.approx((1 / 57 + 1 / 54) / 2 * 100)  # ≈ 1,80%


def test_tempo_constante_nao_tem_r2():
    _, modelo = fit(serie([60] * 6))
    assert modelo.coef_order == pytest.approx(0)
    assert modelo.r2 is None


def test_previsao_nao_positiva_e_descartada():
    # queda forte e artificial: a reta cruza o zero no próximo registro
    p = predict_next(serie([50, 40, 30, 20, 10, 0.5]))
    assert p.training_s is None


def test_reta_no_historico_e_projecao_futura():
    competicoes = (2, 5)
    tempos = [62 - 0.5 * o - (2 if o in competicoes else 0) for o in range(1, 9)]
    p = predict_next(serie(tempos, competicoes))
    assert FUTURE_STEPS == 3
    assert [ponto.order for ponto in p.path] == list(range(1, 12))  # 8 do histórico + 3 futuros
    assert p.path[0].training_s == pytest.approx(61.5)  # 62 − 0,5 · 1
    assert p.path[0].competition_s == pytest.approx(59.5)
    assert p.path[-1].training_s == pytest.approx(56.5)  # 62 − 0,5 · 11
    # o próximo registro da previsão é o primeiro ponto futuro da reta
    assert p.path[8].training_s == p.training_s


def test_projecao_so_com_treinos_nao_tem_linha_de_competicao():
    p = predict_next(serie([60, 59.5, 59, 58.5, 58, 57.5]), steps=2)
    assert len(p.path) == 8
    assert all(ponto.competition_s is None for ponto in p.path)


def test_projecao_de_metrica_com_lacunas_usa_a_ordem_real():
    # métrica = 1,50 + 0,02 · ordem (sem ruído); o 3º e o 6º registro não têm valor
    ordens = [1, 2, 4, 5, 7, 8]
    registros = [Record(value=1.5 + 0.02 * o, is_competition=False) for o in ordens]
    proj = project_series(registros, ordens, last_order=8)
    assert proj.model.coef_order == pytest.approx(0.02)
    assert [p.order for p in proj.path] == list(range(1, 12))  # 8 da prova + 3 futuros
    assert proj.path[2].training_s == pytest.approx(1.56)  # ordem 3, sem valor real
    assert proj.path[-1].training_s == pytest.approx(1.72)  # ordem 11
    assert all(p.competition_s is None for p in proj.path)


def test_projecao_de_metrica_exige_o_minimo_de_registros():
    registros = [Record(value=1.5, is_competition=False) for _ in range(5)]
    with pytest.raises(InsufficientDataError):
        project_series(registros, [1, 2, 3, 4, 5], last_order=7)


def test_selo_pela_variacao_percentual_por_registro():
    assert STABLE_BAND_PCT == 0.2
    # último tempo de 30 s: a faixa de estável vai de −0,06 s a +0,06 s por registro
    pct, selo = classify_trend(-0.3, 30)
    assert pct == pytest.approx(-1.0)
    assert selo is TrendStatus.IMPROVING
    assert classify_trend(0.3, 30)[1] is TrendStatus.ATTENTION
    assert classify_trend(0.03, 30)[1] is TrendStatus.STABLE
    assert classify_trend(-0.07, 30)[1] is TrendStatus.IMPROVING  # logo fora da faixa
    assert classify_trend(0.05, 30)[1] is TrendStatus.STABLE  # logo dentro da faixa


def test_selo_usa_a_mesma_faixa_em_provas_longas():
    # −0,5 s por registro: melhora em 30 s (−1,67%), estável em 300 s (−0,17%)
    assert classify_trend(-0.5, 30)[1] is TrendStatus.IMPROVING
    assert classify_trend(-0.5, 300)[1] is TrendStatus.STABLE


def test_selo_so_a_partir_do_minimo_de_registros():
    assert MIN_TREND_RECORDS == 10  # decisão da equipe, com base no estudo de simulação (AQ-29)
    # mesma inclinação clara (−1,0% por registro): sem selo com 9 registros, Melhorando com 10
    pct, selo = trend_status(-0.3, 30, 9)
    assert pct == pytest.approx(-1.0)  # a variação continua calculada
    assert selo is None
    assert trend_status(-0.3, 30, 10)[1] is TrendStatus.IMPROVING
    assert trend_status(0.3, 30, 10)[1] is TrendStatus.ATTENTION
    assert trend_status(0.03, 30, 12)[1] is TrendStatus.STABLE
    assert trend_status(0.3, 30, MIN_RECORDS)[1] is None  # tem previsão, mas não tem selo


def test_prova_principal_e_a_mais_registrada_com_previsao():
    provas = {
        ("freestyle", 50, 25): (8, date(2026, 11, 1)),
        ("freestyle", 100, 25): (10, date(2026, 10, 1)),
        ("breaststroke", 50, 25): (5, date(2026, 11, 10)),  # abaixo do mínimo
    }
    assert pick_main_event(provas) == ("freestyle", 100, 25)


def test_prova_principal_desempata_pelo_registro_mais_recente():
    provas = {
        ("freestyle", 50, 25): (6, date(2026, 11, 1)),
        ("backstroke", 50, 25): (6, date(2026, 11, 12)),
    }
    assert pick_main_event(provas) == ("backstroke", 50, 25)


def test_sem_prova_com_minimo_nao_ha_prova_principal():
    assert pick_main_event({("freestyle", 50, 25): (5, date(2026, 11, 1))}) is None
    assert pick_main_event({}) is None