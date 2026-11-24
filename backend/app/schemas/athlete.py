from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.athlete import Sex
from app.models.training_session import SessionType, Stroke
from app.services.prediction import TrendStatus


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return value
    value = " ".join(value.split())
    if len(value) < 2:
        raise ValueError("O nome deve ter ao menos 2 caracteres")
    return value


def _check_birth_date(value: date | None) -> date | None:
    if value is None:
        return value
    if value > date.today():
        raise ValueError("A data de nascimento não pode estar no futuro")
    if value.year < 1900:
        raise ValueError("Data de nascimento inválida")
    return value


class AthleteCreate(BaseModel):
    name: str = Field(max_length=120)
    birth_date: date
    sex: Sex

    _clean_name = field_validator("name")(_clean_name)
    _check_birth_date = field_validator("birth_date")(_check_birth_date)


class AthleteUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    birth_date: date | None = None
    sex: Sex | None = None
    active: bool | None = None

    _clean_name = field_validator("name")(_clean_name)
    _check_birth_date = field_validator("birth_date")(_check_birth_date)


class AthleteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    birth_date: date
    sex: Sex
    active: bool
    created_at: datetime


class AthleteLastSession(BaseModel):
    """Registro mais recente do atleta, com as métricas do cartão (AQ-26)."""

    model_config = ConfigDict(from_attributes=True)

    session_date: date
    session_type: SessionType
    stroke: Stroke
    distance_m: int
    pool_length_m: int
    total_time_s: float
    swolf: float | None
    cb: float | None
    vn: float | None


class AthleteMainTrend(BaseModel):
    """Selo de tendência da prova principal, com as regras do painel Início (AQ-26)."""

    model_config = ConfigDict(from_attributes=True)

    stroke: Stroke
    distance_m: int
    pool_length_m: int
    n_records: int
    min_records: int
    status: TrendStatus | None  # None com menos de min_records registros


class AthleteSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sessions_count: int
    last_session: AthleteLastSession | None
    main_trend: AthleteMainTrend | None  # None quando nenhuma prova tem 6 registros


class AthleteListItem(AthleteRead):
    """Atleta na listagem; o resumo só vem com ?summary=true (tela "Meus atletas")."""

    summary: AthleteSummary | None = None