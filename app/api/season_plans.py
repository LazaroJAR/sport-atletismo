from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import athletics_read, athletics_write
from app.db.session import get_db
from app.models.athletics import (
    Athlete, Discipline, Event,
)
from app.models.athletics_stats import (
    SeasonPlan, SeasonPlanEvent,
)
from app.schemas.season_plan import (
    SeasonPlanCreate, SeasonPlanEventCreate,
    SeasonPlanEventRead, SeasonPlanRead, SeasonPlanUpdate,
)
from app.services.athletics import SeasonPlanService

router = APIRouter(prefix="/season-plans", tags=["atletismo-planes"])



async def _lock_plan(db: AsyncSession, plan_id: UUID) -> SeasonPlan:
    """Bloquea el plan hasta el commit/rollback del endpoint."""
    plan = await db.scalar(
        select(SeasonPlan).where(SeasonPlan.id == plan_id).with_for_update()
    )
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    return plan




# ---------- CRUD SeasonPlan ----------
@router.get("", response_model=list[SeasonPlanRead])
async def list_season_plans(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
    athlete_id: UUID | None = None,
):
    q = select(SeasonPlan).order_by(SeasonPlan.created_at.desc())
    if athlete_id:
        q = q.where(SeasonPlan.athlete_id == athlete_id)
    r = await db.execute(q)
    return list(r.scalars().all())


@router.post("", response_model=SeasonPlanRead, status_code=status.HTTP_201_CREATED)
async def create_season_plan(
    body: SeasonPlanCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(Athlete, body.athlete_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Atleta no encontrado")
    if not await db.get(Discipline, body.discipline_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disciplina no encontrada")

    plan = SeasonPlan(**body.model_dump(), updated_at=datetime.now(timezone.utc))
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=SeasonPlanRead)
async def get_season_plan(
    plan_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = await db.get(SeasonPlan, plan_id)
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    return plan


CALC_INPUTS = {"planned_result", "planned_position", "fundamental_result_points"}

@router.patch("/{plan_id}", response_model=SeasonPlanRead)
async def update_season_plan(
    plan_id: UUID,
    body: SeasonPlanUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = await _lock_plan(db, plan_id)

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(plan, k, v)

    if data.keys() & CALC_INPUTS:
        await SeasonPlanService.recalculate(db, plan_id)

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season_plan(
    plan_id: UUID,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = await db.get(SeasonPlan, plan_id)
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    await db.execute(delete(SeasonPlan).where(SeasonPlan.id == plan_id))
    await db.commit()
    return None



# ---------- Eventos del plan ----------
@router.get("/{plan_id}/events", response_model=list[SeasonPlanEventRead])
async def list_plan_events(
    plan_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(SeasonPlan, plan_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    r = await db.execute(
        select(SeasonPlanEvent).where(SeasonPlanEvent.season_plan_id == plan_id)
    )
    return list(r.scalars().all())


@router.post(
    "/{plan_id}/events",
    response_model=SeasonPlanEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_plan_event(
    plan_id: UUID,
    body: SeasonPlanEventCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _lock_plan(db, plan_id)
    if not await db.get(Event, body.event_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")

    dup = await db.scalar(select(SeasonPlanEvent).where(
        SeasonPlanEvent.season_plan_id == plan_id,
        SeasonPlanEvent.event_id == body.event_id,
    ))
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "El evento ya está en el plan")

    if body.is_fundamental:
        existing = await db.scalar(select(SeasonPlanEvent).where(
            SeasonPlanEvent.season_plan_id == plan_id,
            SeasonPlanEvent.is_fundamental.is_(True),
        ))
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Ya existe una competencia fundamental en este plan",
            )

    pe = SeasonPlanEvent(
        season_plan_id=plan_id, **body.model_dump(),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(pe)
    await db.flush()

    await SeasonPlanService.recalculate(db, plan_id)
    await db.commit()
    await db.refresh(pe)
    return pe


@router.delete(
    "/{plan_id}/events/{plan_event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_plan_event(
    plan_id: UUID,
    plan_event_id: UUID,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _lock_plan(db, plan_id)
    pe = await db.get(SeasonPlanEvent, plan_event_id)
    if not pe or pe.season_plan_id != plan_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento del plan no encontrado")

    await db.delete(pe)
    await db.flush()

    await SeasonPlanService.recalculate(db, plan_id)
    await db.commit()
    return None
