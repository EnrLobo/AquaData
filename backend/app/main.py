from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import settings
from app.api import auth, health
from app.api import athletes, auth, health

from app.api import athletes, auth, health, sessions

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API do aquaData: análise de performance de atletas de natação.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(athletes.router)
app.include_router(sessions.router)
