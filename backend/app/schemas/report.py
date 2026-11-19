from datetime import date

from pydantic import BaseModel

from app.models.athlete import Sex
from app.models.training_session import SessionType, Stroke
from app.schemas.performance import MetricSummaryRead, PerformanceSummary
from app.services.prediction import TrendStatus


class ReportRecordRead(BaseModel):
    """Um registro de destaque da prova (melhor tempo ou último registro)."""

    session_id: int
    session_date: date
    session_type: SessionType
    time_s: float


class ReportPrediction(BaseModel):
    """Previsão do próximo registro da prova, com todo o histórico (mesmo modelo do AQ-18)."""

    available: bool  # False com menos de min_records registros na prova
    training_s: float | None  # próximo registro como treino
    competition_s: float | None  # próximo registro como competição (None sem os dois tipos)
    coef_order: float | None  # variação prevista por registro (s)
    change_pct: float | None  # variação prevista por registro, em % do último tempo
    status: TrendStatus | None  # selo; None sem previsão ou com menos de min_trend_records
    r2: float | None
    mae_s: float | None  # erro médio do modelo no teste (s)
    mape_pct: float | None


class ReportChartPoint(BaseModel):
    """Ponto do gráfico: registro do período ou registro futuro (só a reta do modelo)."""

    order: int  # ordem no histórico completo da prova
    session_date: date | None  # None nos registros futuros
    session_type: SessionType | None  # None nos registros futuros
    time_s: float | None
    model_training_s: float | None
    model_competition_s: float | None


class ReportEvent(BaseModel):
    """Bloco do relatório para uma prova (nado, distância e piscina)."""

    stroke: Stroke
    distance_m: int
    pool_length_m: int
    n_history: int  # registros da prova em todo o histórico
    n_records: int  # registros da prova no período
    n_trainings: int
    n_competitions: int
    time: MetricSummaryRead  # tempos no período (menor = melhor), com tendência do período
    best: ReportRecordRead  # melhor tempo no período
    last: ReportRecordRead  # registro mais recente no período
    metrics: PerformanceSummary  # métricas no período
    prediction: ReportPrediction  # todo o histórico
    chart: list[ReportChartPoint]  # registros do período + 3 futuros (com previsão)


class ReportTotals(BaseModel):
    records: int
    trainings: int
    competitions: int
    events: int


class ReportRead(BaseModel):
    athlete_id: int
    athlete_name: str
    athlete_active: bool
    birth_date: date
    sex: Sex
    date_from: date | None  # filtro aplicado (None = sem limite)
    date_to: date | None
    first_session_date: date | None  # primeiro registro no período
    last_session_date: date | None  # último registro no período
    totals: ReportTotals
    min_records: int  # registros na prova para haver previsão
    min_trend_records: int  # registros na prova para o selo
    min_conclusive_points: int  # registros no período para a tendência ser conclusiva
    events: list[ReportEvent]  # mais registros no período primeiro