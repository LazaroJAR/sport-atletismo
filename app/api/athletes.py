from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import athletics_read, athletics_write
from app.db.session import get_db
from app.models.athlete_mirror import AthleteMirror
from app.models.athletics import Athlete, Discipline
from app.schemas.athlete import AthleteDeportistaCreate, AthleteRead, AthleteUpdate

router = APIRouter(prefix="/athletes", tags=["atletismo-atletas"])


def _nombre_completo(a: AthleteMirror) -> str:
    parts = [a.primer_nombre, a.segundo_nombre, a.primer_apellido, a.segundo_apellido]
    return " ".join(p for p in parts if p)


def _to_read(ath: Athlete, base: AthleteMirror) -> AthleteRead:
    return AthleteRead(
        id=ath.id,
        athlete_id=ath.athlete_id,
        nickname=ath.nickname,
        primary_discipline_id=ath.primary_discipline_id,
        active=ath.active,
        primer_nombre=base.primer_nombre,
        primer_apellido=base.primer_apellido,
        segundo_nombre=base.segundo_nombre,
        segundo_apellido=base.segundo_apellido,
        nombre_completo=_nombre_completo(base),
        documento_identidad=base.documento_identidad,
    )


@router.get("", response_model=list[AthleteRead])
async def list_athletes(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
    solo_activos: bool = True,
    buscar: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    q = select(Athlete, AthleteMirror).join(AthleteMirror, Athlete.athlete_id == AthleteMirror.id)
    if solo_activos:
        q = q.where(Athlete.active.is_(True), AthleteMirror.activo.is_(True))
    if buscar and buscar.strip():
        pat = f"%{buscar.strip()}%"
        q = q.where(or_(
            AthleteMirror.primer_nombre.ilike(pat),
            AthleteMirror.primer_apellido.ilike(pat),
            AthleteMirror.documento_identidad.ilike(pat),
        ))
    q = q.order_by(AthleteMirror.primer_apellido, AthleteMirror.primer_nombre).offset(skip).limit(limit)
    r = await db.execute(q)
    return [_to_read(a, m) for a, m in r.all()]


@router.post("", response_model=AthleteRead, status_code=status.HTTP_201_CREATED)
async def create_athlete(
    body: AthleteDeportistaCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.documento_identidad:
        ex = await db.scalar(select(AthleteMirror).where(
            AthleteMirror.documento_identidad == body.documento_identidad.strip()
        ))
        if ex:
            raise HTTPException(status.HTTP_409_CONFLICT, "Documento ya registrado como deportista")

    if body.primary_discipline_id and not await db.get(Discipline, body.primary_discipline_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disciplina no encontrada")

    now = datetime.now(timezone.utc)
    base = AthleteMirror(
        primer_nombre=body.primer_nombre.strip(),
        segundo_nombre=body.segundo_nombre.strip() if body.segundo_nombre else None,
        primer_apellido=body.primer_apellido.strip(),
        segundo_apellido=body.segundo_apellido.strip() if body.segundo_apellido else None,
        fecha_nacimiento=body.fecha_nacimiento,
        sexo=str(body.sexo).lower().strip(),
        documento_identidad=body.documento_identidad.strip() if body.documento_identidad else None,
        deporte_principal="atletismo",
        notas=body.notas,
        activo=True,
        updated_at=now,
    )
    db.add(base)
    await db.flush()

    ath = Athlete(
        athlete_id=base.id,
        nickname=body.nickname.strip() if body.nickname else None,
        primary_discipline_id=body.primary_discipline_id,
        active=True,
        updated_at=now,
    )
    db.add(ath)
    await db.commit()
    await db.refresh(base)
    await db.refresh(ath)
    return _to_read(ath, base)


@router.get("/{athlete_id}", response_model=AthleteRead)
async def get_athlete(
    athlete_id: UUID,
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(
        select(Athlete, AthleteMirror)
        .join(AthleteMirror, Athlete.athlete_id == AthleteMirror.id)
        .where(Athlete.id == athlete_id)
    )
    row = r.one_or_none()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Atleta no encontrado")
    return _to_read(*row)


@router.patch("/{athlete_id}", response_model=AthleteRead)
async def update_athlete(
    athlete_id: UUID,
    body: AthleteUpdate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ath = await db.get(Athlete, athlete_id)
    if not ath:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Atleta no encontrado")
    if body.nickname is not None:
        ath.nickname = body.nickname.strip() or None
    if body.primary_discipline_id is not None:
        ath.primary_discipline_id = body.primary_discipline_id
    if body.active is not None:
        ath.active = body.active
    ath.updated_at = datetime.now(timezone.utc)
    await db.commit()

    base = await db.get(AthleteMirror, ath.athlete_id)
    if not base:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Deportista base no encontrado")
    await db.refresh(ath)
    return _to_read(ath, base)