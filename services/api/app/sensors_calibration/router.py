from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.core.deps import check_state, get_engine, not_found
from app.interop.adapters import RawObservation, configs, get_config
from app.sensors_calibration.provider import sensor_registry, to_observation

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class ObservationIn(BaseModel):
    timestamp: datetime
    pm25_raw: float
    pm10: float | None = None
    temperature: float | None = None
    humidity: float | None = None


@router.get("")
def list_sensors(city: str):
    check_state(city)
    ctx = get_engine().context(city)
    registry = sensor_registry(ctx["cfg"])
    return {
        "state": city,
        "official_station": ctx["station"],
        "low_cost": [{**registry[sid], "latest": obs} for sid, obs in ctx["latest"].items() if sid in registry],
    }


@router.post("/{sensor_id}/observations")
def ingest(sensor_id: str, body: ObservationIn, x_ingest_token: str | None = Header(default=None)):
    if settings.sensor_ingest_token and x_ingest_token != settings.sensor_ingest_token:
        raise HTTPException(401, "invalid or missing X-Ingest-Token")
    for cfg in configs().values():
        registry = sensor_registry(cfg)
        if sensor_id in registry:
            break
    else:
        raise not_found("sensor", sensor_id)
    raw = RawObservation(sensor_id=sensor_id, **body.model_dump())
    if raw.timestamp.tzinfo is None:
        raise HTTPException(422, "timestamp must include a timezone offset")
    obs = to_observation(get_config(cfg.id), raw, registry[sensor_id], simulated=False,
                         source="Ingested via POST /api/sensors/{id}/observations")
    engine = get_engine()
    key = f"{sensor_id}:{raw.timestamp.isoformat()}"
    engine.store.put("observations", key, obs)
    engine.detect(cfg.id)
    return obs
