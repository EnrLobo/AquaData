from app.services.metrics import compute_metrics

# 100 m livre em piscina de 25 m, em 60 s.
# Trecho de nado puro: 60 m em 40 s, 40 ciclos.
# Prova completa: 50 ciclos (= 100 braçadas no crawl).
BASE = dict(
    stroke="freestyle",
    distance_m=100,
    total_time_s=60,
    pool_length_m=25,
    stroke_count=40,
    swim_distance_m=60,
    swim_time_s=40,
    total_cycle_count=50,
)


def test_metricas_basicas():
    m = compute_metrics(**BASE)
    assert m.vm == 1.67
    assert m.vn == 1.5
    assert m.cb == 1.5
    assert m.cn == 60.0
    assert m.swim_index == 2.25


def test_vn_e_produto_de_cb_e_cadencia():
    m = compute_metrics(**BASE)
    assert round(m.cb * m.cn / 60, 2) == m.vn


def test_swolf_simples_e_tempo_mais_bracadas():
    # 60 s + 50 ciclos × 2 braçadas = 160
    assert compute_metrics(**BASE).swolf == 160.0


def test_exemplo_de_uma_extensao():
    # 25 m em 30 s com 4 ciclos (8 braçadas): SWOLF 38, e o SWOLF 25 m é igual
    m = compute_metrics(
        **{
            **BASE,
            "distance_m": 25,
            "total_time_s": 30,
            "stroke_count": 3,
            "swim_distance_m": 15,
            "swim_time_s": 18,
            "total_cycle_count": 4,
        }
    )
    assert m.swolf == 38.0
    assert m.swolf_25 == 38.0


def test_swolf_25_e_proporcional_a_distancia():
    # 160 × 25 ÷ 100 = 40
    assert compute_metrics(**BASE).swolf_25 == 40.0


def test_swolf_usa_a_prova_completa_e_nao_o_trecho():
    outro_trecho = compute_metrics(**{**BASE, "swim_distance_m": 75, "swim_time_s": 45})
    assert outro_trecho.swolf == 160.0
    assert outro_trecho.swolf_25 == 40.0


def test_swolf_costas_tambem_conta_duas_bracadas_por_ciclo():
    assert compute_metrics(**{**BASE, "stroke": "backstroke"}).swolf == 160.0


def test_swolf_peito_e_borboleta_contam_uma_bracada_por_ciclo():
    # 60 + 50 × 1 = 110; 110 × 25 ÷ 100 = 27,5
    for stroke in ("breaststroke", "butterfly"):
        m = compute_metrics(**{**BASE, "stroke": stroke})
        assert m.swolf == 110.0
        assert m.swolf_25 == 27.5


def test_mesma_prova_em_piscinas_diferentes_fica_na_mesma_escala():
    # 50 m em 30 s com 15 ciclos, em 25 m e em 50 m: valores comparáveis;
    # a diferença real entre as piscinas aparece nos tempos e ciclos medidos
    curta = compute_metrics(
        **{**BASE, "distance_m": 50, "total_time_s": 30, "total_cycle_count": 15,
           "swim_distance_m": 30, "swim_time_s": 20, "stroke_count": 10}
    )
    longa = compute_metrics(
        **{**BASE, "pool_length_m": 50, "distance_m": 50, "total_time_s": 30,
           "total_cycle_count": 15, "swim_distance_m": 40, "swim_time_s": 25,
           "stroke_count": 12}
    )
    assert curta.swolf_25 == longa.swolf_25 == 30.0


def test_swolf_sem_ciclos_da_prova_completa_fica_vazio():
    # registros anteriores ao campo total_cycle_count
    m = compute_metrics(**{**BASE, "total_cycle_count": None})
    assert m.swolf is None
    assert m.swolf_25 is None
    assert m.vn == 1.5


def test_swolf_no_medley_fica_vazio():
    m = compute_metrics(**{**BASE, "stroke": "medley"})
    assert m.swolf is None
    assert m.swolf_25 is None


def test_aceita_o_enum_do_nado():
    from app.models.training_session import Stroke

    assert compute_metrics(**{**BASE, "stroke": Stroke.FREESTYLE}).swolf == 160.0


def test_sem_ciclos_nao_quebra():
    m = compute_metrics(**{**BASE, "stroke_count": 0})
    assert m.cb is None
    assert m.swim_index is None
    assert m.cn == 0.0