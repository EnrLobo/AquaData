from dataclasses import dataclass
from statistics import fmean
from typing import Literal

Direction = Literal["up", "down"] | None

# Sentido de melhora de cada métrica. Cadência não tem sentido fixo:
# subir ou descer pode ser bom ou ruim, dependendo do CB e da prova.
METRIC_DIRECTION: dict[str, Direction] = {
    "vm": "up",
    "vn": "up",
    "cb": "up",
    "cn": None,
    "swim_index": "up",
    "swolf": "down",
    "swolf_25": "down",
}

METRIC_DIGITS: dict[str, int] = {
    "vm": 2,
    "vn": 2,
    "cb": 2,
    "cn": 1,
    "swim_index": 2,
    "swolf": 1,
    "swolf_25": 1,
}

MIN_TREND_POINTS = 3  # com menos treinos, a reta não indica tendência (decisão da equipe)


@dataclass(frozen=True)
class Trend:
    """Reta de regressão linear (mínimos quadrados) da métrica pela ordem dos treinos."""

    slope: float  # variação estimada por treino
    start: float  # valor da reta no primeiro treino com dado
    end: float  # valor da reta no último treino com dado
    first_index: int  # posição (na série completa) do primeiro treino com dado
    last_index: int  # posição do último treino com dado
    r2: float | None  # coeficiente de determinação (quanto a reta explica a variação)


@dataclass(frozen=True)
class MetricSummary:
    count: int  # treinos com valor calculado
    first: float  # valor no treino mais antigo do período
    last: float  # valor no treino mais recente do período
    best: float | None  # melhor valor (None quando a métrica não tem sentido de melhora)
    mean: float
    change: float  # last - first
    change_pct: float | None  # variação percentual sobre o primeiro valor
    trend: Trend | None  # None com menos de MIN_TREND_POINTS treinos
    improved: bool | None  # pela inclinação da tendência; None sem tendência ou sem sentido


def linear_trend(points: list[tuple[int, float]], digits: int = 2) -> Trend | None:
    """Ajusta y = a + b·x por mínimos quadrados, com x = posição do treino na série.

    Devolve None com menos de MIN_TREND_POINTS pontos ou se todos tiverem o mesmo x.
    """
    if len(points) < MIN_TREND_POINTS:
        return None
    xs = [float(x) for x, _ in points]
    ys = [y for _, y in points]
    mean_x, mean_y = fmean(xs), fmean(ys)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x

    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = None if ss_tot == 0 else 1 - ss_res / ss_tot

    first_x, last_x = points[0][0], points[-1][0]
    return Trend(
        slope=round(slope, digits + 1),
        start=round(intercept + slope * first_x, digits),
        end=round(intercept + slope * last_x, digits),
        first_index=first_x,
        last_index=last_x,
        r2=None if r2 is None else round(r2, 2),
    )


def summarize_metric(
    values: list[float | None], direction: Direction, digits: int = 2
) -> MetricSummary | None:
    """Resume uma série em ordem cronológica (mais antigo primeiro).

    A posição na lista é o eixo x da tendência; valores nulos são ignorados,
    mas mantêm a posição dos demais (o gráfico usa o mesmo eixo).
    """
    points = [(i, v) for i, v in enumerate(values) if v is not None]
    if not points:
        return None

    present = [v for _, v in points]
    first, last = present[0], present[-1]
    change = last - first
    change_pct = change / first * 100 if first else None

    if direction == "up":
        best = max(present)
    elif direction == "down":
        best = min(present)
    else:
        best = None

    trend = linear_trend(points, digits)

    improved: bool | None = None
    if trend is not None and direction is not None and trend.slope != 0:
        improved = trend.slope > 0 if direction == "up" else trend.slope < 0

    return MetricSummary(
        count=len(present),
        first=round(first, digits),
        last=round(last, digits),
        best=None if best is None else round(best, digits),
        mean=round(fmean(present), digits),
        change=round(change, digits),
        change_pct=None if change_pct is None else round(change_pct, 1),
        trend=trend,
        improved=improved,
    )


def summarize(series: list[dict[str, float | None]]) -> dict[str, MetricSummary | None]:
    """Resume todas as métricas de uma lista de treinos em ordem cronológica."""
    return {
        key: summarize_metric(
            [item.get(key) for item in series], direction, METRIC_DIGITS[key]
        )
        for key, direction in METRIC_DIRECTION.items()
    }