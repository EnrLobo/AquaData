from app.services.performance import MIN_TREND_POINTS, linear_trend, summarize, summarize_metric


def test_metrica_que_melhora_subindo():
    s = summarize_metric([1.20, 1.30, 1.25, 1.40], "up")
    assert s.count == 4
    assert s.first == 1.20
    assert s.last == 1.40
    assert s.best == 1.40
    assert s.mean == 1.29
    assert s.change == 0.20
    assert s.change_pct == 16.7
    assert s.improved is True


def test_reta_calculada_a_mao():
    # x = 0, 1, 2, 3; y = 1,20 1,30 1,25 1,40
    # média x = 1,5; média y = 1,2875; Sxx = 5; Sxy = 0,275 → b = 0,055; a = 1,205
    t = linear_trend([(0, 1.20), (1, 1.30), (2, 1.25), (3, 1.40)])
    assert t.slope == 0.055
    assert t.start == 1.21  # 1,205 arredondado
    assert t.end == 1.37  # 1,205 + 3 × 0,055 = 1,370
    assert t.first_index == 0
    assert t.last_index == 3
    # resíduos: −0,005; 0,040; −0,065; 0,030 → SQres = 0,00675; SQtot = 0,021875
    assert t.r2 == 0.69  # 1 − 0,00675 / 0,021875


def test_reta_perfeita_tem_r2_igual_a_1():
    t = linear_trend([(0, 40.0), (1, 39.0), (2, 38.0)], digits=1)
    assert t.slope == -1.0
    assert t.r2 == 1.0


def test_valores_constantes_nao_tem_r2():
    t = linear_trend([(0, 1.5), (1, 1.5), (2, 1.5)])
    assert t.slope == 0
    assert t.r2 is None


def test_swolf_melhora_descendo():
    s = summarize_metric([40.0, 38.5, 37.0], "down", digits=1)
    assert s.best == 37.0
    assert s.change == -3.0
    assert s.change_pct == -7.5
    assert s.trend.slope == -1.5
    assert s.improved is True


def test_tendencia_de_piora():
    assert summarize_metric([1.40, 1.35, 1.30], "up").improved is False
    assert summarize_metric([37.0, 38.0, 39.0], "down", digits=1).improved is False


def test_melhora_decidida_pela_tendencia_e_nao_pelos_extremos():
    # último maior que o primeiro, mas a reta desce: a tendência é de queda
    s = summarize_metric([1.50, 1.30, 1.25, 1.20, 1.51], "up")
    assert s.change > 0
    assert s.trend.slope < 0
    assert s.improved is False


def test_poucos_treinos_nao_tem_tendencia():
    s = summarize_metric([1.4, 1.5], "up")
    assert MIN_TREND_POINTS == 3
    assert s.trend is None
    assert s.improved is None


def test_cadencia_sem_sentido_de_melhora():
    s = summarize_metric([50.0, 55.0, 60.0], None, digits=1)
    assert s.best is None
    assert s.trend.slope == 5.0
    assert s.improved is None


def test_ignora_nulos_mas_mantem_a_posicao_no_eixo():
    s = summarize_metric([None, 1.0, None, 1.2, 1.4], "up")
    assert s.count == 3
    assert s.trend.first_index == 1
    assert s.trend.last_index == 4


def test_serie_vazia():
    assert summarize_metric([], "up") is None
    assert summarize_metric([None, None], "up") is None


def test_primeiro_valor_zero_nao_quebra_percentual():
    s = summarize_metric([0.0, 10.0], None, digits=1)
    assert s.change == 10.0
    assert s.change_pct is None


def test_summarize_cobre_as_sete_metricas():
    series = [
        {"vm": 1.5, "vn": 1.4, "cb": 1.6, "cn": 52.0, "swim_index": 2.24, "swolf": 160.0, "swolf_25": 40.0},
        {"vm": 1.6, "vn": 1.5, "cb": 1.7, "cn": 53.0, "swim_index": 2.55, "swolf": 156.0, "swolf_25": 39.0},
        {"vm": 1.6, "vn": 1.6, "cb": 1.7, "cn": 54.0, "swim_index": 2.72, "swolf": 152.0, "swolf_25": 38.0},
    ]
    result = summarize(series)
    assert set(result) == {"vm", "vn", "cb", "cn", "swim_index", "swolf", "swolf_25"}
    assert result["swolf"].improved is True
    assert result["swolf_25"].improved is True
    assert result["cn"].improved is None
    assert summarize([]) == {key: None for key in result}