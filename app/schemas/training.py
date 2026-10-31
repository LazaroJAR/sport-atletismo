import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ---------- SeasonTrainingRecord ----------
class SeasonTrainingRecordCreate(BaseModel):
    planned_sessions_count: int | None = Field(default=None, ge=0)   # n SEP
    notes: str | None = None


class SeasonTrainingRecordUpdate(BaseModel):
    planned_sessions_count: int | None = Field(default=None, ge=0)
    notes: str | None = None


class SeasonTrainingRecordRead(BaseModel):
    id: uuid.UUID
    season_plan_id: uuid.UUID
    planned_sessions_count: int | None         # n SEP
    objective_met_sessions_count: int | None   # n SEOC
    ke_p: float | None                         # KE'P
    calculated_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ---------- TrainingSessionLog ----------
class TrainingSessionLogCreate(BaseModel):
    session_date: date
    planned_load_magnitude: int = Field(ge=1, le=5)    # MCP
    effect_load_magnitude: int = Field(ge=1, le=5)     # MEC
    rfc_percentage: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class TrainingSessionLogUpdate(BaseModel):
    session_date: date | None = None
    planned_load_magnitude: int | None = Field(default=None, ge=1, le=5)
    effect_load_magnitude: int | None = Field(default=None, ge=1, le=5)
    rfc_percentage: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class TrainingSessionLogRead(BaseModel):
    id: uuid.UUID
    training_record_id: uuid.UUID
    session_date: date
    planned_load_magnitude: int
    effect_load_magnitude: int
    rfc_percentage: float | None
    objective_met: bool
    notes: str | None
    created_at: datetime
    model_config = {"from_attributes": True}