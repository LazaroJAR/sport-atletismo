from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import athletics_read, athletics_write
from app.db.session import get_db
from app.models.athletics import (
    AgeCategory, Discipline, Event, Participation, Regulation, SuiteEvent,
)
from app.schemas.event import (
    EventConditionsUpdate, EventCreate, EventRead, EventStatusUpdate,
)
from app.schemas.participation import ParticipationRead

router = APIRouter(prefix="/events", tags=["atletismo-eventos"])


@router.get("", response_model=list[EventRead])
async def list_events(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
    suite_event_id: UUID | None = None,
    discipline_id: UUID | None = None,
    status_filter: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    q = select(Event).order_by(Event.scheduled_at.desc())
    if suite_event_id:
        q = q.where(Event.suite_event_id == suite_event_id)
    if discipline_id:
        q = q.where(Event.discipline_id == discipline_id)
    if status_filter:
        q = q.where(Event.status == status_filter)
    q = q.offset(skip).limit(limit)
    r = await db.execute(q)
    return list(r.scalars().all())


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(SuiteEvent, body.suite_event_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SuiteEvent no encontrado")
    if not await db.get(Discipline, body.discipline_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disciplina no encontrada")
    if not await db.get(Regulation, body.regulation_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reglamento no encontrado")
    if body.age_category_id and not await db.get(AgeCategory, body.age_category_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría de edad no encontrada")

    # Derivar is_wind_legal si no viene explícito y hay wind_ms
    is_wind_legal = body.is_wind_legal
    if is_wind_legal is None and body.wind_ms is not None:
        is_wind_legal = abs(body.wind_ms) <= 2.0

    ev = Event(
        **body.model_dump(exclude={"is_wind_legal"}),
        is_wind_legal=is_wind_legal,
        status="scheduled",
        updated_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    return ev


@router.patch("/{event_id}/status", response_model=EventRead)
async def update_event_status(
    event_id: UUID,
    body: EventStatusUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    ev.status = body.status
    ev.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.patch("/{event_id}/conditions", response_model=EventRead)
async def update_event_conditions(
    event_id: UUID,
    body: EventConditionsUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(ev, k, v)
    # Re-derivar validez de viento si cambió wind_ms y no se pasó explícito
    if "wind_ms" in data and "is_wind_legal" not in data and ev.wind_ms is not None:
        ev.is_wind_legal = abs(ev.wind_ms) <= 2.0
    ev.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.get("/{event_id}/participations", response_model=list[ParticipationRead])
async def list_event_participations(
    event_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    r = await db.execute(
        select(Participation)
        .where(Participation.event_id == event_id)
        .order_by(Participation.place.asc().nulls_last(), Participation.lane.asc().nulls_last())
    )
    return list(r.scalars().all())