from pydantic import BaseModel

from app.models.training_session import Stroke
from app.schemas.session import SessionRead


class PerformanceEvent(BaseModel):
    """Combinação de nado, distância e piscina com treinos registrados."""

    stroke: Stroke
    distance_m: int
    pool_length_m: int
    sessions: int


class TrendRead(BaseModel):
    slope: float  # variação estimada por treino
    start: float
    end: float
    first_index: int
    last_index: int
    r2: float | None


class MetricSummaryRead(BaseModel):
    count: int
    first: float
    last: float
    best: float | None
    mean: float
    change: float
    change_pct: float | None
    trend: TrendRead | None
    improved: bool | None


class PerformanceSummary(BaseModel):
    vm: MetricSummaryRead | None
    vn: MetricSummaryRead | None
    cb: MetricSummaryRead | None
    cn: MetricSummaryRead | None
    swim_index: MetricSummaryRead | None
    swolf: MetricSummaryRead | None
    swolf_25: MetricSummaryRead | None


class PerformanceRead(BaseModel):
    athlete_id: int
    athlete_name: str
    athlete_active: bool
    stroke: Stroke | None  # nado aplicado (o informado ou o mais frequente)
    events: list[PerformanceEvent]  # todas as provas do atleta, sem filtro
    sessions: list[SessionRead]  # filtradas, do mais antigo para o mais recente
    total: int  # treinos que atendem aos filtros
    truncated: bool  # True quando há mais treinos que o limite devolvido
    summary: PerformanceSummary