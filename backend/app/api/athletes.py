from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentCoach, DbSession
from app.models import Athlete, Coach
from app.schemas.athlete import AthleteCreate, AthleteRead, AthleteUpdate

router = APIRouter(prefix="/athletes", tags=["Atletas"])


def _get_owned(db: DbSession, coach: Coach, athlete_id: int) -> Athlete:
    athlete = db.scalar(
        select(Athlete).where(
            Athlete.id == athlete_id, Athlete.coach_id == coach.id
        )
    )
    if athlete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Atleta não encontrado"
        )
    return athlete


def _is_duplicate(
    db: DbSession, coach_id: int, name: str, birth_date, exclude_id: int | None = None
) -> bool:
    stmt = select(Athlete.id).where(
        Athlete.coach_id == coach_id,
        func.lower(Athlete.name) == name.lower(),
        Athlete.birth_date == birth_date,
    )
    if exclude_id is not None:
        stmt = stmt.where(Athlete.id != exclude_id)
    return db.scalar(stmt) is not None


@router.post("", response_model=AthleteRead, status_code=status.HTTP_201_CREATED)
def create_athlete(data: AthleteCreate, coach: CurrentCoach, db: DbSession):
    if _is_duplicate(db, coach.id, data.name, data.birth_date):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um atleta com esse nome e data de nascimento",
        )
    athlete = Athlete(coach_id=coach.id, **data.model_dump())
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return athlete


@router.get("", response_model=list[AthleteRead])
def list_athletes(
    coach: CurrentCoach,
    db: DbSession,
    active: bool | None = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Athlete).where(Athlete.coach_id == coach.id)
    if active is not None:
        stmt = stmt.where(Athlete.active == active)
    if search and search.strip():
        term = (
            search.strip()
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        stmt = stmt.where(Athlete.name.ilike(f"%{term}%", escape="\\"))
    stmt = stmt.order_by(Athlete.name, Athlete.id).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{athlete_id}", response_model=AthleteRead)
def get_athlete(athlete_id: int, coach: CurrentCoach, db: DbSession):
    return _get_owned(db, coach, athlete_id)


@router.patch("/{athlete_id}", response_model=AthleteRead)
def update_athlete(
    athlete_id: int, data: AthleteUpdate, coach: CurrentCoach, db: DbSession
):
    athlete = _get_owned(db, coach, athlete_id)
    updates = data.model_dump(exclude_unset=True)

    if not updates or any(value is None for value in updates.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Informe ao menos um campo, sem valores nulos",
        )

    if "name" in updates or "birth_date" in updates:
        name = updates.get("name", athlete.name)
        birth_date = updates.get("birth_date", athlete.birth_date)
        if _is_duplicate(db, coach.id, name, birth_date, exclude_id=athlete.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um atleta com esse nome e data de nascimento",
            )

    for field, value in updates.items():
        setattr(athlete, field, value)
    db.commit()
    db.refresh(athlete)
    return athlete