"""State adapters: city/state-specific configs and feeds -> canonical schema (PRD §20-22).

Each state config lives in data/adapters/<id>.json (jurisdiction, thresholds, action rules,
language, shared-model choice and the field map of its sensor vendor feed).
"""
import json
from datetime import datetime
from functools import lru_cache

from pydantic import BaseModel

from app.config import settings
from app.core.samples import parse_ts


class ActionRule(BaseModel):
    id: str
    action: str
    applies_to: list[str]
    stage: str = "any"


class Jurisdiction(BaseModel):
    id: str
    name: str
    district: str


class Neighbour(BaseModel):
    config_id: str
    jurisdiction_id: str
    name: str
    center: tuple[float, float]
    sources: list[str]


class SensorFeed(BaseModel):
    format: str
    field_map: dict[str, str]
    timestamp_format: str
    timezone: str


class StateConfig(BaseModel):
    id: str
    state_code: str
    name: str
    city: str
    corridor: str
    center: tuple[float, float]
    default_language: str
    languages: list[str]
    jurisdiction: Jurisdiction
    hotspot_threshold: float
    fast_path: dict[str, float]
    forecast_model: str
    calibration_model: str
    cross_boundary_neighbours: list[Neighbour]
    sensor_feed: SensorFeed
    action_rules: list[ActionRule]


class RawObservation(BaseModel):
    """Canonical (uncalibrated) observation produced by a state adapter."""

    sensor_id: str
    timestamp: datetime
    pm25_raw: float
    pm10: float | None = None
    temperature: float | None = None
    humidity: float | None = None


@lru_cache
def configs() -> dict[str, StateConfig]:
    out = {}
    for path in sorted(settings.adapters_dir.glob("*.json")):
        cfg = StateConfig.model_validate(json.loads(path.read_text()))
        out[cfg.id] = cfg
    return out


def get_config(config_id: str) -> StateConfig:
    try:
        return configs()[config_id]
    except KeyError as exc:
        raise KeyError(f"unknown city/state config '{config_id}'") from exc


def config_for_jurisdiction(jurisdiction_id: str) -> StateConfig | None:
    return next((c for c in configs().values() if c.jurisdiction.id == jurisdiction_id), None)


def map_feed_record(cfg: StateConfig, record: dict) -> RawObservation:
    """Map one vendor-feed record (state-specific field names/time format) to the canonical form."""
    fm = cfg.sensor_feed.field_map

    def num(key: str) -> float | None:
        v = record.get(fm[key]) if key in fm else None
        return None if v is None else float(v)

    return RawObservation(
        sensor_id=str(record[fm["sensor_id"]]),
        timestamp=parse_ts(str(record[fm["timestamp"]]), cfg.sensor_feed.timestamp_format,
                           cfg.sensor_feed.timezone),
        pm25_raw=float(record[fm["pm25_raw"]]),
        pm10=num("pm10"),
        temperature=num("temperature"),
        humidity=num("humidity"),
    )
