"""Reflejo de deportistas.athletes para insertar desde judo en la misma BD."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base

SCHEMA = "deportistas"


class AthleteMirror(Base):
    __tablename__ = "athletes"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primer_nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    segundo_nombre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primer_apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    segundo_apellido: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    sexo: Mapped[str] = mapped_column(String(20), nullable=False)
    lateralidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    documento_identidad: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    deporte_principal: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
