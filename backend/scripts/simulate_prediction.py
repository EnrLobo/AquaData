"""Estudo de simulação do modelo de predição (AQ-21).

Gera muitas séries simuladas por cenário (services/simulation.py), aplica o
modelo do sistema em cada uma e mostra uma tabela-resumo para a seção de
resultados do TCC.

Uso (na pasta backend, com o venv ativo):
    python -m scripts.simulate_prediction
    python -m scripts.simulate_prediction --series 1000 --seed 2026 --csv simulacao.csv
"""

import argparse
import csv
import time

from app.services.prediction import STABLE_BAND_PCT, TrendStatus
from app.services.simulation import BASE_TIME_S, SCENARIOS, run_study, true_slope_s

COLUMNS = [
    ("cenario", "Cenário"),
    ("registros", "Registros"),
    ("ruido_pct", "Ruído (%)"),
    ("b1_verdadeiro_s", "b1 verdadeiro (s)"),
    ("b1_medio_s", "b1 médio (s)"),
    ("b1_dp_s", "b1 DP (s)"),
    ("b2_medio_s", "b2 médio (s)"),
    ("mae_s", "MAE teste (s)"),
    ("mape_pct", "MAPE teste (%)"),
    ("vies_proximo_s", "Viés próx. (s)"),
    ("erro_proximo_s", "Erro próx. (s)"),
    ("selo_correto_pct", "Selo correto (%)"),
    ("melhorando_pct", "Melhorando (%)"),
    ("estavel_pct", "Estável (%)"),
    ("atencao_pct", "Atenção (%)"),
]


def _round(value, digits):
    return None if value is None else round(value, digits)


def summarize(result) -> dict:
    s = result.scenario
    accuracy = result.status_accuracy
    return {
        "cenario": s.label,
        "registros": s.n_records,
        "ruido_pct": s.noise_cv_pct,
        "b1_verdadeiro_s": _round(true_slope_s(s), 3),
        "b1_medio_s": _round(result.mean_slope_s, 3),
        "b1_dp_s": _round(result.slope_sd_s, 3),
        "b2_medio_s": _round(result.mean_competition_s, 3),
        "mae_s": _round(result.mean_mae_s, 2),
        "mape_pct": _round(result.mean_mape_pct, 2),
        "vies_proximo_s": _round(result.next_bias_s, 2),
        "erro_proximo_s": _round(result.next_mae_s, 2),
        "selo_correto_pct": None if accuracy is None else round(accuracy * 100, 1),
        "melhorando_pct": round(result.status_share(TrendStatus.IMPROVING) * 100, 1),
        "estavel_pct": round(result.status_share(TrendStatus.STABLE) * 100, 1),
        "atencao_pct": round(result.status_share(TrendStatus.ATTENTION) * 100, 1),
    }


def _fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if value == 0:
            value = 0.0  # evita "-0" quando o arredondamento dá −0,0
        return f"{value:g}".replace(".", ",")
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Estudo de simulação do modelo de predição")
    parser.add_argument("--series", type=int, default=1000, help="séries por cenário")
    parser.add_argument("--seed", type=int, default=2026, help="semente (resultado reproduzível)")
    parser.add_argument("--csv", help="caminho de um arquivo CSV para salvar a tabela")
    args = parser.parse_args()

    print(
        f"Simulando {args.series} séries por cenário (semente {args.seed}, "
        f"tempo inicial {BASE_TIME_S:g} s, faixa de estável ±{_fmt(STABLE_BAND_PCT)}%)...\n"
    )
    rows = []
    for index, scenario in enumerate(SCENARIOS):
        start = time.perf_counter()
        # semente diferente por cenário, derivada da principal, para as séries não se repetirem
        result = run_study(scenario, args.series, args.seed + index)
        rows.append(summarize(result))
        print(f"  {scenario.label}: {time.perf_counter() - start:.1f} s")

    print()
    print("| " + " | ".join(title for _, title in COLUMNS) + " |")
    print("|" + "---|" * len(COLUMNS))
    for row in rows:
        print("| " + " | ".join(_fmt(row[key]) for key, _ in COLUMNS) + " |")

    print(
        "\nb1 = variação do tempo por registro; b2 = efeito competição; "
        "Viés próx. = média de (previsto − esperado) no próximo treino "
        "(negativo = otimista); Erro próx. = erro absoluto médio no próximo treino."
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