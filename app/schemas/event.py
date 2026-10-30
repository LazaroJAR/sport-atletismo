import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator
from app.schemas.literals import EventStatus, RoundType


# ---------- Eventos ----------
class EventCreate(BaseModel):
    suite_event_id: uuid.UUID
    discipline_id: uuid.UUID
    age_category_id: uuid.UUID | None = None
    regulation_id: uuid.UUID
    name: str = Field(max_length=200)
    round: RoundType = "final"
    scheduled_at: datetime

    wind_ms: float | None = Field(default=None, ge=-99.99, le=99.99)
    wind_direction: str | None = Field(default=None, max_length=8)
    is_wind_legal: bool | None = None
    temperature_c: float | None = Field(default=None, ge=-30, le=60)
    humidity_pct: int | None = Field(default=None, ge=0, le=100)
    track_condition: str | None = Field(default=None, max_length=24)
    notes: str | None = None


class EventRead(BaseModel):
    id: uuid.UUID
    suite_event_id: uuid.UUID
    discipline_id: uuid.UUID
    age_category_id: uuid.UUID | None
    regulation_id: uuid.UUID
    name: str
    round: str
    scheduled_at: datetime
    status: str
    wind_ms: float | None
    wind_direction: str | None
    is_wind_legal: bool | None
    temperature_c: float | None
    humidity_pct: int | None
    track_condition: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class EventStatusUpdate(BaseModel):
    status: EventStatus


class EventConditionsUpdate(BaseModel):
    wind_ms: float | None = Field(default=None, ge=-99.99, le=99.99)
    wind_direction: str | None = None
    is_wind_legal: bool | None = None
    temperature_c: float | None = None
    humidity_pct: int | None = Field(default=None, ge=0, le=100)
    track_condition: str | None = None