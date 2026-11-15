import math
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)

MIN_TRAIN = 4  # registros mínimos para ajustar o modelo na avaliação
MIN_TEST = 2  # registros mínimos no conjunto de teste
MIN_RECORDS = MIN_TRAIN + MIN_TEST  # 6 registros na prova para haver predição
TEST_FRACTION = 0.2  # últimos 20% vão para o teste


class InsufficientDataError(ValueError):
    """Histórico curto demais para treinar e avaliar o modelo."""


@dataclass(frozen=True)
class Record:
    """Um registro da série da prova, já em ordem cronológica."""

    time_s: float
    is_competition: bool


@dataclass(frozen=True)
class FittedModel:
    intercept: float  # b0: tempo estimado na "ordem 0"
    coef_order: float  # b1: variação do tempo a cada novo registro (s)
    coef_competition: float | None  # b2: diferença competição − treino (s); None sem os dois tipos
    r2: float | None  # ajuste no próprio histórico (None se o tempo não varia)
    n: int  # registros usados no ajuste


@dataclass(frozen=True)
class TestPoint:
    order: int
    is_competition: bool
    actual_s: float
    predicted_s: float


@dataclass(frozen=True)
class Evaluation:
    n_train: int
    n_test: int
    mae_s: float  # erro absoluto médio, em segundos
    mape_pct: float  # erro percentual absoluto médio, em %
    rmse_s: float  # raiz do erro quadrático médio, em segundos
    points: list[TestPoint]  # previsto × real no conjunto de teste


@dataclass(frozen=True)
class Prediction:
    next_order: int  # ordem do próximo registro
    training_s: float | None  # tempo previsto se o próximo registro for treino
    competition_s: float | None  # tempo previsto se for competição (None sem os dois tipos)
    model: FittedModel  # ajustado com todo o histórico
    evaluation: Evaluation  # ajustado só com o conjunto de treino


def split_sizes(n: int) -> tuple[int, int]:
    """Quantos registros vão para treino e teste (divisão temporal)."""
    if n < MIN_RECORDS:
        raise InsufficientDataError(
            f"São necessários pelo menos {MIN_RECORDS} registros da prova; há {n}."
        )
    n_test = max(MIN_TEST, math.ceil(n * TEST_FRACTION))
    return n - n_test, n_test


def _features(orders: list[int], flags: list[bool], use_competition: bool) -> np.ndarray:
    columns = [orders]
    if use_competition:
        columns.append([1.0 if f else 0.0 for f in flags])
    return np.array(columns, dtype=float).T


def _has_both_types(records: list[Record]) -> bool:
    flags = {r.is_competition for r in records}
    return len(flags) == 2


def fit(records: list[Record], first_order: int = 1) -> tuple[LinearRegression, FittedModel]:
    """Ajusta a regressão linear por mínimos quadrados.

    A variável competição só entra quando há treinos e competições no conjunto;
    com um tipo só, ela seria constante e o coeficiente não poderia ser estimado.
    """
    if len(records) < 2:
        raise InsufficientDataError("São necessários pelo menos 2 registros para ajustar a reta.")
    orders = list(range(first_order, first_order + len(records)))
    flags = [r.is_competition for r in records]
    y = np.array([r.time_s for r in records], dtype=float)
    use_competition = _has_both_types(records)

    x = _features(orders, flags, use_competition)
    model = LinearRegression().fit(x, y)

    r2 = None if np.allclose(y, y[0]) else float(r2_score(y, model.predict(x)))
    fitted = FittedModel(
        intercept=float(model.intercept_),
        coef_order=float(model.coef_[0]),
        coef_competition=float(model.coef_[1]) if use_competition else None,
        r2=r2,
        n=len(records),
    )
    return model, fitted


def _predict(model: LinearRegression, fitted: FittedModel, order: int, competition: bool) -> float:
    row = [order, 1.0 if competition else 0.0] if fitted.coef_competition is not None else [order]
    return float(model.predict(np.array([row], dtype=float))[0])


def evaluate(records: list[Record]) -> Evaluation:
    """Treina com os registros mais antigos e mede o erro nos mais recentes."""
    n_train, n_test = split_sizes(len(records))
    train, test = records[:n_train], records[n_train:]
    model, fitted = fit(train)

    points = []
    for i, record in enumerate(test):
        order = n_train + 1 + i
        predicted = _predict(model, fitted, order, record.is_competition)
        points.append(
            TestPoint(
                order=order,
                is_competition=record.is_competition,
                actual_s=record.time_s,
                predicted_s=predicted,
            )
        )

    actual = [p.actual_s for p in points]
    predicted = [p.predicted_s for p in points]
    return Evaluation(
        n_train=n_train,
        n_test=n_test,
        mae_s=float(mean_absolute_error(actual, predicted)),
        mape_pct=float(mean_absolute_percentage_error(actual, predicted) * 100),
        rmse_s=float(root_mean_squared_error(actual, predicted)),
        points=points,
    )


def _positive(value: float) -> float | None:
    # uma reta extrapolada pode, em tese, dar tempo ≤ 0; isso não é previsão válida
    return value if value > 0 else None


def predict_next(records: list[Record]) -> Prediction:
    """Avalia o modelo (treino/teste) e prevê o próximo registro com todo o histórico."""
    evaluation = evaluate(records)
    model, fitted = fit(records)
    next_order = len(records) + 1
    training = _positive(_predict(model, fitted, next_order, competition=False))
    competition = (
        _positive(_predict(model, fitted, next_order, competition=True))
        if fitted.coef_competition is not None
        else None
    )
    return Prediction(
        next_order=next_order,
        training_s=training,
        competition_s=competition,
        model=fitted,
        evaluation=evaluation,
    )