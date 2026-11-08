from dataclasses import dataclass

# Braçadas por ciclo, para o SWOLF (contagem por braçada, como em Madou et al., 2021).
# Crawl e costas: braços alternados, 1 ciclo = 2 braçadas.
# Peito e borboleta: braços simultâneos, 1 ciclo = 1 braçada.
# Medley fica de fora: mistura nados com regras diferentes.
STROKES_PER_CYCLE = {
    "freestyle": 2,
    "backstroke": 2,
    "breaststroke": 1,
    "butterfly": 1,
}

SWOLF_REFERENCE_M = 25  # base do SWOLF a cada 25 m


@dataclass(frozen=True)
class Metrics:
    vm: float | None  # velocidade média, m/s
    vn: float | None  # velocidade de nado, m/s
    cb: float | None  # comprimento de braçada, m por ciclo
    cn: float | None  # cadência, ciclos por minuto
    swim_index: float | None  # índice de nado (IN), m²/s
    swolf: float | None  # tempo total + braçadas da prova completa
    swolf_25: float | None  # SWOLF proporcional a 25 m


def _div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def total_strokes(stroke, total_cycle_count) -> float | None:
    """Braçadas da prova completa, a partir dos ciclos contados pelo treinador."""
    factor = STROKES_PER_CYCLE.get(getattr(stroke, "value", stroke))
    if total_cycle_count is None or factor is None:
        return None
    return float(total_cycle_count) * factor


def compute_swolf(*, stroke, total_time_s, total_cycle_count) -> float | None:
    """SWOLF simples (Madou et al., 2021): tempo total (s) + braçadas da prova completa.

    Devolve None quando faltam os ciclos da prova (registros antigos) ou no medley.
    """
    strokes = total_strokes(stroke, total_cycle_count)
    if strokes is None:
        return None
    return float(total_time_s) + strokes


def compute_swolf_25(*, swolf, distance_m) -> float | None:
    """SWOLF a cada 25 m: SWOLF × 25 ÷ distância total (proposta da equipe).

    Põe provas de distâncias e piscinas diferentes na mesma escala; a diferença
    que sobra entre piscinas de 25 m e 50 m reflete o efeito das viradas.
    """
    if swolf is None:
        return None
    return _div(swolf * SWOLF_REFERENCE_M, float(distance_m))


def compute_metrics(
    *,
    stroke,
    distance_m,
    total_time_s,
    pool_length_m,
    stroke_count,
    swim_distance_m,
    swim_time_s,
    total_cycle_count=None,
) -> Metrics:
    """Calcula as métricas de uma sessão.

    stroke_count = ciclos de braçada no trecho de nado puro (base de VN, CB, cadência e IN).
    total_cycle_count = ciclos de braçada na prova completa (base do SWOLF).
    pool_length_m entra na validação da sessão; as fórmulas atuais não dependem dele.
    """
    distance = float(distance_m)
    total = float(total_time_s)
    cycles = float(stroke_count)
    swim_d = float(swim_distance_m)
    swim_t = float(swim_time_s)

    vm = _div(distance, total)
    vn = _div(swim_d, swim_t)
    cb = _div(swim_d, cycles)
    cn = _div(cycles * 60, swim_t)
    swim_index = cb * vn if cb is not None and vn is not None else None
    swolf = compute_swolf(
        stroke=stroke, total_time_s=total_time_s, total_cycle_count=total_cycle_count
    )
    swolf_25 = compute_swolf_25(swolf=swolf, distance_m=distance_m)

    return Metrics(
        vm=_round(vm, 2),
        vn=_round(vn, 2),
        cb=_round(cb, 2),
        cn=_round(cn, 1),
        swim_index=_round(swim_index, 2),
        swolf=_round(swolf, 1),
        swolf_25=_round(swolf_25, 1),
    )