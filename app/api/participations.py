from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import athletics_read, athletics_write
from app.db.session import get_db
from app.models.athletics import (
    Athlete, Event, Participation, PerformanceSplit, ResultType,
)
from app.schemas.participation import (
    ParticipationCreate, ParticipationRead, ParticipationResultUpdate,
)

router = APIRouter(prefix="/participations", tags=["atletismo-participaciones"])



@router.get("", response_model=list[ParticipationRead])
async def list_participations(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
    event_id: UUID | None = None,
    athlete_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    q = select(Participation).order_by(Participation.created_at.desc())
    if event_id:
        q = q.where(Participation.event_id == event_id)
    if athlete_id:
        q = q.where(Participation.athlete_id == athlete_id)
    q = q.offset(skip).limit(limit)
    r = await db.execute(q)
    return list(r.scalars().all())


@router.post("", response_model=ParticipationRead, status_code=status.HTTP_201_CREATED)
async def create_participation(
    body: ParticipationCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(Event, body.event_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    if not await db.get(Athlete, body.athlete_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Atleta no encontrado")
    if not await db.get(ResultType, body.result_type_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tipo de resultado no encontrado")

    # Unicidad (event_id, athlete_id)
    dup = await db.scalar(select(Participation).where(
        Participation.event_id == body.event_id,
        Participation.athlete_id == body.athlete_id,
    ))
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "El atleta ya participa en este evento")

    is_wind_legal = body.is_wind_legal
    if is_wind_legal is None and body.wind_ms is not None:
        is_wind_legal = abs(body.wind_ms) <= 2.0

    p = Participation(
        **body.model_dump(exclude={"is_wind_legal"}),
        is_wind_legal=is_wind_legal,
        status="valid",
        updated_at=datetime.now(timezone.utc),
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@router.get("/{participation_id}", response_model=ParticipationRead)
async def get_participation(
    participation_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    p = await db.get(Participation, participation_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Participación no encontrada")
    return p


@router.patch("/{participation_id}/result", response_model=ParticipationRead)
async def update_participation_result(
    participation_id: UUID,
    body: ParticipationResultUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    p = await db.get(Participation, participation_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Participación no encontrada")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)
    if "wind_ms" in data and "is_wind_legal" not in data and p.wind_ms is not None:
        p.is_wind_legal = abs(p.wind_ms) <= 2.0
    p.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(p)
    return p
