from datetime import date

from pydantic import BaseModel

from app.models.training_session import SessionType, Stroke


class PredictionModelRead(BaseModel):
    """Coeficientes da reta tempo = b0 + b1·ordem + b2·competição (todo o histórico)."""

    intercept: float  # b0
    coef_order: float  # b1: variação do tempo a cada novo registro (s)
    coef_competition: float | None  # b2: competição − treino (s); None sem os dois tipos
    r2: float | None
    n: int


class PredictionTestPoint(BaseModel):
    order: int
    session_id: int
    session_date: date
    is_competition: bool
    actual_s: float
    predicted_s: float
    error_s: float  # previsto − real


class PredictionEvaluationRead(BaseModel):
    n_train: int
    n_test: int
    mae_s: float
    mape_pct: float
    rmse_s: float
    points: list[PredictionTestPoint]


class HistoryPoint(BaseModel):
    """Registro real da prova, na ordem usada pelo modelo."""

    order: int
    session_id: int
    session_date: date
    session_type: SessionType
    time_s: float


class PathPointRead(BaseModel):
    """Reta do modelo numa ordem do histórico (com a data real) ou futura (sem data)."""

    order: int
    session_date: date | None  # data real no histórico; None nos registros futuros
    estimated: bool  # True nos registros futuros
    training_s: float | None
    competition_s: float | None


class MetricSeriesRead(BaseModel):
    """Série de uma métrica na prova, com a reta do modelo e a projeção futura."""

    available: bool  # False com menos de min_records registros com valor
    n_records: int  # registros da prova em que a métrica existe
    values: list[float | None]  # valor real, alinhado com history (None quando falta)
    model: PredictionModelRead | None
    path: list[PathPointRead]  # vazio quando não há projeção


class LastSessionRead(BaseModel):
    session_id: int
    session_date: date
    session_type: SessionType
    total_time_s: float


class PredictionRead(BaseModel):
    athlete_id: int
    stroke: Stroke
    distance_m: int
    pool_length_m: int
    n_records: int  # registros da prova no histórico
    min_records: int  # mínimo para haver predição
    available: bool  # False quando o histórico é curto demais
    message: str | None  # motivo quando não há predição
    last_session: LastSessionRead | None
    next_order: int | None
    training_s: float | None  # tempo previsto se o próximo registro for treino
    competition_s: float | None  # tempo previsto se for competição
    model: PredictionModelRead | None
    evaluation: PredictionEvaluationRead | None
    history: list[HistoryPoint]  # todos os registros da prova (também sem predição)
    path: list[PathPointRead]  # reta no histórico + projeção futura (vazio sem predição)
    metric_series: dict[str, MetricSeriesRead]  # vm, vn, cb, cn, swim_index, swolf, swolf_25