from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.training_session import SessionType, Stroke

MAX_SPEED_M_S = 3.0  # acima disso é erro de digitação (recordes ficam perto de 2,4 m/s)


class SessionCreate(BaseModel):
    session_date: date
    session_type: SessionType
    stroke: Stroke
    pool_length_m: Literal[25, 50]
    distance_m: int = Field(gt=0, le=10000)
    total_time_s: Decimal = Field(gt=0, le=36000, max_digits=8, decimal_places=2)
    stroke_count: int = Field(ge=1, le=5000)
    swim_distance_m: Decimal | None = Field(
        default=None, gt=0, max_digits=6, decimal_places=2
    )
    swim_time_s: Decimal | None = Field(
        default=None, gt=0, max_digits=8, decimal_places=2
    )
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def check_consistency(self):
        if self.session_date > date.today():
            raise ValueError("A data da sessão não pode estar no futuro")
        if self.distance_m % self.pool_length_m != 0:
            raise ValueError("A distância deve ser múltipla do tamanho da piscina")
        if self.distance_m / float(self.total_time_s) > MAX_SPEED_M_S:
            raise ValueError("Tempo incompatível com a distância informada")

        if (self.swim_distance_m is None) != (self.swim_time_s is None):
            raise ValueError(
                "Informe a distância e o tempo do trecho de nado puro juntos"
            )
        if self.swim_distance_m is not None:
            if self.swim_distance_m > self.distance_m:
                raise ValueError("O trecho de nado puro não pode superar a distância total")
            if self.swim_time_s > self.total_time_s:
                raise ValueError("O tempo de nado puro não pode superar o tempo total")
            if float(self.swim_distance_m) / float(self.swim_time_s) > MAX_SPEED_M_S:
                raise ValueError("Tempo de nado puro incompatível com a distância")
        return self


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    session_date: date
    session_type: SessionType
    stroke: Stroke
    pool_length_m: int
    distance_m: int
    total_time_s: float
    stroke_count: int
    swim_distance_m: float | None
    swim_time_s: float | None
    notes: str | None
    created_at: datetime