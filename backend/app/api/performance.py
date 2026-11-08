from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import DbSession, OwnedAthlete
from app.models import TrainingSession
from app.models.training_session import SessionType, Stroke
from app.schemas.performance import (
    MetricSummaryRead,
    PerformanceEvent,
    PerformanceRead,
    PerformanceSummary,
)
from app.schemas.session import SessionRead
from app.services.performance import summarize

router = APIRouter(prefix="/athletes/{athlete_id}/performance", tags=["Desempenho"])

MAX_POINTS = 500  # treinos mais recentes devolvidos para o gráfico


@router.get("", response_model=PerformanceRead)
def get_performance(
    athlete: OwnedAthlete,
    db: DbSession,
    stroke: Stroke | None = None,
    distance_m: int | None = None,
    pool_length_m: int | None = None,
    session_type: SessionType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A data inicial não pode ser posterior à final",
        )

    event_rows = db.execute(
        select(
            TrainingSession.stroke,
            TrainingSession.distance_m,
            TrainingSession.pool_length_m,
            func.count(),
        )
        .where(TrainingSession.athlete_id == athlete.id)
        .group_by(
            TrainingSession.stroke,
            TrainingSession.distance_m,
            TrainingSession.pool_length_m,
        )
        .order_by(TrainingSession.stroke, TrainingSession.distance_m, TrainingSession.pool_length_m)
    ).all()
    events = [
        PerformanceEvent(stroke=s, distance_m=d, pool_length_m=p, sessions=n)
        for s, d, p, n in event_rows
    ]

    # Sem nado informado, usa o mais frequente: misturar nados no mesmo gráfico
    # não faz sentido, porque cada nado tem faixas de valores diferentes.
    if stroke is None and events:
        totals: dict[Stroke, int] = {}
        for event in events:
            totals[event.stroke] = totals.get(event.stroke, 0) + event.sessions
        stroke = max(totals, key=lambda s: totals[s])

    conditions = [TrainingSession.athlete_id == athlete.id]
    if stroke:
        conditions.append(TrainingSession.stroke == stroke)
    if distance_m is not None:
        conditions.append(TrainingSession.distance_m == distance_m)
    if pool_length_m is not None:
        conditions.append(TrainingSession.pool_length_m == pool_length_m)
    if session_type:
        conditions.append(TrainingSession.session_type == session_type)
    if date_from:
        conditions.append(TrainingSession.session_date >= date_from)
    if date_to:
        conditions.append(TrainingSession.session_date <= date_to)

    total = (
        db.scalar(select(func.count()).select_from(TrainingSession).where(*conditions)) or 0
    )
    records = db.scalars(
        select(TrainingSession)
        .where(*conditions)
        .order_by(TrainingSession.session_date.desc(), TrainingSession.id.desc())
        .limit(MAX_POINTS)
    ).all()

    sessions = [SessionRead.model_validate(r) for r in reversed(records)]
    summary = summarize([s.metrics.model_dump() for s in sessions])

    return PerformanceRead(
        athlete_id=athlete.id,
        athlete_name=athlete.name,
        athlete_active=athlete.active,
        stroke=stroke,
        events=events,
        sessions=sessions,
        total=total,
        truncated=total > len(sessions),
        summary=PerformanceSummary(
            **{
                key: None if value is None else MetricSummaryRead(**asdict(value))
                for key, value in summary.items()
            }
        ),
    )