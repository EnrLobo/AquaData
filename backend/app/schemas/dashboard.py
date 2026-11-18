from datetime import date

from pydantic import BaseModel

from app.models.athlete import Sex
from app.models.training_session import SessionType, Stroke
from app.schemas.session import SessionListItem
from app.services.prediction import TrendStatus


class DashboardAthlete(BaseModel):
    id: int
    name: str
    birth_date: date
    sex: Sex
    last_session_date: date | None


class DashboardPrediction(BaseModel):
    """Previsão do próximo registro de um atleta numa prova (AQ-20)."""

    athlete_id: int
    athlete_name: str
    stroke: Stroke
    distance_m: int
    pool_length_m: int
    is_main: bool  # prova principal do atleta (a mais registrada entre as que têm previsão)
    n_records: int
    last_time_s: float
    last_session_date: date
    last_session_type: SessionType
    training_s: float | None  # próximo registro como treino
    competition_s: float | None  # próximo registro como competição (None sem os dois tipos)
    coef_order: float  # variação prevista por registro (s)
    change_pct: float  # variação prevista por registro, em % do último tempo
    status: TrendStatus | None  # None com menos de MIN_TREND_RECORDS registros (AQ-29)
    mae_s: float  # erro médio do modelo no teste (s)


class DashboardRead(BaseModel):
    active_athletes: int
    sessions_total: int
    sessions_last_30_days: int
    athletes_without_recent_sessions: int
    recent_sessions: list[SessionListItem]
    athletes: list[DashboardAthlete]
    predictions: list[DashboardPrediction]  # atleta × prova com previsão; Atenção primeiro
    min_trend_records: int  # registros na prova para exibir o selo
    athletes_without_prediction: int  # atletas ativos sem prova com o mínimo de registros