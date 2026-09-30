from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.alerts.router import router as alerts_router
from app.config import settings
from app.core import integrations
from app.core.deps import get_engine
from app.hotspots.router import router as hotspots_router
from app.interop.router import router as interop_router
from app.localization.router import router as localization_router
from app.reports.router import router as reports_router
from app.reports.service import seed_samples
from app.sensors_calibration.router import router as sensors_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_samples(get_engine())
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (reports_router, sensors_router, hotspots_router, alerts_router, localization_router, interop_router):
    app.include_router(r)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "project": settings.project_name, "model": settings.gemini_model,
            "demo_mode": integrations.status()["demo_mode"]}
