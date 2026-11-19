"""Relatório consolidado por atleta (AQ-22): funções puras de apoio.

O relatório reúne todas as provas do atleta. O período escolhido pelo
treinador filtra os registros exibidos (resumo, tempos, métricas e pontos do
gráfico); a previsão, o selo e a reta do modelo usam sempre todo o histórico
da prova, como no Início e no Desempenho.
"""

from dataclasses import dataclass
from datetime import date

from app.services.performance import MetricSummary, summarize_metric
from app.services.prediction import PathPoint

TIME_DIGITS = 2


@dataclass(frozen=True)
class ReportRecord:
    """Um registro da prova, com a ordem que ele tem no histórico completo."""

    order: int  # 1 = primeiro registro da prova (todo o histórico)
    session_id: int
    session_date: date
    is_competition: bool
    time_s: float


def in_period(day: date, date_from: date | None, date_to: date | None) -> bool:
    """O dia está no período? Sem limite informado, o lado fica aberto."""
    if date_from is not None and day < date_from:
        return False
    if date_to is not None and day > date_to:
        return False
    return True


def filter_period(
    records: list[ReportRecord], date_from: date | None, date_to: date | None
) -> list[ReportRecord]:
    return [r for r in records if in_period(r.session_date, date_from, date_to)]


@dataclass(frozen=True)
class EventTimes:
    """Tempos de uma prova no período."""

    n_records: int
    n_trainings: int
    n_competitions: int
    best: ReportRecord  # menor tempo (no empate, o mais antigo)
    last: ReportRecord  # registro mais recente
    summary: MetricSummary  # primeiro, último, melhor, média, variação e tendência do período


def event_times(period: list[ReportRecord]) -> EventTimes | None:
    """Resume os tempos da prova no período (registros em ordem cronológica)."""
    if not period:
        return None
    summary = summarize_metric([r.time_s for r in period], "down", TIME_DIGITS)
    best = min(period, key=lambda r: (r.time_s, r.order))
    competitions = sum(1 for r in period if r.is_competition)
    return EventTimes(
        n_records=len(period),
        n_trainings=len(period) - competitions,
        n_competitions=competitions,
        best=best,
        last=period[-1],
        summary=summary,
    )


@dataclass(frozen=True)
class ChartPoint:
    """Ponto do gráfico: registro do período (com tempo) ou registro futuro (só a reta)."""

    order: int
    session_date: date | None  # None nos registros futuros
    is_competition: bool | None  # None nos registros futuros
    time_s: float | None
    model_training_s: float | None
    model_competition_s: float | None


def chart_points(
    period: list[ReportRecord], path: list[PathPoint], n_history: int
) -> list[ChartPoint]:
    """Monta o gráfico do período com a reta do modelo (todo o histórico) e a projeção.

    Cada registro do período recebe o valor da reta na sua ordem do histórico;
    depois vêm os registros futuros da projeção. Sem reta (previsão
    indisponível), só os registros do período.
    """
    by_order = {p.order: p for p in path}
    points = []
    for record in period:
        model = by_order.get(record.order)
        points.append(
            ChartPoint(
                order=record.order,
                session_date=record.session_date,
                is_competition=record.is_competition,
                time_s=record.time_s,
                model_training_s=None if model is None else model.training_s,
                model_competition_s=None if model is None else model.competition_s,
            )
        )
    for p in path:
        if p.order > n_history:
            points.append(
                ChartPoint(
                    order=p.order,
                    session_date=None,
                    is_competition=None,
                    time_s=None,
                    model_training_s=p.training_s,
                    model_competition_s=p.competition_s,
                )
            )
    return points


def event_sort_key(n_period: int, last_date: date) -> tuple:
    """Ordem das provas no relatório: mais registros no período primeiro; depois a mais recente."""
    return (-n_period, -last_date.toordinal())