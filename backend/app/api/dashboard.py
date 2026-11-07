from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentCoach, DbSession
from app.models import Athlete, TrainingSession
from app.schemas.dashboard import DashboardAthlete, DashboardRead
from app.schemas.session import SessionListItem

router = APIRouter(prefix="/dashboard", tags=["Painel"])

RECENT_DAYS = 30  # o campo sessions_last_30_days assume este valor
RECENT_SESSIONS = 5
OVERVIEW_ATHLETES = 6


@router.get("", response_model=DashboardRead)
def get_dashboard(coach: CurrentCoach, db: DbSession):
    since = date.today() - timedelta(days=RECENT_DAYS)
    owned = Athlete.coach_id == coach.id
    join_on = TrainingSession.athlete_id == Athlete.id

    active_athletes = (
        db.scalar(
            select(func.count())
            .select_from(Athlete)
            .where(owned, Athlete.active.is_(True))
        )
        or 0
    )

    sessions_total = (
        db.scalar(
            select(func.count())
            .select_from(TrainingSession)
            .join(Athlete, join_on)
            .where(owned)
        )
        or 0
    )

    sessions_recent = (
        db.scalar(
            select(func.count())
            .select_from(TrainingSession)
            .join(Athlete, join_on)
            .where(owned, TrainingSession.session_date >= since)
        )
        or 0
    )

    trained_recently = select(TrainingSession.athlete_id).where(
        TrainingSession.session_date >= since
    )
    without_recent = (
        db.scalar(
            select(func.count())
            .select_from(Athlete)
            .where(owned, Athlete.active.is_(True), Athlete.id.not_in(trained_recently))
        )
        or 0
    )

    recent_rows = db.execute(
        select(TrainingSession, Athlete.name)
        .join(Athlete, join_on)
        .where(owned)
        .order_by(TrainingSession.session_date.desc(), TrainingSession.id.desc())
        .limit(RECENT_SESSIONS)
    ).all()

    athlete_rows = db.execute(
        select(Athlete, func.max(TrainingSession.session_date))
        .outerjoin(TrainingSession, join_on)
        .where(owned, Athlete.active.is_(True))
        .group_by(Athlete.id)
        .order_by(func.max(TrainingSession.session_date).desc().nullslast(), Athlete.name)
        .limit(OVERVIEW_ATHLETES)
    ).all()

    return DashboardRead(
        active_athletes=active_athletes,
        sessions_total=sessions_total,
        sessions_last_30_days=sessions_recent,
        athletes_without_recent_sessions=without_recent,
        recent_sessions=[
            SessionListItem.model_validate(record).model_copy(
                update={"athlete_name": name}
            )
            for record, name in recent_rows
        ],
        athletes=[
            DashboardAthlete(
                id=athlete.id,
                name=athlete.name,
                birth_date=athlete.birth_date,
                sex=athlete.sex,
                last_session_date=last_date,
            )
            for athlete, last_date in athlete_rows
        ],
    )