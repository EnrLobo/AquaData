"""Validação das métricas com dados reais do clube parceiro (AQ-25).

Lê a planilha da coleta (CSV no padrão brasileiro, colunas em
docs/validacao/README.md), recalcula as métricas com as mesmas funções do
sistema, compara com as calculadas à mão e resume o tempo gasto nos dois
procedimentos. Mostra as tabelas para a seção de resultados do TCC.

Uso (na pasta backend, com o venv ativo):
    python -m scripts.validate_metrics --planilha=coleta.csv
    python -m scripts.validate_metrics --planilha=coleta.csv --csv=validacao.csv

A planilha e o resultado têm dados reais de atletas: não vão para o Git
(o .gitignore já ignora *.csv).
"""

import argparse
import csv
import sys
from pathlib import Path

from app.services.report import format_decimal
from app.services.validation import (
    METRICS,
    ValidationInputError,
    check_row,
    read_rows,
    summarize_metrics,
    summarize_timing,
    tolerance,
)


def _num(value: float | None, digits: int) -> str:
    return "—" if value is None else format_decimal(value, digits)


def _seconds(value: float | None) -> str:
    if value is None:
        return "—"
    minutes, seconds = divmod(round(value), 60)
    return f"{minutes}:{seconds:02d} ({format_decimal(value, 1)} s)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validação das métricas (AQ-25)")
    parser.add_argument("--planilha", required=True, help="CSV da coleta (padrão brasileiro)")
    parser.add_argument("--csv", help="caminho de um CSV para salvar a comparação por registro")
    args = parser.parse_args()

    try:
        text = Path(args.planilha).read_text(encoding="utf-8-sig")
        rows = read_rows(text)
    except FileNotFoundError:
        sys.exit(f"Arquivo não encontrado: {args.planilha}")
    except UnicodeDecodeError:
        sys.exit("A planilha precisa estar em UTF-8 (no Excel: Salvar como → CSV UTF-8).")
    except ValidationInputError as error:
        sys.exit(f"Erro na planilha: {error}")
    if not rows:
        sys.exit("A planilha não tem registros.")

    results = [check_row(row) for row in rows]
    athletes = {row.athlete for row in rows if row.athlete}
    print(f"{len(rows)} registros de {len(athletes)} atleta(s).\n")

    print("Concordância entre o cálculo manual e o sistema")
    print("| Métrica | Comparados | Concordam | Concordância (%) | Maior diferença | "
          "Diferença média | Tolerância |")
    print("|---|---|---|---|---|---|---|")
    for summary, (_, _, _, digits) in zip(summarize_metrics(results), METRICS):
        pct = summary.agreement_pct
        print(
            f"| {summary.title} | {summary.compared} | {summary.agreed} | "
            f"{_num(pct, 1)} | {_num(summary.max_abs_difference, digits + 1)} | "
            f"{_num(summary.mean_abs_difference, digits + 1)} | "
            f"±{_num(tolerance(digits), digits)} |"
        )

    divergent = [result for result in results if result.disagreements]
    print(f"\nRegistros com diferença acima da tolerância: {len(divergent)}")
    for result in divergent:
        name = result.row.label or "(sem identificação)"
        details = "; ".join(
            f"{title} manual {_num(check.manual, digits)} × sistema {_num(check.system, digits)}"
            for check, (_, _, title, digits) in zip(result.checks, METRICS)
            if check.agrees is False
        )
        print(f"  - {name}: {details}")

    timing = summarize_timing(rows)
    print("\nTempo gasto por registro")
    if timing.n == 0:
        print("  Nenhum registro com os dois tempos cronometrados.")
    else:
        print(f"  Registros com os dois tempos: {timing.n}")
        print(f"  Cálculo manual: média {_seconds(timing.mean_manual_s)}; "
              f"mediana {_seconds(timing.median_manual_s)}")
        print(f"  Cadastro no sistema: média {_seconds(timing.mean_system_s)}; "
              f"mediana {_seconds(timing.median_system_s)}")
        print(f"  O sistema foi {_num(timing.speedup, 1)} vezes mais rápido (pelas médias).")

    if args.csv:
        header = ["Registro", "Atleta"]
        for _, _, title, _ in METRICS:
            header += [f"{title} manual", f"{title} sistema", f"{title} diferença"]
        header += ["Concorda em tudo", "Tempo manual (s)", "Tempo sistema (s)"]
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(header)
            for result in results:
                line = [result.row.label, result.row.athlete]
                for check, (_, _, _, digits) in zip(result.checks, METRICS):
                    line += [
                        "" if check.manual is None else format_decimal(check.manual, digits),
                        "" if check.system is None else format_decimal(check.system, digits),
                        "" if check.difference is None
                        else format_decimal(check.difference, digits + 1),
                    ]
                line += [
                    "não" if result.disagreements else "sim",
                    "" if result.row.manual_seconds is None
                    else format_decimal(result.row.manual_seconds, 1),
                    "" if result.row.system_seconds is None
                    else format_decimal(result.row.system_seconds, 1),
                ]
                writer.writerow(line)
        print(f"\nComparação por registro salva em {args.csv}")


if __name__ == "__main__":
    main()