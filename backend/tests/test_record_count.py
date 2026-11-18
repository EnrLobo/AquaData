"""Estudo do número de registros e das regras do selo (AQ-29).

Verifica as contas usadas pelas regras (erro padrão da inclinação, teste t e
R²) e o comportamento esperado com mais ou menos registros. As séries usam
semente fixa; as margens deixam folga para a variação aleatória.
"""

import numpy as np
import pytest

from app.services.prediction import Record, TrendStatus
from app.services.simulation import (
    R2_MIN,
    SCENARIOS_BY_KEY,
    TrendRule,
    apply_rule,
    run_record_count_study,
    slope_is_significant,
    slope_standard_error,
    with_record_count,
)

N_SERIES = 200  # séries por combinação nos testes (o estudo completo usa 1000)
SEED = 2026


@pytest.fixture(scope="module")
def estudo():
    """Roda as combinações usadas nos testes uma vez só."""
    combinacoes = [
        ("melhora", 6),
        ("melhora", 10),
        ("melhora", 12),
        ("melhora", 20),
        ("estavel", 6),
        ("estavel", 20),
        ("piora", 6),
        ("piora", 20),
    ]
    return {
        (chave, n): run_record_count_study(SCENARIOS_BY_KEY[chave], n, N_SERIES, SEED)
        for chave, n in combinacoes
    }


def _treinos(valores):
    return [Record(value=v, is_competition=False) for v in valores]


def test_muda_so_o_numero_de_registros():
    melhora = SCENARIOS_BY_KEY["melhora"]
    com_20 = with_record_count(melhora, 20)
    assert com_20.n_records == 20
    assert com_20.trend_pct == melhora.trend_pct
    assert com_20.noise_cv_pct == melhora.noise_cv_pct
    assert melhora.n_records == 12  # o cenário original não muda


def test_erro_padrao_da_inclinacao_calculado_a_mao():
    # x = 1..4, y = 60, 59, 59, 57 → b1 = −0,9; resíduos −0,1; −0,2; 0,7; −0,4
    # soma dos quadrados = 0,70; s² = 0,70 ÷ 2 = 0,35; Sxx = 5 → EP = √(0,35 ÷ 5) ≈ 0,2646
    ep = slope_standard_error(_treinos([60, 59, 59, 57]))
    assert ep == pytest.approx(0.2646, abs=1e-4)


def test_erro_padrao_com_reta_exata_e_sem_graus_de_liberdade():
    assert slope_standard_error(_treinos([60, 59, 58, 57])) == pytest.approx(0.0, abs=1e-9)
    assert slope_standard_error(_treinos([60, 59])) is None  # 2 registros, 2 coeficientes


def test_erro_padrao_considera_a_variavel_competicao():
    registros = [
        Record(value=60.0, is_competition=False),
        Record(value=58.6, is_competition=True),
        Record(value=59.6, is_competition=False),
        Record(value=59.3, is_competition=False),
        Record(value=57.9, is_competition=True),
        Record(value=58.9, is_competition=False),
    ]
    # confere com a conta direta: s² = soma dos resíduos² ÷ (6 − 3); EP = √(s² · [(XᵀX)⁻¹] da ordem)
    x = np.column_stack(
        [np.ones(6), np.arange(1, 7), [1.0 if r.is_competition else 0.0 for r in registros]]
    )
    y = np.array([r.value for r in registros])
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    residuos = y - x @ coef
    esperado = np.sqrt(residuos @ residuos / 3 * np.linalg.inv(x.T @ x)[1, 1])
    assert slope_standard_error(registros) == pytest.approx(float(esperado))


def test_teste_da_inclinacao():
    # t = 0,9 ÷ 0,2646 ≈ 3,40; t crítico (95%, 2 graus de liberdade) ≈ 4,30 → não significativa
    assert not slope_is_significant(-0.9, 0.2646, 2)
    # com 10 graus de liberdade, t crítico ≈ 2,23 → significativa
    assert slope_is_significant(-0.9, 0.2646, 10)
    assert slope_is_significant(-0.5, 0.0, 4)  # reta exata com inclinação
    assert not slope_is_significant(0.0, 0.0, 4)
    assert not slope_is_significant(-0.9, None, 2)


def test_regras_so_trocam_mudanca_por_estavel():
    melhorando, estavel = TrendStatus.IMPROVING, TrendStatus.STABLE
    assert apply_rule(TrendRule.SLOPE, melhorando, 0.05, False) is melhorando
    assert apply_rule(TrendRule.SLOPE_R2, melhorando, R2_MIN, False) is melhorando
    assert apply_rule(TrendRule.SLOPE_R2, melhorando, R2_MIN - 0.01, True) is estavel
    assert apply_rule(TrendRule.SLOPE_R2, melhorando, None, True) is estavel
    assert apply_rule(TrendRule.SLOPE_TEST, TrendStatus.ATTENTION, 0.9, True) is TrendStatus.ATTENTION
    assert apply_rule(TrendRule.SLOPE_TEST, melhorando, 0.9, False) is estavel
    for regra in TrendRule:  # nenhuma regra transforma "Estável" em mudança
        assert apply_rule(regra, estavel, 0.99, True) is estavel


def test_mais_registros_deixam_a_reta_mais_estavel(estudo):
    dp = {n: estudo[("melhora", n)].slope_sd_s for n in (6, 10, 12, 20)}
    assert dp[6] > dp[10] > dp[12] > dp[20]
    assert dp[6] > 2 * dp[12]  # como no estudo do AQ-21
    assert dp[20] < 0.05


def test_mais_registros_dao_mais_acertos_na_regra_atual(estudo):
    acerto = {n: estudo[("melhora", n)].rule_accuracy(TrendRule.SLOPE) for n in (6, 10, 12, 20)}
    assert acerto[6] < acerto[10] < acerto[20]
    assert acerto[6] < 0.75
    assert 0.65 <= acerto[10] <= 0.85
    assert acerto[20] >= 0.9


def test_com_6_registros_o_atleta_estavel_e_mal_classificado(estudo):
    assert estudo[("estavel", 6)].rule_accuracy(TrendRule.SLOPE) < 0.6
    assert estudo[("estavel", 20)].rule_accuracy(TrendRule.SLOPE) >= 0.95


def test_r2_e_teste_trocam_mudancas_reais_por_estavel(estudo):
    """As regras 2 e 3 acertam mais o estável e menos a melhora (são mais cautelosas)."""
    estavel_6 = estudo[("estavel", 6)]
    assert estavel_6.rule_accuracy(TrendRule.SLOPE_R2) > estavel_6.rule_accuracy(TrendRule.SLOPE)
    assert estavel_6.rule_accuracy(TrendRule.SLOPE_TEST) > estavel_6.rule_accuracy(TrendRule.SLOPE)
    melhora_10 = estudo[("melhora", 10)]
    assert melhora_10.rule_accuracy(TrendRule.SLOPE_R2) < melhora_10.rule_accuracy(TrendRule.SLOPE)
    assert melhora_10.rule_accuracy(TrendRule.SLOPE_TEST) < melhora_10.rule_accuracy(TrendRule.SLOPE)


def test_com_20_registros_as_regras_quase_coincidem(estudo):
    for chave in ("melhora", "estavel", "piora"):
        resultado = estudo[(chave, 20)]
        acertos = [resultado.rule_accuracy(regra) for regra in TrendRule]
        assert max(acertos) - min(acertos) <= 0.05


def test_erro_grave_some_com_mais_registros(estudo):
    for chave in ("melhora", "piora"):
        assert estudo[(chave, 6)].rule_serious_error(TrendRule.SLOPE) <= 0.12
        assert estudo[(chave, 20)].rule_serious_error(TrendRule.SLOPE) <= 0.01
    assert estudo[("melhora", 10)].rule_serious_error(TrendRule.SLOPE) <= 0.02
    assert estudo[("estavel", 6)].rule_serious_error(TrendRule.SLOPE) is None