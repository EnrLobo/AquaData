"""Carga de atletas e treinos simulados no banco (AQ-21).

Cria um atleta por cenário de services/simulation.py (nome começando com
"Simulado"), todos na prova de 100 m livre em piscina de 25 m, para ver o
modelo de predição nas telas (Início e Desempenho) e demonstrar à banca.

Use só no banco local: os dados são fictícios.

Uso (na pasta backend, com o venv ativo e o .env do banco local):
    python -m scripts.seed_simulated --email seu@email.com
    python -m scripts.seed_simulated --email seu@email.com --reset
"""

import argparse
import sys
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import Athlete, Coach, SessionType, Sex, Stroke, TrainingSession
from app.services.simulation import SCENARIOS, simulate_series

PREFIX = "Simulado"
DISTANCE_M = 100
POOL_M = 25
DAYS_BETWEEN = 3  # um registro a cada 3 dias, terminando ontem
SWIM_SPEED_RATIO = 0.97  # VN um pouco abaixo da Vm (sem o impulso da saída e das viradas)
CYCLE_LENGTH_M = 2.0  # CB típico de crawl usado na simulação (m por ciclo)
TOTAL_CYCLES_RATIO = 0.85  # parte da prova completa nadada com braçadas (resto: saída e viradas)


def session_fields(time_s: float, rng: np.random.Generator) -> dict:
    """Campos de medição coerentes com o tempo simulado (passam nas validações da API)."""
    laps = DISTANCE_M // POOL_M
    swim_distance = (POOL_M - 10) * laps  # trecho entre as bandeirolas (padrão da equipe)
    swim_speed = DISTANCE_M / time_s * SWIM_SPEED_RATIO
    swim_time = swim_distance / swim_speed
    cycle_length = CYCLE_LENGTH_M * (1 + rng.normal(0, 0.03))
    cycles = max(1, round(swim_distance / cycle_length))
    total_cycles = max(cycles, round(cycles * DISTANCE_M / swim_distance * TOTAL_CYCLES_RATIO))
    return {
        "total_time_s": Decimal(f"{time_s:.2f}"),
        "swim_distance_m": Decimal(swim_distance),
        "swim_time_s": Decimal(f"{swim_time:.2f}"),
        "stroke_count": cycles,
        "total_cycle_count": total_cycles,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga de atletas simulados no banco local")
    parser.add_argument("--email", required=True, help="e-mail do treinador que recebe os atletas")
    parser.add_argument("--seed", type=int, default=2026, help="semente (dados reproduzíveis)")
    parser.add_argument(
        "--reset", action="store_true", help="apaga os atletas simulados antes de criar de novo"
    )
    args = parser.parse_args()

    print(f"Banco: {engine.url.render_as_string(hide_password=True)}")
    rng = np.random.default_rng(args.seed)

    with SessionLocal() as db:
        coach = db.scalar(select(Coach).where(Coach.email == args.email.strip().lower()))
        if coach is None:
            sys.exit(f"Treinador não encontrado: {args.email}")

        existing = db.scalars(
            select(Athlete).where(Athlete.coach_id == coach.id, Athlete.name.startswith(PREFIX))
        ).all()
        if existing and not args.reset:
            sys.exit(
                f"Já existem {len(existing)} atletas simulados. Use --reset para recriá-los."
            )
        for athlete in existing:
            db.delete(athlete)  # apaga também os treinos (cascade)
        db.flush()

        yesterday = date.today() - timedelta(days=1)
        for index, scenario in enumerate(SCENARIOS):
            athlete = Athlete(
                coach_id=coach.id,
                name=f"{PREFIX} {scenario.label}",
                birth_date=date(2008, 1, 1) + timedelta(days=97 * index),
                sex=Sex.FEMALE if index % 2 else Sex.MALE,
                active=True,
            )
            db.add(athlete)
            series = simulate_series(scenario, rng)
            n = len(series.records)
            for order, record in enumerate(series.records, start=1):
                athlete.sessions.append(
                    TrainingSession(
                        session_date=yesterday - timedelta(days=DAYS_BETWEEN * (n - order)),
                        session_type=(
                            SessionType.COMPETITION if record.is_competition else SessionType.TRAINING
                        ),
                        stroke=Stroke.FREESTYLE,
                        pool_length_m=POOL_M,
                        distance_m=DISTANCE_M,
                        notes=f"Dado simulado (AQ-21): cenário {scenario.key}",
                        **session_fields(record.value, rng),
                    )
                )
            print(f"  {athlete.name}: {n} registros")

        db.commit()
    print("Pronto. Abra o Início e o Desempenho para ver as previsões.")


if __name__ == "__main__":
    main()