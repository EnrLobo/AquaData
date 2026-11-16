from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentCoach, DbSession
from app.models import Athlete, TrainingSession
from app.models.training_session import SessionType
from app.schemas.dashboard import DashboardAthlete, DashboardPrediction, DashboardRead
from app.schemas.session import SessionListItem
from app.services.prediction import (
    MIN_RECORDS,
    InsufficientDataError,
    Record,
    TrendStatus,
    classify_trend,
    pick_main_event,
    predict_next,
)

router = APIRouter(prefix="/dashboard", tags=["Painel"])

RECENT_DAYS = 30  # o campo sessions_last_30_days assume este valor
RECENT_SESSIONS = 5
OVERVIEW_ATHLETES = 6

# ordem da seção: quem precisa de atenção aparece primeiro
STATUS_ORDER = {TrendStatus.ATTENTION: 0, TrendStatus.STABLE: 1, TrendStatus.IMPROVING: 2}


def athlete_predictions(db: Session, coach_id: int) -> list[DashboardPrediction]:
    """Previsão do próximo registro em cada prova com o mínimo de registros, por atleta ativo.

    Cada previsão indica se a prova é a principal do atleta (a mais registrada
    entre as elegíveis; desempate pelo registro mais recente), usada por padrão
    no painel. Usa o mesmo modelo da tela Desempenho.
    """
    rows = db.execute(
        select(TrainingSession, Athlete.name)
        .join(Athlete, TrainingSession.athlete_id == Athlete.id)
        .where(Athlete.coach_id == coach_id, Athlete.active.is_(True))
        .order_by(TrainingSession.athlete_id, TrainingSession.session_date, TrainingSession.id)
    ).all()

    # atleta → prova → registros em ordem cronológica
    by_athlete: dict[int, dict[tuple, list[TrainingSession]]] = {}
    names: dict[int, str] = {}
    for session, name in rows:
        names[session.athlete_id] = name
        event = (session.stroke, session.distance_m, session.pool_length_m)
        by_athlete.setdefault(session.athlete_id, {}).setdefault(event, []).append(session)

    predictions = []
    for athlete_id, events in by_athlete.items():
        main = pick_main_event(
            {key: (len(items), items[-1].session_date) for key, items in events.items()}
        )
        for event, sessions in events.items():
            if len(sessions) < MIN_RECORDS:
                continue
            prediction = _predict_event(athlete_id, names[athlete_id], event, sessions, main)
            if prediction is not None:
                predictions.append(prediction)

    predictions.sort(key=lambda p: (STATUS_ORDER[p.status], p.athlete_name.lower()))
    return predictions


def _predict_event(
    athlete_id: int,
    athlete_name: str,
    event: tuple,
    sessions: list[TrainingSession],
    main: tuple | None,
) -> DashboardPrediction | None:
    """Previsão do próximo registro de um atleta numa prova (registros em ordem cronológica)."""
    records = [
        Record(
            value=float(s.total_time_s),
            is_competition=s.session_type == SessionType.COMPETITION,
        )
        for s in sessions
    ]
    try:
        result = predict_next(records)
    except InsufficientDataError:
        return None
    last = sessions[-1]
    last_time = float(last.total_time_s)
    change_pct, status = classify_trend(result.model.coef_order, last_time)
    stroke, distance_m, pool_length_m = event
    return DashboardPrediction(
        athlete_id=athlete_id,
        athlete_name=athlete_name,
        stroke=stroke,
        distance_m=distance_m,
        pool_length_m=pool_length_m,
        is_main=event == main,
        n_records=len(sessions),
        last_time_s=last_time,
        last_session_date=last.session_date,
        last_session_type=last.session_type,
        training_s=None if result.training_s is None else round(result.training_s, 2),
        competition_s=None if result.competition_s is None else round(result.competition_s, 2),
        coef_order=round(result.model.coef_order, 3),
        change_pct=round(change_pct, 2),
        status=status,
        mae_s=round(result.evaluation.mae_s, 2),
    )


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

    predictions = athlete_predictions(db, coach.id)

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
        predictions=predictions,
        athletes_without_prediction=max(
            active_athletes - len({p.athlete_id for p in predictions}), 0
        ),
    )