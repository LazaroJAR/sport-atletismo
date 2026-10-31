import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# ---------- SeasonPlan ----------
class SeasonPlanCreate(BaseModel):
    athlete_id: uuid.UUID
    discipline_id: uuid.UUID
    planned_result: float = Field(gt=0)              # RP
    planned_position: int | None = Field(default=None, ge=1, le=999)  # POS P
    notes: str | None = None


class SeasonPlanUpdate(BaseModel):
    planned_result: float | None = Field(default=None, gt=0)
    planned_position: int | None = Field(default=None, ge=1, le=999)
    fundamental_result_points: float | None = None
    notes: str | None = None


class SeasonPlanRead(BaseModel):
    id: uuid.UUID
    athlete_id: uuid.UUID
    discipline_id: uuid.UUID

    # Inputs
    planned_result: float
    planned_position: int | None
    notes: str | None

    # Efectividad
    competitions_in_plan: int | None
    kec: float | None

    # Eficacia
    fundamental_result: float | None
    fundamental_result_points: float | None
    fundamental_position_achieved: int | None
    fundamental_competition_date: date | None
    best_result_date: date | None
    k1: float | None
    k2: float | None
    k3: float | None
    k4: float | None
    ke_cc: float | None


    # Metadatos
    stats_calculated_at: datetime | None
    stats_is_final: bool

    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}



class SeasonPlanEventCreate(BaseModel):
    event_id: uuid.UUID
    is_fundamental: bool = False
    notes: str | None = None


class SeasonPlanEventRead(BaseModel):
    id: uuid.UUID
    season_plan_id: uuid.UUID
    event_id: uuid.UUID
    is_fundamental: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


