from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    vm: float | None  # velocidade média, m/s
    vn: float | None  # velocidade de nado, m/s
    cb: float | None  # comprimento de braçada, m por ciclo
    cn: float | None  # cadência, ciclos por minuto
    swim_index: float | None  # índice de nado (IN), m²/s
    swolf: float | None


def _div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def compute_metrics(
    *,
    distance_m,
    total_time_s,
    pool_length_m,
    stroke_count,
    swim_distance_m,
    swim_time_s,
) -> Metrics:
    """Calcula as métricas de uma sessão. stroke_count = ciclos de braçada no trecho de nado puro."""
    distance = float(distance_m)
    total = float(total_time_s)
    pool = float(pool_length_m)
    cycles = float(stroke_count)
    swim_d = float(swim_distance_m)
    swim_t = float(swim_time_s)

    vm = _div(distance, total)
    vn = _div(swim_d, swim_t)
    cb = _div(swim_d, cycles)
    cn = _div(cycles * 60, swim_t)
    swim_index = cb * vn if cb is not None and vn is not None else None
    swolf = _div((swim_t + cycles) * pool, swim_d)

    return Metrics(
        vm=_round(vm, 2),
        vn=_round(vn, 2),
        cb=_round(cb, 2),
        cn=_round(cn, 1),
        swim_index=_round(swim_index, 2),
        swolf=_round(swolf, 1),
    )