"""Resumo de cada atleta para os cartões da tela "Meus atletas" (AQ-26).

Para cada atleta: quantos registros tem, as métricas do registro mais recente
(SWOLF, CB e VN, as mesmas do cartão) e o selo de tendência da prova principal,
com as mesmas regras do painel Início (previsão a partir de 6 registros na
prova, selo a partir de 10).
"""

from dataclasses import dataclass
from datetime import date

from app.services.metrics import compute_metrics
from app.services.prediction import (
    MIN_TREND_RECORDS,
    InsufficientDataError,
    Record,
    TrendStatus,
    pick_main_event,
    predict_next,
    trend_status,
)

COMPETITION = "competition"  # valor de SessionType.COMPETITION (sem importar o modelo do banco)


@dataclass(frozen=True)
class LastSession:
    session_date: date
    session_type: str
    stroke: str
    distance_m: int
    pool_length_m: int
    total_time_s: float
    swolf: float | None
    cb: float | None
    vn: float | None


@dataclass(frozen=True)
class MainTrend:
    stroke: str
    distance_m: int
    pool_length_m: int
    n_records: int
    min_records: int  # registros exigidos para o selo (MIN_TREND_RECORDS)
    status: TrendStatus | None  # None com menos de min_records registros


@dataclass(frozen=True)
class AthleteSummary:
    sessions_count: int
    last_session: LastSession | None
    main_trend: MainTrend | None  # None quando nenhuma prova tem 6 registros


def _value(enum_or_str) -> str:
    return getattr(enum_or_str, "value", enum_or_str)


def _last_session(session) -> LastSession:
    metrics = compute_metrics(
        stroke=session.stroke,
        distance_m=session.distance_m,
        total_time_s=session.total_time_s,
        pool_length_m=session.pool_length_m,
        stroke_count=session.stroke_count,
        swim_distance_m=session.swim_distance_m,
        swim_time_s=session.swim_time_s,
        total_cycle_count=session.total_cycle_count,
    )
    return LastSession(
        session_date=session.session_date,
        session_type=_value(session.session_type),
        stroke=_value(session.stroke),
        distance_m=session.distance_m,
        pool_length_m=session.pool_length_m,
        total_time_s=float(session.total_time_s),
        swolf=metrics.swolf,
        cb=metrics.cb,
        vn=metrics.vn,
    )


def _main_trend(sessions: list) -> MainTrend | None:
    events: dict[tuple, list] = {}
    for session in sessions:
        key = (_value(session.stroke), session.distance_m, session.pool_length_m)
        events.setdefault(key, []).append(session)

    main = pick_main_event(
        {key: (len(items), items[-1].session_date) for key, items in events.items()}
    )
    if main is None:
        return None

    items = events[main]
    records = [
        Record(
            value=float(s.total_time_s),
            is_competition=_value(s.session_type) == COMPETITION,
        )
        for s in items
    ]
    try:
        result = predict_next(records)
    except InsufficientDataError:
        return None
    _, status = trend_status(
        result.model.coef_order, float(items[-1].total_time_s), len(items)
    )
    stroke, distance_m, pool_length_m = main
    return MainTrend(
        stroke=stroke,
        distance_m=distance_m,
        pool_length_m=pool_length_m,
        n_records=len(items),
        min_records=MIN_TREND_RECORDS,
        status=status,
    )


def summarize_athlete(sessions: list) -> AthleteSummary:
    """Resumo a partir dos registros do atleta em ordem cronológica (data e id)."""
    if not sessions:
        return AthleteSummary(sessions_count=0, last_session=None, main_trend=None)
    return AthleteSummary(
        sessions_count=len(sessions),
        last_session=_last_session(sessions[-1]),
        main_trend=_main_trend(sessions),
    )