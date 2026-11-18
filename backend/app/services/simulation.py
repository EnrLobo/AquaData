"""Séries simuladas de tempos para testar o modelo de predição (AQ-21).

Cada cenário define um comportamento "verdadeiro" do atleta (melhora, piora,
platô...) e um ruído aleatório que imita a variação natural entre registros.
Como o comportamento verdadeiro é conhecido, dá para medir se o modelo de
predição (services/prediction.py) recupera a tendência, acerta o selo e com
que erro prevê o próximo registro, antes de usá-lo com dados reais.

Ruído (variação típica de um mesmo atleta entre provas, em % do tempo):
- 1,4%: nadadores de nível nacional e juniores (Stewart; Hopkins, 2000)
- 0,8%: nadadores de elite (Trewin; Hopkins; Pyne, 2004; coerente com Pyne;
  Trewin; Hopkins, 2004, que tratam 0,4% como metade da variação entre provas)

Os demais valores (tendência por registro, efeito competição, registro
atípico, platô) são escolhas da equipe para os cenários, não dados de fonte.

Estudo do número de registros (AQ-29): roda os cenários lineares com 6 a 20
registros e compara três regras para o selo de tendência (só a inclinação;
inclinação + R² mínimo; inclinação + teste estatístico da inclinação), para
definir quantos registros o selo precisa para ser confiável.
"""

import math
from dataclasses import dataclass, field, replace
from enum import StrEnum

import numpy as np
from scipy import stats

from app.services.prediction import (
    InsufficientDataError,
    Record,
    TrendStatus,
    classify_trend,
    predict_next,
)

NOISE_CV_NATIONAL = 1.4  # % (Stewart; Hopkins, 2000)
NOISE_CV_ELITE = 0.8  # % (Trewin; Hopkins; Pyne, 2004)
BASE_TIME_S = 60.0  # tempo inicial padrão (ex.: 100 m livre)
COMPETITION_EFFECT_PCT = -1.5  # competição 1,5% mais rápida que treino (valor ilustrativo)


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    trend_pct: float = 0.0  # variação verdadeira por registro, em % do tempo inicial
    expected: TrendStatus | None = None  # selo correto (None quando não há um só correto)
    noise_cv_pct: float = NOISE_CV_NATIONAL
    n_records: int = 12
    competition_every: int = 0  # a cada k registros, um é competição (0 = só treinos)
    competition_pct: float = COMPETITION_EFFECT_PCT
    outlier_at: int | None = None  # ordem do registro atípico (1 = primeiro)
    outlier_pct: float = 0.0  # quanto o registro atípico fica acima do esperado (%)
    plateau_pct: float = 0.0  # melhora total que se aproxima de um platô (%)
    plateau_tau: float = 3.0  # quão rápido chega ao platô (em registros)


SCENARIOS: list[Scenario] = [
    Scenario("melhora", "Melhora linear", trend_pct=-0.3, expected=TrendStatus.IMPROVING),
    Scenario("estavel", "Estável", trend_pct=0.0, expected=TrendStatus.STABLE),
    Scenario("piora", "Piora linear", trend_pct=0.3, expected=TrendStatus.ATTENTION),
    Scenario(
        "melhora_elite",
        "Melhora linear, ruído de elite",
        trend_pct=-0.3,
        expected=TrendStatus.IMPROVING,
        noise_cv_pct=NOISE_CV_ELITE,
    ),
    Scenario(
        "competicao",
        "Melhora com competições",
        trend_pct=-0.3,
        expected=TrendStatus.IMPROVING,
        competition_every=4,
    ),
    Scenario(
        "atipico",
        "Melhora com um registro atípico",
        trend_pct=-0.3,
        expected=TrendStatus.IMPROVING,
        outlier_at=6,
        outlier_pct=5.0,
    ),
    Scenario(
        "poucos",
        "Melhora com só 6 registros",
        trend_pct=-0.3,
        expected=TrendStatus.IMPROVING,
        n_records=6,
    ),
    Scenario("plato", "Melhora que desacelera (platô)", plateau_pct=4.0),
]

SCENARIOS_BY_KEY = {s.key: s for s in SCENARIOS}


def is_competition(scenario: Scenario, order: int) -> bool:
    return scenario.competition_every > 0 and order % scenario.competition_every == 0


def true_time(scenario: Scenario, order: int, base_s: float = BASE_TIME_S) -> float:
    """Tempo esperado (sem ruído) do registro de ordem `order` no cenário."""
    if scenario.plateau_pct:
        # melhora rápida no início que vai parando: base · (1 − P · (1 − e^(−(ordem−1)/τ)))
        gain = scenario.plateau_pct / 100 * (1 - math.exp(-(order - 1) / scenario.plateau_tau))
        value = base_s * (1 - gain)
    else:
        value = base_s * (1 + scenario.trend_pct / 100 * (order - 1))
    if is_competition(scenario, order):
        value *= 1 + scenario.competition_pct / 100
    return value


@dataclass(frozen=True)
class SimulatedSeries:
    records: list[Record]  # tempos com ruído, em ordem cronológica
    true_times: list[float]  # tempos esperados (sem ruído) dos mesmos registros
    true_next_training_s: float  # tempo esperado do próximo registro como treino


def simulate_series(
    scenario: Scenario,
    rng: np.random.Generator,
    base_s: float = BASE_TIME_S,
    noise: bool = True,
) -> SimulatedSeries:
    """Gera uma série do cenário. Ruído multiplicativo: tempo · (1 + ε), ε ~ N(0, CV)."""
    records, truths = [], []
    for order in range(1, scenario.n_records + 1):
        expected = true_time(scenario, order, base_s)
        value = expected
        if noise:
            value *= 1 + rng.normal(0, scenario.noise_cv_pct / 100)
        if order == scenario.outlier_at:
            value *= 1 + scenario.outlier_pct / 100
        records.append(Record(value=round(value, 2), is_competition=is_competition(scenario, order)))
        truths.append(expected)

    next_order = scenario.n_records + 1
    next_training = true_time(scenario, next_order, base_s)
    if is_competition(scenario, next_order):  # o "próximo treino" nunca é competição
        next_training /= 1 + scenario.competition_pct / 100
    return SimulatedSeries(records=records, true_times=truths, true_next_training_s=next_training)


def true_slope_s(scenario: Scenario, base_s: float = BASE_TIME_S) -> float | None:
    """Inclinação verdadeira (s por registro) nos cenários lineares; None no platô."""
    if scenario.plateau_pct:
        return None
    return base_s * scenario.trend_pct / 100


@dataclass
class StudyResult:
    scenario: Scenario
    n_series: int
    mae_s: list[float] = field(default_factory=list)  # erro no teste (como no sistema)
    mape_pct: list[float] = field(default_factory=list)
    next_error_s: list[float] = field(default_factory=list)  # previsto − esperado, próximo treino
    slope_s: list[float] = field(default_factory=list)  # b1 estimado
    competition_s: list[float] = field(default_factory=list)  # b2 estimado
    statuses: list[TrendStatus] = field(default_factory=list)
    skipped: int = 0  # séries sem previsão (ex.: previsão ≤ 0)

    @staticmethod
    def _mean(values: list[float]) -> float | None:
        return float(np.mean(values)) if values else None

    @property
    def mean_mae_s(self) -> float | None:
        return self._mean(self.mae_s)

    @property
    def mean_mape_pct(self) -> float | None:
        return self._mean(self.mape_pct)

    @property
    def next_bias_s(self) -> float | None:
        """Viés da previsão do próximo treino: negativo = otimista (tempo previsto menor)."""
        return self._mean(self.next_error_s)

    @property
    def next_mae_s(self) -> float | None:
        return self._mean([abs(e) for e in self.next_error_s])

    @property
    def mean_slope_s(self) -> float | None:
        return self._mean(self.slope_s)

    @property
    def slope_sd_s(self) -> float | None:
        return float(np.std(self.slope_s, ddof=1)) if len(self.slope_s) > 1 else None

    @property
    def mean_competition_s(self) -> float | None:
        return self._mean(self.competition_s)

    def status_share(self, status: TrendStatus) -> float:
        """Fração das séries que recebeu o selo `status` (0 a 1)."""
        return self.statuses.count(status) / len(self.statuses) if self.statuses else 0.0

    @property
    def status_accuracy(self) -> float | None:
        """Fração de selos corretos; None quando o cenário não tem selo correto definido."""
        if self.scenario.expected is None:
            return None
        return self.status_share(self.scenario.expected)


def run_study(
    scenario: Scenario,
    n_series: int,
    seed: int,
    base_s: float = BASE_TIME_S,
    noise: bool = True,
) -> StudyResult:
    """Simula `n_series` séries do cenário e aplica o modelo do sistema em cada uma."""
    rng = np.random.default_rng(seed)
    result = StudyResult(scenario=scenario, n_series=n_series)
    for _ in range(n_series):
        series = simulate_series(scenario, rng, base_s, noise)
        try:
            prediction = predict_next(series.records)
        except InsufficientDataError:
            result.skipped += 1
            continue
        if prediction.training_s is None:
            result.skipped += 1
            continue
        result.mae_s.append(prediction.evaluation.mae_s)
        result.mape_pct.append(prediction.evaluation.mape_pct)
        result.next_error_s.append(prediction.training_s - series.true_next_training_s)
        result.slope_s.append(prediction.model.coef_order)
        if prediction.model.coef_competition is not None:
            result.competition_s.append(prediction.model.coef_competition)
        _, status = classify_trend(prediction.model.coef_order, series.records[-1].value)
        result.statuses.append(status)
    return result


# ---------------------------------------------------------------------------
# Estudo do número de registros e das regras do selo (AQ-29)
# ---------------------------------------------------------------------------

RECORD_COUNTS = (6, 8, 10, 12, 15, 20)  # números de registros comparados
RECORD_COUNT_SCENARIOS = ("melhora", "estavel", "piora", "melhora_elite")
R2_MIN = 0.3  # regra 2: abaixo deste R², o selo vira "Estável" (valor em estudo, sem fonte)
SLOPE_TEST_CONFIDENCE = 0.95  # regra 3: nível de confiança do teste da inclinação


class TrendRule(StrEnum):
    """Regras comparadas para o selo de tendência."""

    SLOPE = "inclinacao"  # regra atual do sistema: só a inclinação (faixa de ±0,2%)
    SLOPE_R2 = "inclinacao_r2"  # inclinação + R² ≥ R2_MIN
    SLOPE_TEST = "inclinacao_teste"  # inclinação + inclinação diferente de zero (teste t)


TREND_RULE_LABELS = {
    TrendRule.SLOPE: "Só inclinação",
    TrendRule.SLOPE_R2: f"Inclinação + R² ≥ {R2_MIN:g}".replace(".", ","),
    TrendRule.SLOPE_TEST: "Inclinação + teste",
}


def with_record_count(scenario: Scenario, n_records: int) -> Scenario:
    """Mesmo cenário, com outro número de registros."""
    return replace(scenario, n_records=n_records)


def slope_standard_error(records: list[Record]) -> float | None:
    """Erro padrão da inclinação (b1) na regressão do sistema (mínimos quadrados).

    Usa as mesmas variáveis do modelo: ordem (1, 2, 3...) e, quando há treinos e
    competições, a variável competição. Devolve None quando não sobram graus de
    liberdade para estimar o erro (registros ≤ número de coeficientes).
    """
    n = len(records)
    flags = [1.0 if r.is_competition else 0.0 for r in records]
    columns = [np.ones(n), np.arange(1, n + 1, dtype=float)]
    if len(set(flags)) == 2:
        columns.append(np.array(flags))
    x = np.column_stack(columns)
    y = np.array([r.value for r in records], dtype=float)
    dof = n - x.shape[1]
    if dof <= 0:
        return None
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    residuals = y - x @ coef
    variance = float(residuals @ residuals) / dof
    cov = variance * np.linalg.inv(x.T @ x)
    return float(math.sqrt(max(cov[1, 1], 0.0)))


def slope_is_significant(
    coef_order: float,
    standard_error: float | None,
    dof: int,
    confidence: float = SLOPE_TEST_CONFIDENCE,
) -> bool:
    """Teste t bilateral: a inclinação é diferente de zero no nível de confiança dado?

    Equivale a dizer que o intervalo de confiança da inclinação não contém o zero.
    """
    if standard_error is None or dof <= 0:
        return False
    if standard_error == 0:
        return coef_order != 0  # reta perfeita: qualquer inclinação é exata
    t_value = abs(coef_order) / standard_error
    t_critical = float(stats.t.ppf(1 - (1 - confidence) / 2, dof))
    return t_value >= t_critical


def apply_rule(
    rule: TrendRule,
    status: TrendStatus,
    r2: float | None,
    significant: bool,
) -> TrendStatus:
    """Aplica a regra ao selo da regra atual.

    As regras 2 e 3 só podem trocar "Melhorando"/"Atenção" por "Estável"
    (nunca o contrário): elas pedem mais evidência antes de indicar mudança.
    """
    if rule is TrendRule.SLOPE or status is TrendStatus.STABLE:
        return status
    if rule is TrendRule.SLOPE_R2:
        return status if r2 is not None and r2 >= R2_MIN else TrendStatus.STABLE
    return status if significant else TrendStatus.STABLE


@dataclass
class RecordCountResult(StudyResult):
    """Resultado de um cenário com um número de registros, com o selo de cada regra."""

    statuses_by_rule: dict[TrendRule, list[TrendStatus]] = field(
        default_factory=lambda: {rule: [] for rule in TrendRule}
    )

    def rule_accuracy(self, rule: TrendRule) -> float | None:
        """Fração de selos corretos na regra; None se o cenário não tem selo correto."""
        statuses = self.statuses_by_rule[rule]
        if self.scenario.expected is None or not statuses:
            return None
        return statuses.count(self.scenario.expected) / len(statuses)

    def rule_serious_error(self, rule: TrendRule) -> float | None:
        """Fração de erros graves (melhora vista como Atenção ou o contrário).

        None no cenário estável, em que não há um sentido oposto.
        """
        opposite = {
            TrendStatus.IMPROVING: TrendStatus.ATTENTION,
            TrendStatus.ATTENTION: TrendStatus.IMPROVING,
        }.get(self.scenario.expected)
        statuses = self.statuses_by_rule[rule]
        if opposite is None or not statuses:
            return None
        return statuses.count(opposite) / len(statuses)


def run_record_count_study(
    scenario: Scenario,
    n_records: int,
    n_series: int,
    seed: int,
    base_s: float = BASE_TIME_S,
) -> RecordCountResult:
    """Simula o cenário com `n_records` registros e classifica cada série pelas três regras."""
    scenario = with_record_count(scenario, n_records)
    rng = np.random.default_rng(seed)
    result = RecordCountResult(scenario=scenario, n_series=n_series)
    for _ in range(n_series):
        series = simulate_series(scenario, rng, base_s)
        try:
            prediction = predict_next(series.records)
        except InsufficientDataError:
            result.skipped += 1
            continue
        if prediction.training_s is None:
            result.skipped += 1
            continue
        model = prediction.model
        result.mae_s.append(prediction.evaluation.mae_s)
        result.mape_pct.append(prediction.evaluation.mape_pct)
        result.next_error_s.append(prediction.training_s - series.true_next_training_s)
        result.slope_s.append(model.coef_order)
        if model.coef_competition is not None:
            result.competition_s.append(model.coef_competition)

        _, status = classify_trend(model.coef_order, series.records[-1].value)
        result.statuses.append(status)
        n_params = 3 if model.coef_competition is not None else 2
        significant = slope_is_significant(
            model.coef_order, slope_standard_error(series.records), len(series.records) - n_params
        )
        for rule in TrendRule:
            result.statuses_by_rule[rule].append(apply_rule(rule, status, model.r2, significant))
    return result