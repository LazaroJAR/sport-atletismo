"""Servicios del módulo atletismo.

Cada servicio gestiona el recálculo de SU modelo. No hay acoplamiento:
- SeasonTrainingService solo toca SeasonTrainingRecord.
- SeasonPlanService solo toca SeasonPlan.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.athletics import (
    Discipline,
    Event,
    Participation,
)
from app.models.athletics_stats import (
    SeasonPlan,
    SeasonPlanEvent,
    SeasonTrainingRecord,
    TrainingSessionLog,
)


class EvaluationCalculator:
    """Coeficientes del documento (sin ranking)."""

    @staticmethod
    def is_time_discipline(category: str) -> bool:
        return category in ("track", "road", "race_walk")

    @staticmethod
    def compute_kec(plan_events, by_event, planned_result, is_time):
        n = len(plan_events)
        if n == 0:
            return 0, 0.0
        total = 0.0
        for pe in plan_events:
            p = by_event.get(pe.event_id)
            if p is None or p.result_value is None:
                continue
            rp = float(planned_result)
            ri = float(p.result_value)
            if ri <= 0 or rp <= 0:
                continue
            total += (rp / ri) if is_time else (ri / rp)
        return n, (total / n) / 100.0

    @staticmethod
    def compute_ke_p(objective_met_sessions: int, planned_sessions: int) -> float:
        if planned_sessions <= 0:
            return 0.0
        return objective_met_sessions / planned_sessions

    @staticmethod
    def compute_k1(rcf, rp, is_time) -> float:
        if rcf is None or rcf <= 0 or rp <= 0:
            return 0.0
        return (rp / rcf) if is_time else (rcf / rp)

    @staticmethod
    def compute_k2(points) -> float:
        return (points or 0.0) / 1000.0

    @staticmethod
    def compute_k3(pos_achieved, pos_planned) -> float:
        if pos_achieved is None or pos_planned is None:
            return 0.0
        return (pos_achieved / 10.0) - (pos_achieved - pos_planned)

    @staticmethod
    def compute_k4(fcf, fmrt) -> float:
        if not fcf or not fmrt:
            return 0.0
        delta_f = abs((fcf - fmrt).days)
        return max(0.0, 100.0 - delta_f) / 100.0

    @staticmethod
    def compute_ke_cc(k1, k2, k3, k4) -> float:
        return k1 + k2 + k3 + k4



# =====================================================================
# Servicio 1: SeasonTrainingRecord (independiente)
# =====================================================================
class SeasonTrainingService:
    """Recálculo del agregado de entrenamiento por temporada.

    Solo modifica SeasonTrainingRecord. Requiere que la instancia exista.
    """

    @staticmethod
    async def recalculate(
        db: AsyncSession, training_record_id: UUID
    ) -> SeasonTrainingRecord:
        """Recalcula n SEOC y KE'P desde las sesiones registradas.

        Lanza ValueError si el registro no existe.
        No hace commit (el llamador controla la transacción).
        """
        rec = await db.get(SeasonTrainingRecord, training_record_id)
        if rec is None:
            raise ValueError(
                f"SeasonTrainingRecord {training_record_id} no encontrado"
            )

        met_count = await db.scalar(
            select(func.count())
            .select_from(TrainingSessionLog)
            .where(
                TrainingSessionLog.training_record_id == rec.id,
                TrainingSessionLog.objective_met.is_(True),
            )
        ) or 0

        rec.objective_met_sessions_count = int(met_count)
        if rec.planned_sessions_count is None:
            rec.ke_p = None
        else:
            rec.ke_p = EvaluationCalculator.compute_ke_p(
                int(met_count), rec.planned_sessions_count
            )
        rec.calculated_at = datetime.now(timezone.utc)
        rec.updated_at = datetime.now(timezone.utc)

        await db.flush()
        return rec


# =====================================================================
# Servicio 2: SeasonPlan (independiente)
# =====================================================================
class SeasonPlanService:
    """Recálculo de los coeficientes del plan."""

    @staticmethod
    async def recalculate(db: AsyncSession, plan_id: UUID) -> SeasonPlan:
        plan = await db.get(SeasonPlan, plan_id)
        if plan is None:
            raise ValueError(f"SeasonPlan {plan_id} no encontrado")

        discipline = await db.get(Discipline, plan.discipline_id)
        if discipline is None:
            raise ValueError(f"Discipline {plan.discipline_id} no encontrada")
        is_time = EvaluationCalculator.is_time_discipline(discipline.category)

        pe_res = await db.execute(
            select(SeasonPlanEvent).where(SeasonPlanEvent.season_plan_id == plan.id)
        )
        plan_events = list(pe_res.scalars().all())

        event_ids = [pe.event_id for pe in plan_events]
        if event_ids:
            p_res = await db.execute(
                select(Participation).where(
                    Participation.event_id.in_(event_ids),
                    Participation.athlete_id == plan.athlete_id,
                )
            )
            by_event = {p.event_id: p for p in p_res.scalars().all()}
        else:
            by_event = {}

        n_comp, kec = EvaluationCalculator.compute_kec(
            plan_events, by_event, float(plan.planned_result), is_time
        )

        fundamental_pe = next((pe for pe in plan_events if pe.is_fundamental), None)
        rcf = pos_r = fcf = None
        if fundamental_pe is not None:
            p = by_event.get(fundamental_pe.event_id)
            if p is not None:
                rcf = float(p.result_value) if p.result_value is not None else None
                pos_r = p.place
            ev = await db.get(Event, fundamental_pe.event_id)
            if ev is None:
                raise ValueError(f"Event {fundamental_pe.event_id} no encontrado")
            fcf = ev.scheduled_at.date()

        k1 = EvaluationCalculator.compute_k1(rcf, float(plan.planned_result), is_time)
        k2 = EvaluationCalculator.compute_k2(plan.fundamental_result_points)
        k3 = EvaluationCalculator.compute_k3(pos_r, plan.planned_position)
        fmrt = await SeasonPlanService._compute_fmrt(db, plan, event_ids, is_time)
        k4 = EvaluationCalculator.compute_k4(fcf, fmrt)
        ke_cc = EvaluationCalculator.compute_ke_cc(k1, k2, k3, k4)

        now = datetime.now(timezone.utc)
        plan.competitions_in_plan = n_comp
        plan.kec = kec
        plan.fundamental_result = rcf
        plan.fundamental_position_achieved = pos_r
        plan.fundamental_competition_date = fcf
        plan.best_result_date = fmrt
        plan.k1 = k1
        plan.k2 = k2
        plan.k3 = k3
        plan.k4 = k4
        plan.ke_cc = ke_cc
        plan.stats_calculated_at = now
        plan.updated_at = now

        await db.flush()
        return plan

    @staticmethod
    async def _compute_fmrt(db, plan, event_ids, is_time):
        if not event_ids:
            return None
        res = await db.execute(
            select(Participation, Event.scheduled_at)
            .join(Event, Event.id == Participation.event_id)
            .where(
                Participation.athlete_id == plan.athlete_id,
                Participation.event_id.in_(event_ids),
                Participation.result_value.isnot(None),
                Participation.status == "valid",
            )
        )
        pairs = list(res.all())
        if not pairs:
            return None
        if is_time:
            best = min(pairs, key=lambda t: float(t[0].result_value))
        else:
            best = max(pairs, key=lambda t: float(t[0].result_value))
        return best[1].date()