"""Citizen photo reports (FR-01) + Gemini multimodal verification (FR-02)."""
import uuid
from datetime import timedelta

import h3

from app.ai import services as ai
from app.config import settings
from app.core.engine import H3_RES, Engine, iso_now
from app.core.samples import load, now
from app.geo import maps
from app.interop.adapters import configs, get_config
from app.reports.storage import save_photo

SCENARIO_SOURCE = {"delhi-ncr": "industrial_emission", "punjab": "crop_residue_burning",
                   "maharashtra": "construction_dust"}

# Pre-existing SAMPLE reports so Punjab + Maharashtra have live hotspots when the demo starts.
SEED_REPORTS = [
    {"state": "punjab", "photo": "crop_burning_field.jpg", "offset": (0.0, 0.0), "minutes_ago": 40,
     "description": "Stubble fire next to the village road, lots of smoke (sample report)", "language": "pa"},
    {"state": "maharashtra", "photo": "construction_dust_site.jpg", "offset": (0.0, 0.0), "minutes_ago": 55,
     "description": "Dust cloud from building site, no water sprinkling (sample report)", "language": "en"},
]


def verification_status(v: dict) -> str:
    if not v["is_pollution_event"] or not v["image_quality_ok"]:
        return "rejected"
    if v["requires_human_review"] or v["confidence"] < 0.6:
        return "needs_review"
    return "verified"


def create_report(engine: Engine, *, photo: bytes, mime_type: str, lat: float, lon: float,
                  description: str = "", language: str = "en", reporter_id: str = "anonymous",
                  sample_seed: bool = False, created_at: str | None = None) -> dict:
    cfg, dist = engine.nearest_config(lat, lon)
    report_id = f"RP-{uuid.uuid4().hex[:8].upper()}"
    cell = h3.latlng_to_cell(lat, lon, H3_RES)
    created_at = created_at or iso_now()
    photo_url = save_photo(report_id, photo, mime_type)
    report = {
        "report_id": report_id,
        "reporter_id": reporter_id,  # pseudonymous id from the client
        "photo_url": photo_url,
        "photo_endpoint": f"/api/reports/{report_id}/photo",
        "location": {"lat": lat, "lon": lon},
        "address": None if sample_seed else maps.reverse(lat, lon),
        "h3_cell": cell,
        "state": cfg.id if cfg else None,
        "jurisdiction_id": cfg.jurisdiction.id if cfg else None,
        "created_at": created_at,
        "description": description,
        "language": language,
        "is_sample": sample_seed,
    }
    if cfg is None:
        report.update({"status": "outside_pilot_area", "verification": None, "provenance": None,
                       "note": f"Nearest pilot area is {dist:.0f} km away"})
        return engine.store.put("reports", report_id, report)

    ctx = engine.context(cfg.id)
    before = engine.score_cell(ctx, cell) if cell in ctx["cells"] else None
    context = {"location": {"lat": lat, "lon": lon, "h3_cell": cell, "area": f"{cfg.corridor}, {cfg.name}"},
               "reported_at": created_at,
               "nearby_land_use": ctx["land_use"].get(cell, "unknown"),
               "citizen_description": description[:300]}
    verification, prov = ai.verify_photo(photo, mime_type, context, SCENARIO_SOURCE[cfg.id])
    v = verification.model_dump()
    report.update({
        "verification": v,
        "provenance": prov,
        "model_name": prov["model_name"], "model_version": prov["model_version"],
        "prompt_version": prov["prompt_version"],
        "is_pollution_event": v["is_pollution_event"],
        "source_type": v["source_type"],
        "visual_severity": v["visual_severity"],
        "confidence": v["confidence"],
        "status": verification_status(v),
    })
    engine.store.put("reports", report_id, report)

    hotspots = engine.detect(cfg.id)
    after_ctx = engine.context(cfg.id)
    after = engine.score_cell(after_ctx, cell) if cell in after_ctx["cells"] else None
    hs = next((h for h in hotspots if cell in h["h3_cells"]), None)
    report["impact"] = {
        "cell_confidence_before": before["confidence"] if before else None,
        "cell_confidence_after": after["confidence"] if after else None,
        "hotspot_id": hs["hotspot_id"] if hs else None,
        "alert_id": hs["alert_id"] if hs else None,
        "threshold": cfg.hotspot_threshold,
    }
    report["status_timeline"] = [
        {"at": created_at, "event": "submitted"},
        {"at": iso_now(), "event": f"ai_{report['status']}"},
    ] + ([{"at": iso_now(), "event": "linked_to_hotspot_and_routed_to_officer"}] if hs else [])
    return engine.store.put("reports", report_id, report)


def seed_samples(engine: Engine) -> None:
    """Idempotently add the labelled sample reports and run detection for every state."""
    existing = {(r["state"], r.get("seed_photo")) for r in engine.store.all("reports") if r.get("is_sample")}
    fixtures = load("ai_fixtures/photo_verification.json", replay=False)["by_sha256"]
    for seed in SEED_REPORTS:
        if (seed["state"], seed["photo"]) in existing:
            continue
        cfg = get_config(seed["state"])
        photo = (settings.sample_data_dir / "photos" / seed["photo"]).read_bytes()
        assert any(f["file"] == seed["photo"] for f in fixtures.values())
        r = create_report(engine, photo=photo, mime_type="image/jpeg", lat=cfg.center[0] + seed["offset"][0],
                          lon=cfg.center[1] + seed["offset"][1], description=seed["description"],
                          language=seed["language"], reporter_id="sample-seed", sample_seed=True,
                          created_at=(now() - timedelta(minutes=seed["minutes_ago"])).isoformat())
        r["seed_photo"] = seed["photo"]
        engine.store.put("reports", r["report_id"], r)
    for cid in configs():
        engine.detect(cid)

