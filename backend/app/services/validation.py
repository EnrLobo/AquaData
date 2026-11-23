"""Validação das métricas com dados reais do clube parceiro (AQ-25).

Compara as métricas calculadas à mão pelo treinador com as calculadas pelo
sistema (mesmas funções de services/metrics.py) e resume o tempo gasto nos dois
procedimentos (cálculo manual × cadastro no sistema).

A planilha da coleta é um CSV no padrão brasileiro (";" entre colunas, vírgula
decimal), com uma linha por registro; as colunas estão em VALIDATION_COLUMNS e
o protocolo em docs/validacao/README.md. Os dados reais não vão para o Git.
"""

import csv
import io
from dataclasses import dataclass
from statistics import mean, median

from app.services.metrics import Metrics, compute_metrics

# Nado na planilha (português) → valor usado pelo sistema
STROKE_INPUT = {
    "livre": "freestyle",
    "crawl": "freestyle",
    "costas": "backstroke",
    "peito": "breaststroke",
    "borboleta": "butterfly",
    "medley": "medley",
}

# (campo da classe Metrics, coluna do valor manual na planilha, nome exibido, casas decimais)
# As casas decimais são as mesmas que o sistema exibe (services/metrics.py).
METRICS = [
    ("vm", "vm_manual", "Vm (m/s)", 2),
    ("vn", "vn_manual", "VN (m/s)", 2),
    ("cb", "cb_manual", "CB (m/ciclo)", 2),
    ("cn", "cadencia_manual", "Cadência (ciclos/min)", 1),
    ("swim_index", "in_manual", "IN (m²/s)", 2),
    ("swolf", "swolf_manual", "SWOLF", 1),
    ("swolf_25", "swolf25_manual", "SWOLF 25 m", 1),
]

# Colunas da planilha da coleta, na ordem do modelo (docs/validacao/README.md)
VALIDATION_COLUMNS = [
    "registro",
    "atleta",
    "nado",
    "distancia_m",
    "piscina_m",
    "tempo_total",
    "trecho_m",
    "trecho_s",
    "ciclos_trecho",
    "ciclos_prova",
    *[column for _, column, _, _ in METRICS],
    "tempo_calculo_manual",
    "tempo_cadastro_sistema",
]

REQUIRED_COLUMNS = VALIDATION_COLUMNS[:10]


def tolerance(digits: int) -> float:
    """Diferença aceita: uma unidade na última casa exibida (0,01 ou 0,1).

    Cobre o arredondamento feito em etapas diferentes (ex.: o treinador arredonda
    a VN antes de calcular o IN; o sistema só arredonda no fim).
    """
    return 10 ** -digits


class ValidationInputError(ValueError):
    """Valor da planilha que não pôde ser lido."""


def parse_decimal(text: str | None) -> float | None:
    """Número da planilha: aceita vírgula ou ponto decimal; vazio → None."""
    if text is None or not text.strip():
        return None
    value = text.strip().replace(" ", "")
    if "," in value:
        value = value.replace(".", "").replace(",", ".")  # 1.234,5 → 1234.5
    try:
        return float(value)
    except ValueError as error:
        raise ValidationInputError(f'número inválido: "{text}"') from error


def parse_time(text: str | None) -> float | None:
    """Tempo da planilha em segundos: "1:04,62", "64,62", "64.62" ou "3:20"; vazio → None."""
    if text is None or not text.strip():
        return None
    value = text.strip()
    if ":" in value:
        minutes, _, seconds = value.partition(":")
        try:
            whole_minutes = int(minutes)
        except ValueError as error:
            raise ValidationInputError(f'tempo inválido: "{text}"') from error
        rest = parse_decimal(seconds)
        if rest is None or rest >= 60 or whole_minutes < 0:
            raise ValidationInputError(f'tempo inválido: "{text}"')
        return whole_minutes * 60 + rest
    return parse_decimal(value)


@dataclass(frozen=True)
class ValidationRow:
    """Uma linha da planilha: dados medidos, métricas à mão e tempos cronometrados."""

    label: str
    athlete: str
    stroke: str
    distance_m: float
    pool_length_m: float
    total_time_s: float
    swim_distance_m: float
    swim_time_s: float
    swim_cycles: float
    total_cycles: float | None
    manual: dict[str, float | None]
    manual_seconds: float | None  # tempo gasto calculando à mão
    system_seconds: float | None  # tempo gasto cadastrando no sistema


@dataclass(frozen=True)
class MetricCheck:
    metric: str
    manual: float | None
    system: float | None
    difference: float | None  # manual − sistema
    agrees: bool | None  # None = não comparado (falta um dos valores)


@dataclass(frozen=True)
class RowResult:
    row: ValidationRow
    metrics: Metrics
    checks: list[MetricCheck]

    @property
    def disagreements(self) -> list[MetricCheck]:
        return [check for check in self.checks if check.agrees is False]


@dataclass(frozen=True)
class MetricSummary:
    metric: str
    title: str
    compared: int
    agreed: int
    max_abs_difference: float | None
    mean_abs_difference: float | None

    @property
    def agreement_pct(self) -> float | None:
        return None if not self.compared else self.agreed / self.compared * 100


@dataclass(frozen=True)
class TimingSummary:
    n: int  # registros com os dois tempos cronometrados
    mean_manual_s: float | None
    mean_system_s: float | None
    median_manual_s: float | None
    median_system_s: float | None

    @property
    def speedup(self) -> float | None:
        """Quantas vezes o cadastro no sistema é mais rápido que o cálculo à mão (médias)."""
        if not self.mean_manual_s or not self.mean_system_s:
            return None
        return self.mean_manual_s / self.mean_system_s


def _required(value: float | None, column: str) -> float:
    if value is None:
        raise ValidationInputError(f'coluna "{column}" vazia')
    return value


def parse_row(raw: dict[str, str]) -> ValidationRow:
    """Converte uma linha da planilha (dict coluna → texto)."""
    stroke_text = (raw.get("nado") or "").strip().lower()
    if stroke_text not in STROKE_INPUT:
        raise ValidationInputError(
            f'nado inválido: "{raw.get("nado")}" (use {", ".join(STROKE_INPUT)})'
        )
    swim_cycles = _required(parse_decimal(raw.get("ciclos_trecho")), "ciclos_trecho")
    swim_time_s = _required(parse_time(raw.get("trecho_s")), "trecho_s")
    if swim_cycles <= 0 or swim_time_s <= 0:
        raise ValidationInputError("ciclos e tempo do trecho precisam ser maiores que zero")
    return ValidationRow(
        label=(raw.get("registro") or "").strip(),
        athlete=(raw.get("atleta") or "").strip(),
        stroke=STROKE_INPUT[stroke_text],
        distance_m=_required(parse_decimal(raw.get("distancia_m")), "distancia_m"),
        pool_length_m=_required(parse_decimal(raw.get("piscina_m")), "piscina_m"),
        total_time_s=_required(parse_time(raw.get("tempo_total")), "tempo_total"),
        swim_distance_m=_required(parse_decimal(raw.get("trecho_m")), "trecho_m"),
        swim_time_s=swim_time_s,
        swim_cycles=swim_cycles,
        total_cycles=parse_decimal(raw.get("ciclos_prova")),
        manual={field: parse_decimal(raw.get(column)) for field, column, _, _ in METRICS},
        manual_seconds=parse_time(raw.get("tempo_calculo_manual")),
        system_seconds=parse_time(raw.get("tempo_cadastro_sistema")),
    )


def read_rows(text: str) -> list[ValidationRow]:
    """Lê a planilha inteira (CSV com ";", com ou sem BOM); erros apontam a linha."""
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), delimiter=";")
    header = [name.strip() for name in reader.fieldnames or []]
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise ValidationInputError(f"colunas ausentes na planilha: {', '.join(missing)}")
    reader.fieldnames = header

    rows = []
    for line, raw in enumerate(reader, start=2):  # linha 1 = cabeçalho
        if not any((value or "").strip() for value in raw.values()):
            continue  # linha em branco
        try:
            rows.append(parse_row(raw))
        except ValidationInputError as error:
            raise ValidationInputError(f"linha {line}: {error}") from error
    return rows


def check_row(row: ValidationRow) -> RowResult:
    """Recalcula as métricas com as funções do sistema e compara com as manuais."""
    metrics = compute_metrics(
        stroke=row.stroke,
        distance_m=row.distance_m,
        total_time_s=row.total_time_s,
        pool_length_m=row.pool_length_m,
        stroke_count=row.swim_cycles,
        swim_distance_m=row.swim_distance_m,
        swim_time_s=row.swim_time_s,
        total_cycle_count=row.total_cycles,
    )
    checks = []
    for field, _, _, digits in METRICS:
        manual = row.manual[field]
        system = getattr(metrics, field)
        if manual is None or system is None:
            checks.append(MetricCheck(field, manual, system, None, None))
            continue
        difference = round(manual - system, digits + 2) + 0.0  # + 0.0 evita "-0"
        # pequena folga para a imprecisão do ponto flutuante (ex.: 1,68 − 1,67)
        agrees = abs(difference) <= tolerance(digits) + 1e-9
        checks.append(MetricCheck(field, manual, system, difference, agrees))
    return RowResult(row, metrics, checks)


def summarize_metrics(results: list[RowResult]) -> list[MetricSummary]:
    """Concordância por métrica, só nos registros em que as duas fontes têm valor."""
    summaries = []
    for index, (field, _, title, _) in enumerate(METRICS):
        checks = [result.checks[index] for result in results]
        compared = [check for check in checks if check.agrees is not None]
        differences = [abs(check.difference) for check in compared]
        summaries.append(
            MetricSummary(
                metric=field,
                title=title,
                compared=len(compared),
                agreed=sum(1 for check in compared if check.agrees),
                max_abs_difference=max(differences) if differences else None,
                mean_abs_difference=mean(differences) if differences else None,
            )
        )
    return summaries


def summarize_timing(rows: list[ValidationRow]) -> TimingSummary:
    """Tempo gasto à mão × no sistema, só nos registros com os dois tempos."""
    pairs = [
        (row.manual_seconds, row.system_seconds)
        for row in rows
        if row.manual_seconds and row.system_seconds
    ]
    if not pairs:
        return TimingSummary(0, None, None, None, None)
    manual = [pair[0] for pair in pairs]
    system = [pair[1] for pair in pairs]
    return TimingSummary(
        n=len(pairs),
        mean_manual_s=mean(manual),
        mean_system_s=mean(system),
        median_manual_s=median(manual),
        median_system_s=median(system),
    )