from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Coach

from sqlalchemy import select
from app.models import Athlete, Coach

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_coach(
    token: Annotated[str, Depends(oauth2_scheme)], db: DbSession
) -> Coach:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise credentials_error

    coach = db.get(Coach, int(subject))
    if coach is None:
        raise credentials_error
    return coach


CurrentCoach = Annotated[Coach, Depends(get_current_coach)]

def get_owned_athlete(athlete_id: int, coach: CurrentCoach, db: DbSession) -> Athlete:
    athlete = db.scalar(
        select(Athlete).where(Athlete.id == athlete_id, Athlete.coach_id == coach.id)
    )
    if athlete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Atleta não encontrado"
        )
    return athlete


OwnedAthlete = Annotated[Athlete, Depends(get_owned_athlete)]