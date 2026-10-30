from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
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
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


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
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


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
    db.add(ac)
    await db.commit()
    await db.refresh(ac)
    return ac


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
    db.add(reg)
    await db.commit()
    await db.refresh(reg)
    return reg


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
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return rt