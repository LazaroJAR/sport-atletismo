from fastapi import APIRouter

from app.api import (
    athletes, catalog, events, participations, season_plans, training
)

router = APIRouter()
router.include_router(catalog.router)
router.include_router(athletes.router)
router.include_router(events.router)
router.include_router(participations.router)
router.include_router(season_plans.router)
router.include_router(training.router)


@router.get("/")
def root():
    return {
        "module": "sport-athletics",
        "message": "API del módulo atletismo (World Athletics)",
        "endpoints": [
            "/suite-events",
            "/disciplines",
            "/age-categories",
            "/regulations",
            "/result-types",
            "/athletes",
            "/events",
            "/events/{id}/participations",
            "/participations",
            "/season-plans",
            "/season-plans/{id}/events",
            "/season-plans/{id}/training-record",
            "/season-plans/{id}/training-record/sessions",
        ],
    }