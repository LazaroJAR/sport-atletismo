import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


# ---------- Atletas ----------
class AthleteDeportistaCreate(BaseModel):
    primer_nombre: str = Field(max_length=100)
    segundo_nombre: str | None = None
    primer_apellido: str = Field(max_length=100)
    segundo_apellido: str | None = None
    fecha_nacimiento: date
    sexo: str
    documento_identidad: str | None = Field(default=None, max_length=32)
    notas: str | None = None
    nickname: str | None = Field(default=None, max_length=80)
    primary_discipline_id: uuid.UUID | None = None

    @field_validator("sexo", mode="before")
    @classmethod
    def norm_sexo(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class AthleteRead(BaseModel):
    id: uuid.UUID
    athlete_id: uuid.UUID
    nickname: str | None
    primary_discipline_id: uuid.UUID | None
    active: bool
    primer_nombre: str
    primer_apellido: str
    segundo_nombre: str | None
    segundo_apellido: str | None
    nombre_completo: str
    documento_identidad: str | None
    model_config = {"from_attributes": True}


class AthleteUpdate(BaseModel):
    nickname: str | None = None
    primary_discipline_id: uuid.UUID | None = None
    active: bool | None = None
