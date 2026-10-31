from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import athletics_read, athletics_write
from app.db.session import get_db
from app.models.athletics_stats import (
    SeasonPlan, SeasonTrainingRecord, TrainingSessionLog,
)
from app.schemas.training import (
    SeasonTrainingRecordCreate, SeasonTrainingRecordRead,
    SeasonTrainingRecordUpdate,
    TrainingSessionLogCreate, TrainingSessionLogRead, TrainingSessionLogUpdate,
)
from app.services.athletics import SeasonTrainingService

router = APIRouter(prefix="/season-plans", tags=["atletismo-entrenamiento"])


async def _lock_training_record(
    db: AsyncSession, plan_id: UUID
) -> SeasonTrainingRecord:
    """Bloquea el registro de entrenamiento hasta el commit/rollback."""
    rec = await db.scalar(
        select(SeasonTrainingRecord)
        .where(SeasonTrainingRecord.season_plan_id == plan_id)
        .with_for_update()
    )
    if rec is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Registro de entrenamiento no encontrado"
        )
    return rec


# ---------- SeasonTrainingRecord ----------
@router.get(
    "/{plan_id}/training-record",
    response_model=SeasonTrainingRecordRead,
)
async def get_training_record(
    plan_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(SeasonPlan, plan_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    rec = await db.scalar(
        select(SeasonTrainingRecord).where(
            SeasonTrainingRecord.season_plan_id == plan_id
        )
    )
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de entrenamiento no encontrado")
    return rec


@router.post(
    "/{plan_id}/training-record",
    response_model=SeasonTrainingRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_record(
    plan_id: UUID,
    body: SeasonTrainingRecordCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(SeasonPlan, plan_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")

    existing = await db.scalar(
        select(SeasonTrainingRecord).where(
            SeasonTrainingRecord.season_plan_id == plan_id
        )
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El registro de entrenamiento ya existe para este plan",
        )

    now = datetime.now(timezone.utc)
    rec = SeasonTrainingRecord(
        season_plan_id=plan_id,
        planned_sessions_count=body.planned_sessions_count,
        objective_met_sessions_count=0,
        ke_p=0.0 if body.planned_sessions_count == 0 else None,
        notes=body.notes,
        updated_at=now,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


@router.patch(
    "/{plan_id}/training-record",
    response_model=SeasonTrainingRecordRead,
)
async def update_training_record(
    plan_id: UUID,
    body: SeasonTrainingRecordUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await db.get(SeasonPlan, plan_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    rec = await db.scalar(
        select(SeasonTrainingRecord).where(
            SeasonTrainingRecord.season_plan_id == plan_id
        )
    )
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de entrenamiento no encontrado")

    rec = await _lock_training_record(db, plan_id)

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(rec, k, v)

    if "planned_sessions_count" in data:
        await SeasonTrainingService.recalculate(db, rec.id)

    await db.commit()
    await db.refresh(rec)
    return rec


@router.delete(
    "/{plan_id}/training-record",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_training_record(
    plan_id: UUID,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await db.scalar(
        select(SeasonTrainingRecord).where(
            SeasonTrainingRecord.season_plan_id == plan_id
        )
    )
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de entrenamiento no encontrado")
    await db.execute(
        delete(SeasonTrainingRecord).where(SeasonTrainingRecord.id == rec.id)
    )
    await db.commit()
    return None



# ---------- TrainingSessionLog ----------
@router.get(
    "/{plan_id}/training-record/sessions",
    response_model=list[TrainingSessionLogRead],
)
async def list_sessions(
    plan_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await db.scalar(
        select(SeasonTrainingRecord).where(
            SeasonTrainingRecord.season_plan_id == plan_id
        )
    )
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de entrenamiento no encontrado")
    r = await db.execute(
        select(TrainingSessionLog)
        .where(TrainingSessionLog.training_record_id == rec.id)
        .order_by(TrainingSessionLog.session_date)
    )
    return list(r.scalars().all())


@router.post(
    "/{plan_id}/training-record/sessions",
    response_model=TrainingSessionLogRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    plan_id: UUID,
    body: TrainingSessionLogCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await _lock_training_record(db, plan_id)

    session = TrainingSessionLog(
        training_record_id=rec.id,
        session_date=body.session_date,
        planned_load_magnitude=body.planned_load_magnitude,
        effect_load_magnitude=body.effect_load_magnitude,
        rfc_percentage=body.rfc_percentage,
        objective_met=(body.planned_load_magnitude == body.effect_load_magnitude),
        notes=body.notes,
    )
    db.add(session)
    await db.flush()

    await SeasonTrainingService.recalculate(db, rec.id)
    await db.commit()
    await db.refresh(session)
    return session


@router.get(
    "/{plan_id}/training-record/sessions/{session_id}",
    response_model=TrainingSessionLogRead,
)
async def get_session(
    plan_id: UUID,
    session_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await db.scalar(
        select(SeasonTrainingRecord).where(
            SeasonTrainingRecord.season_plan_id == plan_id
        )
    )
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de entrenamiento no encontrado")
    session = await db.get(TrainingSessionLog, session_id)
    if not session or session.training_record_id != rec.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesión no encontrada")
    return session


CALC_SESSION_FIELDS = {"planned_load_magnitude", "effect_load_magnitude"}

@router.patch(
    "/{plan_id}/training-record/sessions/{session_id}",
    response_model=TrainingSessionLogRead,
)
async def update_session(
    plan_id: UUID,
    session_id: UUID,
    body: TrainingSessionLogUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await _lock_training_record(db, plan_id)
    session = await db.get(TrainingSessionLog, session_id)
    if not session or session.training_record_id != rec.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesión no encontrada")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(session, k, v)
    if data.keys() & CALC_SESSION_FIELDS:
        session.objective_met = (
            session.planned_load_magnitude == session.effect_load_magnitude
        )
        await db.flush()
        await SeasonTrainingService.recalculate(db, rec.id)
    else:
        await db.flush()

    await db.commit()
    await db.refresh(session)
    return session


@router.delete(
    "/{plan_id}/training-record/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
    plan_id: UUID,
    session_id: UUID,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await _lock_training_record(db, plan_id)
    session = await db.get(TrainingSessionLog, session_id)
    if not session or session.training_record_id != rec.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesión no encontrada")

    await db.delete(session)
    await db.flush()

    await SeasonTrainingService.recalculate(db, rec.id)
    await db.commit()
    return None