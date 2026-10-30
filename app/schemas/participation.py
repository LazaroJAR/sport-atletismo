import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.literals import ParticipationStatus

# ---------- Participaciones ----------
class ParticipationCreate(BaseModel):
    event_id: uuid.UUID
    athlete_id: uuid.UUID
    result_type_id: uuid.UUID
    bib_number: str | None = Field(default=None, max_length=16)
    lane: int | None = Field(default=None, ge=1, le=10)
    starting_position: int | None = Field(default=None, ge=1, le=99)
    result_value: float | None = None
    result_display: str | None = Field(default=None, max_length=32)
    place: int | None = Field(default=None, ge=1, le=999)
    points: int | None = None
    reaction_time_ms: int | None = Field(default=None, ge=0, le=9999)
    is_photo_finish: bool | None = None
    wind_ms: float | None = Field(default=None, ge=-99.99, le=99.99)
    is_wind_legal: bool | None = None
    notes: str | None = None


class ParticipationRead(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    athlete_id: uuid.UUID
    result_type_id: uuid.UUID
    bib_number: str | None
    lane: int | None
    starting_position: int | None
    result_value: float | None
    result_display: str | None
    place: int | None
    points: int | None
    reaction_time_ms: int | None
    is_photo_finish: bool | None
    wind_ms: float | None
    is_wind_legal: bool | None
    is_personal_best: bool
    is_season_best: bool
    is_national_record: bool
    is_world_record: bool
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ParticipationResultUpdate(BaseModel):
    result_value: float | None = None
    result_display: str | None = None
    place: int | None = Field(default=None, ge=1, le=999)
    points: int | None = None
    result_type_id: uuid.UUID | None = None
    status: ParticipationStatus = "valid"
    wind_ms: float | None = None
    is_wind_legal: bool | None = None
    is_personal_best: bool | None = None
    is_season_best: bool | None = None
    is_national_record: bool | None = None
    is_world_record: bool | None = None
    notes: str | None = None