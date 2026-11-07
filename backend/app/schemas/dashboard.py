from datetime import date

from pydantic import BaseModel

from app.models.athlete import Sex
from app.schemas.session import SessionListItem


class DashboardAthlete(BaseModel):
    id: int
    name: str
    birth_date: date
    sex: Sex
    last_session_date: date | None


class DashboardRead(BaseModel):
    active_athletes: int
    sessions_total: int
    sessions_last_30_days: int
    athletes_without_recent_sessions: int
    recent_sessions: list[SessionListItem]
    athletes: list[DashboardAthlete]