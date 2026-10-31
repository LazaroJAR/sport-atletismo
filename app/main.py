"""Servicio deportivo: atletismo — atletas (deportistas)"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api import router as api_router
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models import (  # noqa: F401 — metadatos
    AthleteMirror,
    Event,
    Participation,
    AgeCategory,
    Athlete,
    Regulation,
    ResultType,
    SuiteEvent,
    Discipline,
    SeasonPlan,
    SeasonPlanEvent,
    SeasonTrainingRecord,
    TrainingSessionLog,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS deportistas"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS athletics"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await session.commit()
    yield
    await engine.dispose()


app = FastAPI(
    title="Suite Deportiva Cuba — Atletismo",
    description="Atletas (deportistas), eventos y estadísticas.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router, prefix="")


@app.get("/health")
def health():
    return {"service": "sport-athletics", "sport": "athletics", "status": "ok"}
