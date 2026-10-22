from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Coach

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