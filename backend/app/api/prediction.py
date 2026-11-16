from dataclasses import fields
from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession, OwnedAthlete
from app.models import TrainingSession
from app.models.training_session import SessionType, Stroke
from app.schemas.prediction import (
    HistoryPoint,
    LastSessionRead,
    MetricSeriesRead,
    PathPointRead,
    PredictionEvaluationRead,
    PredictionModelRead,
    PredictionRead,
    PredictionTestPoint,
)
from app.schemas.session import SessionRead
from app.services.metrics import Metrics
from app.services.prediction import (
    MIN_RECORDS,
    FittedModel,
    InsufficientDataError,
    PathPoint,
    Record,
    predict_next,
    project_series,
)

METRIC_KEYS = [f.name for f in fields(Metrics)]  # vm, vn, cb, cn, swim_index, swolf, swolf_25

router = APIRouter(prefix="/athletes/{athlete_id}/prediction", tags=["Predição"])


def _r(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def mean_interval_days(dates: list[date]) -> int | None:
    """Intervalo médio, em dias, entre o primeiro e o último registro (mínimo de 1 dia)."""
    if len(dates) < 2:
        return None
    span = (dates[-1] - dates[0]).days
    return max(1, round(span / (len(dates) - 1)))


def _path_read(
    path: list[PathPoint], dates: list[date], interval: int | None, digits: int
) -> list[PathPointRead]:
    """Converte a reta do serviço, com a data real (histórico) ou estimada (futuro)."""
    n = len(dates)
    result = []
    for point in path:
        future = point.order > n
        if future:
            session_date = (
                dates[-1] + timedelta(days=interval * (point.order - n)) if interval else None
            )
        else:
            session_date = dates[point.order - 1]
        result.append(
            PathPointRead(
                order=point.order,
                session_date=session_date,
                estimated=future,
                training_s=_r(point.training_s, digits),
                competition_s=_r(point.competition_s, digits),
            )
        )
    return result


def _model_read(model: FittedModel) -> PredictionModelRead:
    return PredictionModelRead(
        intercept=round(model.intercept, 3),
        coef_order=round(model.coef_order, 3),
        coef_competition=_r(model.coef_competition, 3),
        r2=_r(model.r2),
        n=model.n,
    )


def metric_series(
    sessions: list[TrainingSession], dates: list[date], interval: int | None
) -> dict[str, MetricSeriesRead]:
    """Ajusta a reta em cada métrica calculada da prova e projeta os próximos registros."""
    computed = [SessionRead.model_validate(s).metrics.model_dump() for s in sessions]
    flags = [s.session_type == SessionType.COMPETITION for s in sessions]
    series = {}
    for key in METRIC_KEYS:
        values = [m[key] for m in computed]
        orders = [i + 1 for i, v in enumerate(values) if v is not None]
        records = [Record(value=values[o - 1], is_competition=flags[o - 1]) for o in orders]
        try:
            projection = project_series(records, orders, last_order=len(sessions))
        except InsufficientDataError:
            series[key] = MetricSeriesRead(
                available=False, n_records=len(records), values=values, model=None, path=[]
            )
            continue
        series[key] = MetricSeriesRead(
            available=True,
            n_records=len(records),
            values=values,
            model=_model_read(projection.model),
            path=_path_read(projection.path, dates, interval, digits=3),
        )
    return series


@router.get("", response_model=PredictionRead)
def get_prediction(
    athlete: OwnedAthlete,
    db: DbSession,
    stroke: Stroke,
    distance_m: int,
    pool_length_m: int,
):
    """Prevê o tempo dos próximos registros de uma prova do atleta (Regressão Linear).

    Usa todo o histórico da prova (mesmo nado, distância e piscina), em ordem
    cronológica, e devolve também a avaliação do modelo (divisão temporal
    treino/teste), a reta ajustada no histórico e a projeção para os registros
    seguintes, com datas estimadas pelo intervalo médio entre os registros.
    As métricas calculadas recebem a mesma reta e projeção (metric_series).
    """
    sessions = db.scalars(
        select(TrainingSession)
        .where(
            TrainingSession.athlete_id == athlete.id,
            TrainingSession.stroke == stroke,
            TrainingSession.distance_m == distance_m,
            TrainingSession.pool_length_m == pool_length_m,
        )
        .order_by(TrainingSession.session_date, TrainingSession.id)
    ).all()

    dates = [s.session_date for s in sessions]
    interval = mean_interval_days(dates)

    base = dict(
        athlete_id=athlete.id,
        stroke=stroke,
        distance_m=distance_m,
        pool_length_m=pool_length_m,
        n_records=len(sessions),
        min_records=MIN_RECORDS,
        last_session=(
            LastSessionRead(
                session_id=sessions[-1].id,
                session_date=sessions[-1].session_date,
                session_type=sessions[-1].session_type,
                total_time_s=float(sessions[-1].total_time_s),
            )
            if sessions
            else None
        ),
        history=[
            HistoryPoint(
                order=i + 1,
                session_id=s.id,
                session_date=s.session_date,
                session_type=s.session_type,
                time_s=float(s.total_time_s),
            )
            for i, s in enumerate(sessions)
        ],
        interval_days=interval,
        metric_series=metric_series(sessions, dates, interval),
    )

    records = [
        Record(
            value=float(s.total_time_s),
            is_competition=s.session_type == SessionType.COMPETITION,
        )
        for s in sessions
    ]

    try:
        result = predict_next(records)
    except InsufficientDataError:
        return PredictionRead(
            **base,
            available=False,
            message=(
                f"São necessários pelo menos {MIN_RECORDS} registros desta prova "
                f"para gerar a previsão; há {len(sessions)}."
            ),
            next_order=None,
            training_s=None,
            competition_s=None,
            model=None,
            evaluation=None,
            path=[],
        )

    ev = result.evaluation
    points = [
        PredictionTestPoint(
            order=p.order,
            session_id=sessions[p.order - 1].id,
            session_date=sessions[p.order - 1].session_date,
            is_competition=p.is_competition,
            actual_s=round(p.actual_s, 2),
            predicted_s=round(p.predicted_s, 2),
            error_s=round(p.predicted_s - p.actual_s, 2),
        )
        for p in ev.points
    ]

    return PredictionRead(
        **base,
        available=True,
        message=None,
        next_order=result.next_order,
        training_s=_r(result.training_s),
        competition_s=_r(result.competition_s),
        model=_model_read(result.model),
        evaluation=PredictionEvaluationRead(
            n_train=ev.n_train,
            n_test=ev.n_test,
            mae_s=round(ev.mae_s, 2),
            mape_pct=round(ev.mape_pct, 2),
            rmse_s=round(ev.rmse_s, 2),
            points=points,
        ),
        path=_path_read(result.path, dates, interval, digits=2),
    )