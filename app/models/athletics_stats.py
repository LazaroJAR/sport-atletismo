import uuid
from datetime import date, datetime
from sqlalchemy import text

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.athletics import Athlete, Discipline, Event


SCHEMA = "athletics"



class SeasonPlanEvent(Base):
    """Competencia (Event) incluida en el plan de temporada de un atleta.

    Es la relación N:M entre SeasonPlan y Event, con atributos propios
    de la relación (rol, si es la competencia fundamental, target override).

    NO duplica:
    - planned_result (RP): se lee de SeasonPlan.planned_result
    - result_achieved (Ri): se lee de Participation
      (lookup: event_id + season_plan.athlete_id)
    - fulfillment_pct (%Ci): se calcula como Ri / RP (o RP / Ri en tiempos)

    Un SeasonPlan puede tener N competencias planificadas, pero solo una
    puede ser is_fundamental=True (garantizado por índice parcial).
    """
    __tablename__ = "season_plan_events"
    __table_args__ = (
        UniqueConstraint("season_plan_id", "event_id",
                         name="uq_athletics_plan_event"),
        Index(
            "uq_athletics_plan_fundamental",
            "season_plan_id",
            unique=True,
            postgresql_where=text("is_fundamental = true"),
        ),
        Index("ix_athletics_plan_events_plan", "season_plan_id"),
        Index("ix_athletics_plan_events_event", "event_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.season_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Solo una por plan (garantizado por índice parcial)
    is_fundamental: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    season_plan: Mapped["SeasonPlan"] = relationship(back_populates="plan_events")
    event: Mapped["Event"] = relationship()



class SeasonPlan(Base):
    """Plan de temporada + estadísticos derivados (excepto ranking)."""
    __tablename__ = "season_plans"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.athletes.id", ondelete="CASCADE"), nullable=False,
    )
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.disciplines.id", ondelete="RESTRICT"), nullable=False,
    )

    # ---------- INPUTS (planificación) ----------
    planned_result: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)   # RP
    planned_position: Mapped[int | None] = mapped_column(Integer, nullable=True)           # POS P
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---------- EJE 1: Efectividad (derivados) ----------
    competitions_in_plan: Mapped[int | None] = mapped_column(Integer, nullable=True)       # n
    kec: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)       # KEC

    
    # ---------- EJE 3: Eficacia (derivados) ----------
    fundamental_result: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)      # RCF
    fundamental_result_points: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # PTS
    fundamental_position_achieved: Mapped[int | None] = mapped_column(Integer, nullable=True)    # POS R
    fundamental_competition_date: Mapped[date | None] = mapped_column(Date, nullable=True)       # FCF
    best_result_date: Mapped[date | None] = mapped_column(Date, nullable=True)                   # FMRT
    k1: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    k2: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    k3: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    k4: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    ke_cc: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)               # KE''C

    # ---------- EJE 4: Integralidad (agregado) ----------

    # ---------- Metadatos de cálculo ----------
    stats_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stats_is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ---------- Relaciones ----------
    athlete: Mapped["Athlete"] = relationship()
    discipline: Mapped["Discipline"] = relationship()
    plan_events: Mapped[list["SeasonPlanEvent"]] = relationship(
        back_populates="season_plan", cascade="all, delete-orphan"
    )
    training_record: Mapped["SeasonTrainingRecord | None"] = relationship(
        back_populates="season_plan", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def fundamental_plan_event(self) -> "SeasonPlanEvent | None":
        for pe in self.plan_events:
            if pe.is_fundamental:
                return pe
        return None



class SeasonTrainingRecord(Base):
    """Agregado de entrenamiento por temporada (1:1 con SeasonPlan).

    Almacena los inputs y coeficientes del eje de Eficiencia de la Preparación:
    - n SEP  (planned_sessions_count): sesiones planificadas
    - n SEOC (objective_met_sessions_count): sesiones con MCP == MEC
    - KE'P   (ke_p): coeficiente de eficiencia = n SEOC / n SEP
    """
    __tablename__ = "season_training_records"
    __table_args__ = (
        UniqueConstraint("season_plan_id", name="uq_athletics_season_training_plan"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.season_plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ---- Input ----
    planned_sessions_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # n SEP

    # ---- Derivados ----
    objective_met_sessions_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # n SEOC
    ke_p: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)                  # KE'P

    # ---- Metadatos ----
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ---- Relaciones ----
    season_plan: Mapped["SeasonPlan"] = relationship(back_populates="training_record")
    sessions: Mapped[list["TrainingSessionLog"]] = relationship(
        back_populates="training_record", cascade="all, delete-orphan"
    )



class TrainingSessionLog(Base):
    """Registro de una sesión de entrenamiento individual.

    Renombrado desde TrainingLoadRecord. Alimenta el agregado n SEOC
    (cuenta de sesiones con objective_met=True) en SeasonTrainingRecord.
    """
    __tablename__ = "training_session_logs"
    __table_args__ = (
        Index("ix_athletics_session_logs_record_date", "training_record_id", "session_date"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.season_training_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)

    # MCP: 5=Máxima, 4=Submáxima, 3=Media, 2=Moderada, 1=Ligera
    planned_load_magnitude: Mapped[int] = mapped_column(Integer, nullable=False)
    # MEC: 5=96–100%, 4=91.9–95.9%, 3=87.8–91.8%, 2=83.7–87.7%, 1=79.6–83.6% RFCi
    effect_load_magnitude: Mapped[int] = mapped_column(Integer, nullable=False)
    rfc_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # SEOC por sesión: True si MCP == MEC
    objective_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    training_record: Mapped["SeasonTrainingRecord"] = relationship(back_populates="sessions")
