import math
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

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
FUTURE_STEPS = 3  # registros futuros projetados no gráfico (decisão da equipe)
STABLE_BAND_PCT = 0.2  # |variação prevista por registro| abaixo disso (% do último tempo) = estável
# registros mínimos na prova para exibir o selo de tendência (decisão da equipe, AQ-29):
# com menos, a inclinação varia demais entre séries e o selo erra muito (estudo de simulação)
MIN_TREND_RECORDS = 10


class InsufficientDataError(ValueError):
    """Histórico curto demais para treinar e avaliar o modelo."""


@dataclass(frozen=True)
class Record:
    """Um registro da série da prova, já em ordem cronológica.

    value é o tempo total (s) na predição do tempo, ou o valor da métrica.
    """

    value: float
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
class PathPoint:
    """Valor da reta ajustada (todo o histórico) numa ordem do histórico ou futura."""

    order: int
    training_s: float | None  # reta para treino
    competition_s: float | None  # reta para competição (None sem os dois tipos)


@dataclass(frozen=True)
class Prediction:
    next_order: int  # ordem do próximo registro
    training_s: float | None  # tempo previsto se o próximo registro for treino
    competition_s: float | None  # tempo previsto se for competição (None sem os dois tipos)
    model: FittedModel  # ajustado com todo o histórico
    evaluation: Evaluation  # ajustado só com o conjunto de treino
    path: list[PathPoint]  # reta nas ordens 1..n e nos registros futuros


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


def fit(
    records: list[Record], first_order: int = 1, orders: list[int] | None = None
) -> tuple[LinearRegression, FittedModel]:
    """Ajusta a regressão linear por mínimos quadrados.

    Sem `orders`, os registros recebem ordens consecutivas a partir de
    `first_order`. Com `orders`, cada registro usa a ordem informada (série com
    lacunas, como uma métrica que não existe em todos os registros).

    A variável competição só entra quando há treinos e competições no conjunto;
    com um tipo só, ela seria constante e o coeficiente não poderia ser estimado.
    """
    if len(records) < 2:
        raise InsufficientDataError("São necessários pelo menos 2 registros para ajustar a reta.")
    if orders is None:
        orders = list(range(first_order, first_order + len(records)))
    elif len(orders) != len(records):
        raise ValueError("orders e records precisam ter o mesmo tamanho.")
    flags = [r.is_competition for r in records]
    y = np.array([r.value for r in records], dtype=float)
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
                actual_s=record.value,
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


def _path_point(model: LinearRegression, fitted: FittedModel, order: int) -> PathPoint:
    return PathPoint(
        order=order,
        training_s=_positive(_predict(model, fitted, order, competition=False)),
        competition_s=(
            _positive(_predict(model, fitted, order, competition=True))
            if fitted.coef_competition is not None
            else None
        ),
    )


def predict_next(records: list[Record], steps: int = FUTURE_STEPS) -> Prediction:
    """Avalia o modelo (treino/teste) e prevê com todo o histórico.

    Devolve a previsão do próximo registro e a reta (path) no histórico e nos
    `steps` registros seguintes, para o gráfico.
    """
    evaluation = evaluate(records)
    model, fitted = fit(records)
    n = len(records)
    path = [_path_point(model, fitted, order) for order in range(1, n + steps + 1)]
    following = path[n]  # ordem n + 1
    return Prediction(
        next_order=n + 1,
        training_s=following.training_s,
        competition_s=following.competition_s,
        model=fitted,
        evaluation=evaluation,
        path=path,
    )


@dataclass(frozen=True)
class SeriesProjection:
    model: FittedModel  # ajustado com todos os registros que têm valor
    path: list[PathPoint]  # reta nas ordens 1..last_order e nos registros futuros


def project_series(
    records: list[Record],
    orders: list[int],
    last_order: int,
    steps: int = FUTURE_STEPS,
) -> SeriesProjection:
    """Ajusta a reta numa série (métrica) e projeta os próximos registros.

    - records/orders: só os registros que têm valor, com a ordem de cada um na
      série completa da prova (a métrica pode faltar em alguns registros)
    - last_order: ordem do último registro da prova; a projeção começa depois dele

    Usa o mesmo mínimo de registros da predição do tempo (MIN_RECORDS).
    """
    if len(records) < MIN_RECORDS:
        raise InsufficientDataError(
            f"São necessários pelo menos {MIN_RECORDS} registros com valor; há {len(records)}."
        )
    model, fitted = fit(records, orders=orders)
    path = [_path_point(model, fitted, order) for order in range(1, last_order + steps + 1)]
    return SeriesProjection(model=fitted, path=path)


class TrendStatus(StrEnum):
    """Selo do painel, pela inclinação da reta do tempo (menor tempo = melhor)."""

    IMPROVING = "improving"  # tempo caindo
    STABLE = "stable"  # variação dentro da faixa de estabilidade
    ATTENTION = "attention"  # tempo subindo


def classify_trend(coef_order: float, reference_s: float) -> tuple[float, TrendStatus]:
    """Classifica a tendência do tempo pela variação prevista a cada registro (b1).

    A variação é expressa em % do tempo de referência (o último registro), para
    que provas de durações diferentes usem a mesma faixa de estabilidade.
    Devolve (variação em % por registro, selo).
    """
    if reference_s <= 0:
        raise ValueError("O tempo de referência precisa ser positivo.")
    change_pct = coef_order / reference_s * 100
    if change_pct <= -STABLE_BAND_PCT:
        return change_pct, TrendStatus.IMPROVING
    if change_pct >= STABLE_BAND_PCT:
        return change_pct, TrendStatus.ATTENTION
    return change_pct, TrendStatus.STABLE


def trend_status(
    coef_order: float, reference_s: float, n_records: int
) -> tuple[float, TrendStatus | None]:
    """Selo do painel, só a partir de MIN_TREND_RECORDS registros na prova.

    Abaixo do mínimo, a previsão continua valendo, mas o selo fica vazio (None):
    com poucos registros, a inclinação ainda não indica a tendência com confiança.
    Devolve (variação em % por registro, selo ou None).
    """
    change_pct, status = classify_trend(coef_order, reference_s)
    return change_pct, status if n_records >= MIN_TREND_RECORDS else None


def pick_main_event(events: dict[tuple, tuple[int, date]]) -> tuple | None:
    """Escolhe a prova principal do atleta para o painel.

    events: prova (nado, distância, piscina) → (quantidade de registros, data do último).
    Vale a prova com mais registros entre as que têm o mínimo para a previsão;
    no empate, a de registro mais recente. Sem prova elegível, devolve None.
    """
    eligible = {key: value for key, value in events.items() if value[0] >= MIN_RECORDS}
    if not eligible:
        return None
    return max(eligible, key=lambda key: eligible[key])