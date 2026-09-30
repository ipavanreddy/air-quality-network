import json

import h3
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import settings
from app.core import integrations
from app.core.deps import check_state, get_engine, not_found
from app.interop.adapters import configs
from app.models_registry.registry import get_model, models
from app.reports.service import seed_samples

router = APIRouter(prefix="/api", tags=["cities, models, config"])


@router.get("/config")
def config():
    return integrations.status()


@router.get("/cities")
def cities():
    return [c.model_dump(exclude={"sensor_feed"}) | {"sensor_feed_format": c.sensor_feed.format}
            for c in configs().values()]


@router.get("/cities/{city_id}")
def city(city_id: str):
    return configs()[check_state(city_id)].model_dump()


@router.get("/cities/{city_id}/analytics")
def analytics(city_id: str):
    check_state(city_id)
    engine = get_engine()
    cfg = configs()[city_id]
    alerts = [a for a in engine.store.all("alerts") if a["jurisdiction_id"] == cfg.jurisdiction.id]
    by_status: dict[str, int] = {}
    for a in alerts:
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
    reports = [r for r in engine.store.all("reports") if r["state"] == city_id]
    return {
        "state": city_id,
        "active_hotspots": sum(1 for h in engine.store.all("hotspots") if h["state"] == city_id and h["status"] != "closed"),
        "alerts_by_status": by_status,
        "cross_boundary_in": sum(1 for a in alerts if a["kind"] == "cross_boundary"),
        "cross_boundary_out": sum(1 for a in engine.store.all("alerts")
                                  if a.get("origin_jurisdiction_id") == cfg.jurisdiction.id),
        "citizen_reports": len(reports),
        "verified_reports": sum(1 for r in reports if r["status"] == "verified"),
    }


@router.get("/cities/{city_id}/forecast")
def corridor_forecast(city_id: str):
    return get_engine().corridor_forecast(check_state(city_id))


@router.get("/models")
def list_models():
    return models()


@router.get("/models/{model_id}/card")
def model_card(model_id: str):
    m = get_model(model_id)
    if m is None:
        raise not_found("model", model_id)
    return m


@router.post("/demo/reset")
def reset_demo():
    engine = get_engine()
    engine.store.reset()
    seed_samples(engine)
    return {"status": "reset", "reports": len(engine.store.all("reports")),
            "alerts": len(engine.store.all("alerts"))}


@router.get("/locate")
def locate(lat: float, lon: float):
    """Jurisdiction + H3 cell lookup for a point (used by the citizen app before reporting)."""
    engine = get_engine()
    cfg, dist = engine.nearest_config(lat, lon)
    cell = h3.latlng_to_cell(lat, lon, 8)
    if cfg is None:
        return {"in_pilot_area": False, "h3_cell": cell, "nearest_pilot_km": round(dist)}
    in_grid = cell in engine.context(cfg.id)["cells"]
    return {"in_pilot_area": True, "state": cfg.id, "name": cfg.name, "corridor": cfg.corridor,
            "jurisdiction": cfg.jurisdiction.model_dump(), "h3_cell": cell, "in_demo_grid": in_grid,
            "languages": cfg.languages, "default_language": cfg.default_language}


@router.get("/samples/photos")
def sample_photos():
    """CC-licensed Wikimedia Commons photos used as sample citizen reports (attribution included)."""
    d = settings.sample_data_dir / "photos"
    credits = json.loads((d / "ATTRIBUTION.json").read_text())["photos"]
    out = []
    for p in sorted(d.glob("*.jpg")):
        c = credits.get(p.name, {})
        out.append({"name": p.name, "url": f"/api/samples/photos/{p.name}", "is_sample": True,
                    "attribution": f"{c.get('author', 'unknown')} · {c.get('license', '')} · Wikimedia Commons",
                    "source_url": c.get("source_url"),
                    "note": "Sample photo (real CC-licensed photograph, not taken at the demo location)"})
    return out


@router.get("/samples/photos/{name}")
def sample_photo(name: str):
    path = settings.sample_data_dir / "photos" / name
    if "/" in name or ".." in name or not path.exists():
        raise not_found("sample photo", name)
    return FileResponse(path, media_type="image/jpeg")
