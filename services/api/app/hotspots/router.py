import h3
from fastapi import APIRouter

from app.core.deps import check_state, get_engine, not_found
from app.forecasting.model import aqi_category

router = APIRouter(prefix="/api", tags=["grid & hotspots"])


def _state_for_cell(cell: str) -> str:
    engine = get_engine()
    from app.interop.adapters import configs

    if not h3.is_valid_cell(cell):
        raise not_found("cell", cell)
    for cid in configs():
        if cell in engine.context(cid)["cells"]:
            return cid
    raise not_found("cell (outside demo grids)", cell)


@router.get("/grid")
def grid(city: str):
    return get_engine().grid(check_state(city))


@router.get("/cells/{cell_id}")
def cell(cell_id: str):
    """Canonical grid-cell snapshot (PRD §21) + Hotspot Confidence breakdown."""
    engine = get_engine()
    cid = _state_for_cell(cell_id)
    ctx = engine.context(cid)
    cfg = ctx["cfg"]
    s = engine.score_cell(ctx, cell_id)
    sat = ctx["geo"]["satellite"].get(cell_id) or {}
    wx = ctx["geo"]["weather"]["current"]
    fc = engine.cell_forecast(cid, cell_id, ctx)
    hs = next((h for h in engine.store.all("hotspots") if cell_id in h["h3_cells"] and h["status"] != "closed"), None)
    sensor = s["sensor"] or {}
    return {
        "state": cfg.state_code,
        "config_id": cid,
        "city": cfg.city,
        "cell_id": cell_id,
        "timestamp": sensor.get("observed_at") or wx.get("observed_at"),
        "observations": {
            "pm25_calibrated": sensor.get("pm25_calibrated"),
            "pm25_source": "low_cost_sensor" if sensor else None,
            "pm10": sensor.get("pm10"),
            "no2_column_anomaly_pct": sat.get("no2_column_anomaly_pct"),
            "fire_count_upwind_100km": sat.get("fire_count_upwind_100km"),
            "aod": sat.get("aod"),
        },
        "weather": {"wind_speed_ms": wx.get("wind_speed_ms"), "wind_dir_deg": wx.get("wind_dir_deg"),
                    "humidity": wx.get("humidity"), "boundary_layer_m": wx.get("boundary_layer_m")},
        "citizen_reports": len(s["report_ids"]),
        "hotspot": {"confidence": round(s["confidence"] / 100, 2), "band": s["band"],
                    "likely_source": (hs["likely_sources"][0]["type"] if hs and hs.get("likely_sources") else None),
                    "hotspot_id": hs["hotspot_id"] if hs else None},
        "forecast": {f"pm25_{h['horizon_hours']}h": h["pm25_expected"] for h in fc["horizons"]},
        "category": aqi_category(sensor["pm25_calibrated"]) if sensor else None,
        "confidence_breakdown": s,
        "land_use": ctx["land_use"].get(cell_id),
        "freshness": engine.freshness(ctx),
        "is_sample_data": engine.is_sample(ctx),
    }


@router.get("/cells/{cell_id}/forecast")
def cell_forecast(cell_id: str):
    cid = _state_for_cell(cell_id)
    return get_engine().cell_forecast(cid, cell_id)


@router.get("/hotspots")
def hotspots(city: str | None = None, status: str | None = None):
    rows = [h for h in get_engine().store.all("hotspots")
            if (city is None or h["state"] == city) and (status is None or h["status"] == status)]
    return sorted(rows, key=lambda h: -h["confidence"])


@router.get("/hotspots/{hotspot_id}")
def hotspot(hotspot_id: str):
    engine = get_engine()
    hs = engine.store.get("hotspots", hotspot_id)
    if hs is None:
        raise not_found("hotspot", hotspot_id)
    ctx = engine.context(hs["state"])
    return {**hs, "evidence_bundle": engine.bundle(ctx, hs),
            "alert": engine.store.get("alerts", hs["alert_id"]) if hs.get("alert_id") else None}


@router.post("/hotspots/{hotspot_id}/brief")
def regenerate_brief(hotspot_id: str):
    try:
        return get_engine().regenerate_brief(hotspot_id)
    except KeyError:
        raise not_found("hotspot", hotspot_id) from None
