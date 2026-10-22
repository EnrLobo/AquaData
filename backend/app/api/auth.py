from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentCoach, DbSession
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import Coach
from app.schemas.auth import CoachCreate, CoachRead, Token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=CoachRead, status_code=status.HTTP_201_CREATED)
def register(data: CoachCreate, db: DbSession):
    email = data.email.lower()
    if db.scalar(select(Coach).where(Coach.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado"
        )

    coach = Coach(
        name=data.name, email=email, password_hash=hash_password(data.password)
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    coach = db.scalar(select(Coach).where(Coach.email == form.username.lower()))

    # Sempre verifica um hash, mesmo sem usuário, para não revelar quais e-mails existem
    hashed = coach.password_hash if coach else DUMMY_HASH
    password_ok = verify_password(form.password, hashed)

    if coach is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(coach.id)))


@router.get("/me", response_model=CoachRead)
def me(current_coach: CurrentCoach):
    return current_coach