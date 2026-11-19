from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, OwnedAthlete
from app.models import TrainingSession
from app.models.training_session import SessionType
from app.schemas.performance import MetricSummaryRead, PerformanceSummary
from app.schemas.report import (
    ReportChartPoint,
    ReportEvent,
    ReportPrediction,
    ReportRead,
    ReportRecordRead,
    ReportTotals,
)
from app.schemas.session import SessionRead
from app.services.performance import MIN_CONCLUSIVE_POINTS, summarize
from app.services.prediction import (
    MIN_RECORDS,
    MIN_TREND_RECORDS,
    InsufficientDataError,
    Record,
    predict_next,
    trend_status,
)
from app.services.report import (
    ReportRecord,
    chart_points,
    event_sort_key,
    event_times,
    in_period,
)

router = APIRouter(prefix="/athletes/{athlete_id}/report", tags=["Relatórios"])

SESSION_TYPE = {True: SessionType.COMPETITION, False: SessionType.TRAINING}


def _r(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def _record_read(record: ReportRecord) -> ReportRecordRead:
    return ReportRecordRead(
        session_id=record.session_id,
        session_date=record.session_date,
        session_type=SESSION_TYPE[record.is_competition],
        time_s=record.time_s,
    )


def _summary_read(summary) -> MetricSummaryRead | None:
    return None if summary is None else MetricSummaryRead(**asdict(summary))


def _event_block(
    event: tuple, sessions: list[TrainingSession], date_from: date | None, date_to: date | None
) -> ReportEvent | None:
    """Bloco de uma prova; None se a prova não tem registros no período."""
    records = [
        ReportRecord(
            order=i + 1,
            session_id=s.id,
            session_date=s.session_date,
            is_competition=s.session_type == SessionType.COMPETITION,
            time_s=float(s.total_time_s),
        )
        for i, s in enumerate(sessions)
    ]
    period_index = [
        i for i, r in enumerate(records) if in_period(r.session_date, date_from, date_to)
    ]
    if not period_index:
        return None
    period = [records[i] for i in period_index]
    times = event_times(period)
    metrics = summarize(
        [SessionRead.model_validate(sessions[i]).metrics.model_dump() for i in period_index]
    )

    # previsão, selo e reta: todo o histórico da prova (como no Início e no Desempenho)
    path = []
    try:
        result = predict_next(
            [Record(value=r.time_s, is_competition=r.is_competition) for r in records]
        )
    except InsufficientDataError:
        prediction = ReportPrediction(
            available=False,
            training_s=None,
            competition_s=None,
            coef_order=None,
            change_pct=None,
            status=None,
            r2=None,
            mae_s=None,
            mape_pct=None,
        )
    else:
        path = result.path
        change_pct, trend = trend_status(
            result.model.coef_order, records[-1].time_s, len(records)
        )
        prediction = ReportPrediction(
            available=True,
            training_s=_r(result.training_s),
            competition_s=_r(result.competition_s),
            coef_order=round(result.model.coef_order, 3),
            change_pct=round(change_pct, 2),
            status=trend,
            r2=_r(result.model.r2),
            mae_s=round(result.evaluation.mae_s, 2),
            mape_pct=round(result.evaluation.mape_pct, 2),
        )

    stroke, distance_m, pool_length_m = event
    return ReportEvent(
        stroke=stroke,
        distance_m=distance_m,
        pool_length_m=pool_length_m,
        n_history=len(records),
        n_records=times.n_records,
        n_trainings=times.n_trainings,
        n_competitions=times.n_competitions,
        time=_summary_read(times.summary),
        best=_record_read(times.best),
        last=_record_read(times.last),
        metrics=PerformanceSummary(**{k: _summary_read(v) for k, v in metrics.items()}),
        prediction=prediction,
        chart=[
            ReportChartPoint(
                order=p.order,
                session_date=p.session_date,
                session_type=(
                    None if p.is_competition is None else SESSION_TYPE[p.is_competition]
                ),
                time_s=p.time_s,
                model_training_s=_r(p.model_training_s),
                model_competition_s=_r(p.model_competition_s),
            )
            for p in chart_points(period, path, len(records))
        ],
    )


@router.get("", response_model=ReportRead)
def get_report(
    athlete: OwnedAthlete,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Relatório consolidado do atleta: resumo e um bloco por prova (AQ-22).

    O período filtra os registros exibidos; previsão, selo e reta do modelo
    usam todo o histórico de cada prova.
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A data inicial não pode ser posterior à final",
        )

    sessions = db.scalars(
        select(TrainingSession)
        .where(TrainingSession.athlete_id == athlete.id)
        .order_by(TrainingSession.session_date, TrainingSession.id)
    ).all()

    # prova → registros em ordem cronológica (todo o histórico)
    by_event: dict[tuple, list[TrainingSession]] = {}
    for s in sessions:
        by_event.setdefault((s.stroke, s.distance_m, s.pool_length_m), []).append(s)

    events = [
        block
        for event, items in by_event.items()
        if (block := _event_block(event, items, date_from, date_to)) is not None
    ]
    events.sort(key=lambda e: event_sort_key(e.n_records, e.last.session_date))

    period_dates = [
        s.session_date for s in sessions if in_period(s.session_date, date_from, date_to)
    ]

    return ReportRead(
        athlete_id=athlete.id,
        athlete_name=athlete.name,
        athlete_active=athlete.active,
        birth_date=athlete.birth_date,
        sex=athlete.sex,
        date_from=date_from,
        date_to=date_to,
        first_session_date=min(period_dates) if period_dates else None,
        last_session_date=max(period_dates) if period_dates else None,
        totals=ReportTotals(
            records=sum(e.n_records for e in events),
            trainings=sum(e.n_trainings for e in events),
            competitions=sum(e.n_competitions for e in events),
            events=len(events),
        ),
        min_records=MIN_RECORDS,
        min_trend_records=MIN_TREND_RECORDS,
        min_conclusive_points=MIN_CONCLUSIVE_POINTS,
        events=events,
    )