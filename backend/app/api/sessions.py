from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentCoach, DbSession, OwnedAthlete
from app.models import Athlete, TrainingSession
from app.models.training_session import SessionType, Stroke
from app.schemas.session import SessionCreate, SessionListItem, SessionPage, SessionRead
router = APIRouter(
    prefix="/athletes/{athlete_id}/sessions", tags=["Sessões de treino"]
)


def _get_record(db: DbSession, athlete: Athlete, session_id: int) -> TrainingSession:
    record = db.scalar(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.athlete_id == athlete.id,
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada"
        )
    return record


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(data: SessionCreate, athlete: OwnedAthlete, db: DbSession):
    if not athlete.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Atleta inativo: reative-o para registrar novas sessões",
        )
    record = TrainingSession(athlete_id=athlete.id, **data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[SessionRead])
def list_sessions(
    athlete: OwnedAthlete,
    db: DbSession,
    session_type: SessionType | None = None,
    stroke: Stroke | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A data inicial não pode ser posterior à final",
        )
    stmt = select(TrainingSession).where(TrainingSession.athlete_id == athlete.id)
    if session_type:
        stmt = stmt.where(TrainingSession.session_type == session_type)
    if stroke:
        stmt = stmt.where(TrainingSession.stroke == stroke)
    if date_from:
        stmt = stmt.where(TrainingSession.session_date >= date_from)
    if date_to:
        stmt = stmt.where(TrainingSession.session_date <= date_to)
    stmt = (
        stmt.order_by(TrainingSession.session_date.desc(), TrainingSession.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: int, athlete: OwnedAthlete, db: DbSession):
    return _get_record(db, athlete, session_id)


@router.put("/{session_id}", response_model=SessionRead)
def update_session(
    session_id: int, data: SessionCreate, athlete: OwnedAthlete, db: DbSession
):
    record = _get_record(db, athlete, session_id)
    for field, value in data.model_dump().items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, athlete: OwnedAthlete, db: DbSession):
    record = _get_record(db, athlete, session_id)
    db.delete(record)
    db.commit()

coach_router = APIRouter(prefix="/sessions", tags=["Sessões de treino"])


@coach_router.get("", response_model=SessionPage)
def list_all_sessions(
    coach: CurrentCoach,
    db: DbSession,
    athlete_id: int | None = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
    session_type: SessionType | None = None,
    stroke: Stroke | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A data inicial não pode ser posterior à final",
        )

    conditions = [Athlete.coach_id == coach.id]
    if athlete_id is not None:
        conditions.append(TrainingSession.athlete_id == athlete_id)
    if search and search.strip():
        term = (
            search.strip()
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        conditions.append(Athlete.name.ilike(f"%{term}%", escape="\\"))
    if session_type:
        conditions.append(TrainingSession.session_type == session_type)
    if stroke:
        conditions.append(TrainingSession.stroke == stroke)
    if date_from:
        conditions.append(TrainingSession.session_date >= date_from)
    if date_to:
        conditions.append(TrainingSession.session_date <= date_to)

    join_on = TrainingSession.athlete_id == Athlete.id
    total = (
        db.scalar(
            select(func.count())
            .select_from(TrainingSession)
            .join(Athlete, join_on)
            .where(*conditions)
        )
        or 0
    )
    rows = db.execute(
        select(TrainingSession, Athlete.name)
        .join(Athlete, join_on)
        .where(*conditions)
        .order_by(TrainingSession.session_date.desc(), TrainingSession.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return SessionPage(
        items=[
            SessionListItem.model_validate(record).model_copy(
                update={"athlete_name": name}
            )
            for record, name in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )