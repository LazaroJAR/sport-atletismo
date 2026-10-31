import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field
from app.schemas.literals import DisciplineCategory, DisciplineSubCategory, ResultTypeCategory, ScopeType, SexType



# ---------- Catálogos ----------
class SuiteEventBase(BaseModel):
    name: str = Field(max_length=200)
    code: str = Field(max_length=64)
    country_code: str = Field(default="CUB", max_length=3)
    city: str | None = Field(default=None, max_length=120)
    starts_on: date
    ends_on: date | None = None
    scope: ScopeType = "national"
    event_kind: str = Field(default="championship", max_length=32)
    notes: str | None = None


class SuiteEventCreate(SuiteEventBase):
    pass


class SuiteEventRead(SuiteEventBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class DisciplineBase(BaseModel):
    code: str = Field(max_length=32)
    name: str = Field(max_length=120)
    category: DisciplineCategory
    sub_category: DisciplineSubCategory | None = None
    sex: SexType | None = None
    is_indoor: bool = False
    sort_order: int = 0
    notes: str | None = None


class DisciplineCreate(DisciplineBase):
    pass


class DisciplineRead(DisciplineBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class AgeCategoryBase(BaseModel):
    code: str = Field(max_length=16)
    label: str = Field(max_length=80)
    min_age: int | None = Field(default=None, ge=0, le=120)
    max_age: int | None = Field(default=None, ge=0, le=120)
    notes: str | None = None


class AgeCategoryCreate(AgeCategoryBase):
    pass


class AgeCategoryRead(AgeCategoryBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class RegulationBase(BaseModel):
    code: str = Field(max_length=32)
    name: str = Field(max_length=160)
    edition_year: int | None = Field(default=None, ge=1900, le=2100)
    is_current: bool = False
    notes: str | None = None


class RegulationCreate(RegulationBase):
    pass


class RegulationRead(RegulationBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class ResultTypeBase(BaseModel):
    code: str = Field(max_length=16)
    label: str = Field(max_length=120)
    unit: str | None = Field(default=None, max_length=16)
    category: ResultTypeCategory


class ResultTypeCreate(ResultTypeBase):
    pass


class ResultTypeRead(ResultTypeBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}

