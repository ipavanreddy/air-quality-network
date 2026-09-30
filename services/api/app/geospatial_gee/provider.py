"""Geospatial adapter: Earth Engine when configured, otherwise cached sample extracts."""
import time

from app.core import integrations
from app.core.samples import load
from app.interop.adapters import StateConfig

TTL_S = 3600
_cache: dict[str, tuple[float, dict]] = {}


def _sample_layers(cfg: StateConfig) -> dict:
    sat = load(f"{cfg.id}/satellite_h3.json")
    wx = load(f"{cfg.id}/weather.json")
    return {
        "satellite": {r["h3_cell"]: {**r, "is_sample": True} for r in sat["records"]},
        "weather": {"current": {**wx["current"], "is_sample": True},
                    "forecast": {**wx["forecast"], "is_sample": True}},
        "meta": {"mode": "sample", "satellite": sat["metadata"], "weather": wx["metadata"]},
    }


def land_use(cfg: StateConfig) -> dict[str, str]:
    """Synthetic demo land-use labels (both modes; see README known gaps)."""
    return {r["h3_cell"]: r["land_use"] for r in load(f"{cfg.id}/land_use_h3.json")["records"]}


def layers(cfg: StateConfig, cells: list[str]) -> dict:
    if not integrations.enabled("earth_engine"):
        return _sample_layers(cfg)
    cached = _cache.get(cfg.id)
    if cached and time.time() - cached[0] < TTL_S:
        return cached[1]
    try:
        from app.geospatial_gee import earth_engine

        weather = earth_engine.fetch_weather(*cfg.center)
        sat = earth_engine.fetch_satellite(cells, cfg.center, weather["current"]["wind_dir_deg"])
        fires = sat[0]["fire_count_upwind_100km"] if sat else 0
        for step in weather["forecast"]["steps"]:
            step["fire_count_upwind_forecast"] = fires  # persistence assumption, labelled
        result = {
            "satellite": {r["h3_cell"]: {**r, "is_sample": False} for r in sat},
            "weather": {"current": {**weather["current"], "is_sample": False},
                        "forecast": {**weather["forecast"], "is_sample": False}},
            "meta": {"mode": "earth_engine"},
        }
        integrations.clear_error("earth_engine")
        _cache[cfg.id] = (time.time(), result)
        return result
    except Exception as exc:  # noqa: BLE001
        integrations.record_fallback("earth_engine", exc)
        return _sample_layers(cfg)
