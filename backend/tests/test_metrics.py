from app.services.metrics import compute_metrics

BASE = dict(
    distance_m=100,
    total_time_s=60,
    pool_length_m=25,
    stroke_count=40,
    swim_distance_m=60,
    swim_time_s=40,
)


def test_metricas_basicas():
    m = compute_metrics(**BASE)
    assert m.vm == 1.67
    assert m.vn == 1.5
    assert m.cb == 1.5
    assert m.cn == 60.0
    assert m.swim_index == 2.25
    assert m.swolf == 33.3


def test_vn_e_produto_de_cb_e_cadencia():
    m = compute_metrics(**BASE)
    assert round(m.cb * m.cn / 60, 2) == m.vn


def test_swolf_escala_com_o_tamanho_da_piscina():
    assert compute_metrics(**{**BASE, "pool_length_m": 50}).swolf == 66.7


def test_sem_ciclos_nao_quebra():
    m = compute_metrics(**{**BASE, "stroke_count": 0})
    assert m.cb is None
    assert m.swim_index is None
    assert m.cn == 0.0