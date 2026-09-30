"""Sensor data adapter: official stations (CPCB real or sample) + low-cost feeds (simulated/ingested)."""
import time

import h3

from app.core import integrations
from app.core.samples import load
from app.interop.adapters import RawObservation, StateConfig, map_feed_record
from app.sensors_calibration import cpcb
from app.sensors_calibration.calibration import (
    CALIBRATION_MODEL_VERSION,
    calibrate_pm25,
)

H3_RES = 8
_station_cache: dict[str, tuple[float, dict]] = {}
STATION_TTL_S = 900


def sensor_registry(cfg: StateConfig) -> dict[str, dict]:
    data = load(f"{cfg.id}/sensors_lowcost_meta.json")
    out = {}
    for s in data["records"]:
        out[s["sensor_id"]] = {
            **s,
            "h3_cell": h3.latlng_to_cell(s["lat"], s["lon"], H3_RES),
            "source": data["metadata"]["source"],
        }
    return out


def to_observation(cfg: StateConfig, raw: RawObservation, sensor: dict, *, simulated: bool,
                   source: str) -> dict:
    return {
        "sensor_id": raw.sensor_id,
        "type": "low_cost",
        "state": cfg.id,
        "lat": sensor["lat"],
        "lon": sensor["lon"],
        "h3_cell": sensor["h3_cell"],
        "timestamp": raw.timestamp.isoformat(),
        "pm25_raw": raw.pm25_raw,
        "pm25_calibrated": calibrate_pm25(raw.pm25_raw, raw.humidity),
        "pm10": raw.pm10,
        "no2": None,
        "temperature": raw.temperature,
        "humidity": raw.humidity,
        "calibration_model_version": CALIBRATION_MODEL_VERSION,
        "source": source,
        "indicative": True,
        "is_simulated": simulated,
    }


def lowcost_observations(cfg: StateConfig, ingested: list[dict] | None = None) -> list[dict]:
    """All low-cost observations (simulated feed mapped through the state adapter + ingested)."""
    registry = sensor_registry(cfg)
    feed = load(f"{cfg.id}/sensors_lowcost_feed.json")
    src = "Simulated low-cost sensor feed (sample)"
    obs = []
    for rec in feed["records"]:
        raw = map_feed_record(cfg, rec)
        obs.append(to_observation(cfg, raw, registry[raw.sensor_id], simulated=True, source=src))
    obs.extend(ingested or [])
    return sorted(obs, key=lambda o: o["timestamp"])


def latest_by_sensor(observations: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for o in observations:
        if o["sensor_id"] not in latest or o["timestamp"] >= latest[o["sensor_id"]]["timestamp"]:
            latest[o["sensor_id"]] = o
    return latest


def _sample_station(cfg: StateConfig) -> dict:
    data = load(f"{cfg.id}/official_stations.json")
    st = dict(data["records"][0])
    st.update({"source": data["metadata"]["source"], "is_sample": True})
    return st


def official_station(cfg: StateConfig) -> dict:
    """Nearest official station reading: live CPCB when DATA_GOV_IN_API_KEY is set, else sample."""
    if not integrations.enabled("cpcb"):
        return _sample_station(cfg)
    cached = _station_cache.get(cfg.id)
    if cached and time.time() - cached[0] < STATION_TTL_S:
        return cached[1]
    try:
        st = cpcb.fetch_nearest_station(cfg.state_code, *cfg.center)
        if not st:
            raise RuntimeError(f"no CPCB station with PM2.5 found for {cfg.state_code}")
        integrations.clear_error("cpcb")
        _station_cache[cfg.id] = (time.time(), st)
        return st
    except Exception as exc:  # noqa: BLE001 - any failure -> labelled fallback
        integrations.record_fallback("cpcb", exc)
        return _sample_station(cfg)
