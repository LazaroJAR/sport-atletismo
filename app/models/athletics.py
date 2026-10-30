"""Esquema atletismo: eventos, pruebas, reglamentos, atletas y actuaciones (performances)."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

SCHEMA = "athletics"


class SuiteEvent(Base):
    """Evento contenedor (campeonato, meeting, mitin, etc.)."""
    __tablename__ = "suite_events"
    __table_args__ = (
        UniqueConstraint("code", name="uq_athletics_suite_events_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, default="CUB")
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    scope: Mapped[str] = mapped_column(String(24), nullable=False, default="national")
    event_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="championship")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Discipline(Base):
    """Catálogo de pruebas oficiales (100m, salto de altura, maratón, etc.)."""
    __tablename__ = "disciplines"
    __table_args__ = (
        UniqueConstraint("code", name="uq_athletics_disciplines_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # Ej: "100m", "HJ", "MAR"
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # "track", "field", "road", "combined", "race_walk"
    sub_category: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "sprint", "hurdles", "jump", "throw", etc.
    sex: Mapped[str | None] = mapped_column(String(12), nullable=True)  # "M", "W", "X" (mixto)
    is_indoor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgeCategory(Base):
    """Categorías de edad oficiales (Sub-18, Sub-20, Sénior, Máster, etc.)."""
    __tablename__ = "age_categories"
    __table_args__ = (
        UniqueConstraint("code", name="uq_athletics_age_categories_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(16), nullable=False)  # "U18", "U20", "SEN", "MAS"
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Regulation(Base):
    """Reglamento de competición (World Athletics / RFEA)."""
    __tablename__ = "regulations"
    __table_args__ = (
        UniqueConstraint("code", name="uq_athletics_regulations_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # "WA_2026", "RFEA_2025"
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    edition_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResultType(Base):
    """Tipología de resultado (tiempo, distancia, puntos, DNF, DSQ, etc.)."""
    __tablename__ = "result_types"
    __table_args__ = (
        UniqueConstraint("code", name="uq_athletics_result_types_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(16), nullable=False)  # "TIME", "DIST", "POINTS", "DNF", "DSQ"
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(16), nullable=True)  # "s", "m", "pts"
    category: Mapped[str] = mapped_column(String(24), nullable=False)  # "valid", "invalid", "no_mark"


class Athlete(Base):
    """Atleta (vinculado a la tabla maestra de deportistas)."""
    __tablename__ = "athletes"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deportistas.athletes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    primary_discipline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.disciplines.id", ondelete="SET NULL"),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    primary_discipline: Mapped["Discipline | None"] = relationship()


class Event(Base):
    """Instancia concreta de una prueba dentro de un SuiteEvent.

    Ejemplo: 'Final 100m masculino' dentro de 'Campeonato Nacional 2026'.
    Agrupa las condiciones ambientales compartidas por todos los participantes.
    """
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_athletics_events_suite", "suite_event_id"),
        Index("ix_athletics_events_discipline", "discipline_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.suite_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.disciplines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    age_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.age_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.regulations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)  # "Final 100m masculino"
    round: Mapped[str] = mapped_column(String(24), nullable=False, default="final")  # heat, quarter, semi, final
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled")  # scheduled, running, finished, cancelled

    # Condiciones ambientales compartidas por TODOS los participantes
    wind_ms: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)      # +2.1, -0.5, 0.0
    wind_direction: Mapped[str | None] = mapped_column(String(8), nullable=True)     # "N", "S", "E", "W", "NE"...
    is_wind_legal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)       # |wind| <= 2.0 m/s
    temperature_c: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    humidity_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    track_condition: Mapped[str | None] = mapped_column(String(24), nullable=True)   # dry, wet, indoor

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    suite_event: Mapped["SuiteEvent"] = relationship()
    discipline: Mapped["Discipline"] = relationship()
    age_category: Mapped["AgeCategory | None"] = relationship()
    regulation: Mapped["Regulation"] = relationship()
    participations: Mapped[list["Participation"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class Participation(Base):
    """Participación de un atleta en un evento concreto (relación M:N con atributos)."""
    __tablename__ = "participations"
    __table_args__ = (
        UniqueConstraint("event_id", "athlete_id", name="uq_athletics_participations_event_athlete"),
        UniqueConstraint("event_id", "bib_number", name="uq_athletics_participations_event_bib"),
        Index("ix_athletics_participations_athlete", "athlete_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.events.id", ondelete="CASCADE"),
        nullable=False,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.athletes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    result_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.result_types.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Identificación en la prueba
    bib_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    lane: Mapped[int | None] = mapped_column(Integer, nullable=True)                # solo pista
    starting_position: Mapped[int | None] = mapped_column(Integer, nullable=True)    # orden de salida

    # Resultado individual
    result_value: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)   # seg, metros o puntos
    result_display: Mapped[str | None] = mapped_column(String(32), nullable=True)       # "9.87", "2.35", "8:05.12"
    place: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)                  # pruebas combinadas
    reaction_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_photo_finish: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Viento propio: necesario en saltos/lanzamientos donde cada intento tiene su lectura.
    # En pruebas de pista se deja NULL y se usa Event.wind_ms.
    wind_ms: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    is_wind_legal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Logros
    is_personal_best: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_season_best: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_national_record: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_world_record: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(String(24), nullable=False, default="valid")  # valid, dns, dnf, dsq
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    event: Mapped["Event"] = relationship(back_populates="participations")
    athlete: Mapped["Athlete"] = relationship()
    result_type: Mapped["ResultType"] = relationship()
