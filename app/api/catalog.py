from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import athletics_read, athletics_write
from app.db.session import get_db
from app.models.athletics import AgeCategory, Discipline, Regulation, ResultType, SuiteEvent
from app.schemas.catalog import (
    AgeCategoryCreate, AgeCategoryRead,
    DisciplineCreate, DisciplineRead,
    RegulationCreate, RegulationRead,
    ResultTypeCreate, ResultTypeRead,
    SuiteEventCreate, SuiteEventRead,
)

router = APIRouter(tags=["atletismo-catalogo"])


async def _create_unique(db: AsyncSession, obj, conflict: str):
    db.add(obj)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, conflict)
    await db.refresh(obj)
    return obj


@router.get("/suite-events", response_model=list[SuiteEventRead])
async def list_suite_events(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(SuiteEvent).order_by(SuiteEvent.starts_on.desc()))
    return list(r.scalars().all())


@router.post("/suite-events", response_model=SuiteEventRead, status_code=status.HTTP_201_CREATED)
async def create_suite_event(
    body: SuiteEventCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    e = SuiteEvent(**body.model_dump())
    return await _create_unique(db, e, "Ya existe un SuiteEvent con ese código")


@router.get("/disciplines", response_model=list[DisciplineRead])
async def list_disciplines(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
):
    q = select(Discipline).order_by(Discipline.sort_order, Discipline.name)
    if category:
        q = q.where(Discipline.category == category)
    r = await db.execute(q)
    return list(r.scalars().all())


@router.post("/disciplines", response_model=DisciplineRead, status_code=status.HTTP_201_CREATED)
async def create_discipline(
    body: DisciplineCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    d = Discipline(**body.model_dump())
    return await _create_unique(db, d, "Ya existe una disciplina con ese código")


@router.get("/age-categories", response_model=list[AgeCategoryRead])
async def list_age_categories(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(AgeCategory).order_by(AgeCategory.code))
    return list(r.scalars().all())


@router.post("/age-categories", response_model=AgeCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_age_category(
    body: AgeCategoryCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ac = AgeCategory(**body.model_dump())
    return await _create_unique(db, ac, "Ya existe una categoría de edad con ese código")


@router.get("/regulations", response_model=list[RegulationRead])
async def list_regulations(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(Regulation).order_by(Regulation.name))
    return list(r.scalars().all())


@router.post("/regulations", response_model=RegulationRead, status_code=status.HTTP_201_CREATED)
async def create_regulation(
    body: RegulationCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reg = Regulation(**body.model_dump())
    return await _create_unique(db, reg, "Ya existe un reglamento con ese código")


@router.get("/result-types", response_model=list[ResultTypeRead])
async def list_result_types(
    _: Annotated[dict, Depends(athletics_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(ResultType).order_by(ResultType.label))
    return list(r.scalars().all())


@router.post("/result-types", response_model=ResultTypeRead, status_code=status.HTTP_201_CREATED)
async def create_result_type(
    body: ResultTypeCreate,
    _: Annotated[dict, Depends(athletics_write)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rt = ResultType(**body.model_dump())
    return await _create_unique(db, rt, "Ya existe un tipo de resultado con ese código")