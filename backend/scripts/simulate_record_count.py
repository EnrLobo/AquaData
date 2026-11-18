"""Estudo do número de registros e das regras do selo (AQ-29).

Roda os cenários lineares (melhora, estável, piora e melhora com ruído de
elite) com 6, 8, 10, 12, 15 e 20 registros, aplica o modelo do sistema em cada
série e compara três regras para o selo de tendência:

1. só a inclinação (regra atual do sistema, faixa de ±0,2%)
2. inclinação + R² mínimo (abaixo dele, o selo vira "Estável")
3. inclinação + teste da inclinação (o selo só sai de "Estável" se a
   inclinação for estatisticamente diferente de zero)

Uso (na pasta backend, com o venv ativo):
    python -m scripts.simulate_record_count
    python -m scripts.simulate_record_count --series 1000 --seed 2026 --csv=registros.csv
"""

import argparse
import csv
import time

from app.services.prediction import STABLE_BAND_PCT
from app.services.simulation import (
    BASE_TIME_S,
    R2_MIN,
    RECORD_COUNT_SCENARIOS,
    RECORD_COUNTS,
    SCENARIOS,
    SCENARIOS_BY_KEY,
    SLOPE_TEST_CONFIDENCE,
    TREND_RULE_LABELS,
    TrendRule,
    run_record_count_study,
    true_slope_s,
)

COLUMNS = [
    ("cenario", "Cenário"),
    ("registros", "Registros"),
    ("ruido_pct", "Ruído (%)"),
    ("b1_verdadeiro_s", "b1 verdadeiro (s)"),
    ("b1_medio_s", "b1 médio (s)"),
    ("b1_dp_s", "b1 DP (s)"),
    ("mae_s", "MAE teste (s)"),
    ("erro_proximo_s", "Erro próx. (s)"),
    ("selo_inclinacao_pct", f"Selo correto: {TREND_RULE_LABELS[TrendRule.SLOPE]} (%)"),
    ("selo_r2_pct", f"Selo correto: {TREND_RULE_LABELS[TrendRule.SLOPE_R2]} (%)"),
    ("selo_teste_pct", f"Selo correto: {TREND_RULE_LABELS[TrendRule.SLOPE_TEST]} (%)"),
    ("grave_inclinacao_pct", f"Erro grave: {TREND_RULE_LABELS[TrendRule.SLOPE]} (%)"),
    ("grave_r2_pct", f"Erro grave: {TREND_RULE_LABELS[TrendRule.SLOPE_R2]} (%)"),
    ("grave_teste_pct", f"Erro grave: {TREND_RULE_LABELS[TrendRule.SLOPE_TEST]} (%)"),
]

RULE_KEYS = {
    TrendRule.SLOPE: "inclinacao",
    TrendRule.SLOPE_R2: "r2",
    TrendRule.SLOPE_TEST: "teste",
}


def _round(value, digits):
    return None if value is None else round(value, digits)


def _pct(value):
    return None if value is None else round(value * 100, 1)


def summarize(result) -> dict:
    s = result.scenario
    row = {
        "cenario": s.label,
        "registros": s.n_records,
        "ruido_pct": s.noise_cv_pct,
        "b1_verdadeiro_s": _round(true_slope_s(s), 3),
        "b1_medio_s": _round(result.mean_slope_s, 3),
        "b1_dp_s": _round(result.slope_sd_s, 3),
        "mae_s": _round(result.mean_mae_s, 2),
        "erro_proximo_s": _round(result.next_mae_s, 2),
    }
    for rule, key in RULE_KEYS.items():
        row[f"selo_{key}_pct"] = _pct(result.rule_accuracy(rule))
        row[f"grave_{key}_pct"] = _pct(result.rule_serious_error(rule))
    return row


def _fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if value == 0:
            value = 0.0  # evita "-0" quando o arredondamento dá −0,0
        return f"{value:g}".replace(".", ",")
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Estudo do número de registros e do selo")
    parser.add_argument("--series", type=int, default=1000, help="séries por combinação")
    parser.add_argument("--seed", type=int, default=2026, help="semente (resultado reproduzível)")
    parser.add_argument("--csv", help="caminho de um arquivo CSV para salvar a tabela")
    args = parser.parse_args()

    print(
        f"Simulando {args.series} séries por combinação (semente {args.seed}, "
        f"tempo inicial {BASE_TIME_S:g} s, faixa de estável ±{_fmt(STABLE_BAND_PCT)}%, "
        f"R² mínimo {_fmt(R2_MIN)}, teste com {_fmt(SLOPE_TEST_CONFIDENCE * 100)}% de confiança)...\n"
    )
    rows = []
    for key in RECORD_COUNT_SCENARIOS:
        scenario = SCENARIOS_BY_KEY[key]
        # mesma semente derivada do estudo do AQ-21 para cada cenário
        seed = args.seed + SCENARIOS.index(scenario)
        for n_records in RECORD_COUNTS:
            start = time.perf_counter()
            result = run_record_count_study(scenario, n_records, args.series, seed)
            rows.append(summarize(result))
            print(f"  {scenario.label}, {n_records} registros: {time.perf_counter() - start:.1f} s")

    print()
    print("| " + " | ".join(title for _, title in COLUMNS) + " |")
    print("|" + "---|" * len(COLUMNS))
    for row in rows:
        print("| " + " | ".join(_fmt(row[key]) for key, _ in COLUMNS) + " |")

    print(
        "\nb1 = variação do tempo por registro; Erro próx. = erro absoluto médio da previsão "
        "do próximo treino contra o tempo esperado; Erro grave = melhora vista como Atenção "
        "ou o contrário (— no cenário estável)."
    )

    if args.csv:
        # padrão brasileiro: ";" separa colunas e "," separa decimais (Excel e Planilhas
        # Google em português leem certo); utf-8-sig faz o Excel reconhecer os acentos
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow([title for _, title in COLUMNS])
            for row in rows:
                writer.writerow(["" if row[key] is None else _fmt(row[key]) for key, _ in COLUMNS])
        print(f"\nTabela salva em {args.csv}")


if __name__ == "__main__":
    main()