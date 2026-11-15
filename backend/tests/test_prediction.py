import pytest

from app.services.prediction import (
    MIN_RECORDS,
    InsufficientDataError,
    Record,
    evaluate,
    fit,
    predict_next,
    split_sizes,
)


def serie(tempos, competicoes=()):
    """Monta registros; `competicoes` lista as posições (a partir de 1) que são competição."""
    return [Record(time_s=t, is_competition=(i + 1) in competicoes) for i, t in enumerate(tempos)]


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