"""Comportamento do modelo de predição com dados simulados (AQ-21).

As séries são geradas com semente fixa, então os resultados são sempre os
mesmos. As margens dos testes deixam folga para a variação aleatória: o
objetivo é verificar o comportamento esperado, não um número exato.
"""

import numpy as np
import pytest

from app.services.prediction import TrendStatus
from app.services.simulation import (
    BASE_TIME_S,
    NOISE_CV_ELITE,
    NOISE_CV_NATIONAL,
    SCENARIOS,
    SCENARIOS_BY_KEY,
    run_study,
    simulate_series,
    true_slope_s,
    true_time,
)

N_SERIES = 200  # séries por cenário nos testes (o estudo completo usa mais)
SEED = 2026


@pytest.fixture(scope="module")
def estudo():
    """Roda cada cenário uma vez e reaproveita o resultado nos testes."""
    return {s.key: run_study(s, N_SERIES, SEED) for s in SCENARIOS}


def test_ruido_vem_das_fontes():
    assert NOISE_CV_NATIONAL == 1.4  # Stewart e Hopkins (2000)
    assert NOISE_CV_ELITE == 0.8  # Trewin, Hopkins e Pyne (2004)


def test_tempo_verdadeiro_dos_cenarios():
    melhora = SCENARIOS_BY_KEY["melhora"]
    assert true_time(melhora, 1) == pytest.approx(60.0)
    assert true_time(melhora, 11) == pytest.approx(60 * (1 - 0.003 * 10))  # 58,2 s
    assert true_slope_s(melhora) == pytest.approx(-0.18)
    competicao = SCENARIOS_BY_KEY["competicao"]
    assert true_time(competicao, 4) == pytest.approx(60 * (1 - 0.009) * 0.985)  # 4º é competição
    plato = SCENARIOS_BY_KEY["plato"]
    assert true_time(plato, 1) == pytest.approx(60.0)
    assert true_time(plato, 100) == pytest.approx(60 * 0.96, abs=1e-6)  # chega ao platô (−4%)
    assert true_slope_s(plato) is None


def test_mesma_semente_gera_a_mesma_serie():
    cenario = SCENARIOS_BY_KEY["melhora"]
    a = simulate_series(cenario, np.random.default_rng(7))
    b = simulate_series(cenario, np.random.default_rng(7))
    assert [r.value for r in a.records] == [r.value for r in b.records]


@pytest.mark.parametrize("chave", ["melhora", "estavel", "piora"])
def test_sem_ruido_o_modelo_recupera_a_reta_e_o_selo(chave):
    cenario = SCENARIOS_BY_KEY[chave]
    resultado = run_study(cenario, n_series=1, seed=SEED, noise=False)
    assert resultado.mean_slope_s == pytest.approx(true_slope_s(cenario), abs=0.01)
    assert resultado.status_accuracy == 1.0


@pytest.mark.parametrize("chave", ["melhora", "estavel", "piora", "competicao"])
def test_inclinacao_media_proxima_da_verdadeira(estudo, chave):
    resultado = estudo[chave]
    assert resultado.mean_slope_s == pytest.approx(true_slope_s(resultado.scenario), abs=0.02)


def test_selo_acerta_na_maior_parte_das_series(estudo):
    assert estudo["melhora"].status_accuracy >= 0.75
    assert estudo["estavel"].status_accuracy >= 0.85
    assert estudo["piora"].status_accuracy >= 0.70
    # erro grosseiro (melhora vista como piora, e vice-versa) quase não acontece
    assert estudo["melhora"].status_share(TrendStatus.ATTENTION) <= 0.02
    assert estudo["piora"].status_share(TrendStatus.IMPROVING) <= 0.02


def test_erro_no_teste_acompanha_o_ruido(estudo):
    # com ruído de 1,4% em 60 s (desvio de 0,84 s), o MAE fica na mesma ordem
    desvio = BASE_TIME_S * NOISE_CV_NATIONAL / 100
    assert 0.6 * desvio < estudo["melhora"].mean_mae_s < 1.4 * desvio


def test_menos_ruido_da_previsoes_melhores(estudo):
    elite, nacional = estudo["melhora_elite"], estudo["melhora"]
    assert elite.mean_mae_s < nacional.mean_mae_s
    assert elite.slope_sd_s < nacional.slope_sd_s
    assert elite.status_accuracy > nacional.status_accuracy


def test_efeito_competicao_e_estimado(estudo):
    # competição 1,5% mais rápida: no 4º registro (≈ 59,5 s) isso dá ≈ −0,89 s
    assert estudo["competicao"].mean_competition_s == pytest.approx(-0.89, abs=0.15)
    assert len(estudo["competicao"].competition_s) == N_SERIES


def test_registro_atipico_aumenta_o_erro(estudo):
    assert estudo["atipico"].mean_mae_s > estudo["melhora"].mean_mae_s
    # o registro atípico (mais lento) puxa a previsão do próximo treino para cima
    assert estudo["atipico"].next_bias_s > estudo["melhora"].next_bias_s + 0.05


def test_poucos_registros_deixam_a_reta_instavel(estudo):
    poucos, normal = estudo["poucos"], estudo["melhora"]
    assert poucos.slope_sd_s > 2 * normal.slope_sd_s
    assert poucos.status_accuracy < normal.status_accuracy
    assert poucos.next_mae_s > normal.next_mae_s


def test_plato_mostra_o_limite_da_reta(estudo):
    plato = estudo["plato"]
    # a reta ignora a desaceleração: a previsão do próximo treino sai otimista (tempo menor)
    assert plato.next_bias_s < -0.3
    # e o selo continua "Melhorando" na maioria das séries, embora o atleta já esteja estagnado
    assert plato.status_share(TrendStatus.IMPROVING) > 0.7


def test_previsao_sem_vies_nos_cenarios_lineares(estudo):
    for chave in ["melhora", "estavel", "piora", "competicao"]:
        assert estudo[chave].next_bias_s == pytest.approx(0, abs=0.15)