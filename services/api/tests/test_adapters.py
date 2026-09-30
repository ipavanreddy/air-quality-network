import hashlib
import json

import httpx

from app.ai import services as ai
from app.ai.schemas import SCHEMA_DIR, SCHEMAS, ActionBrief
from app.config import settings
from app.core import integrations
from app.core.samples import load
from app.forecasting.model import aqi_category, forecast, trained
from app.geospatial_gee import provider as geo
from app.interop.adapters import configs, get_config, map_feed_record
from app.sensors_calibration import cpcb
from app.sensors_calibration.calibration import calibrate_pm25
from app.sensors_calibration.provider import lowcost_observations, official_station


def test_at_least_two_state_configs_with_jurisdictions():
    cfgs = configs()
    assert {"delhi-ncr", "punjab", "maharashtra"} <= set(cfgs)
    assert len({c.jurisdiction.id for c in cfgs.values()}) == len(cfgs)
    assert cfgs["punjab"].cross_boundary_neighbours[0].jurisdiction_id == "DL-DPCC"


def test_state_feed_formats_map_to_same_canonical_observation():
    for cid in ("delhi-ncr", "punjab", "maharashtra"):
        cfg = get_config(cid)
        rec = load(f"{cid}/sensors_lowcost_feed.json")["records"][0]
        obs = map_feed_record(cfg, rec)
        assert obs.sensor_id.startswith(cfg.state_code)
        assert obs.timestamp.tzinfo is not None
        assert obs.pm25_raw > 0 and obs.humidity is not None


def test_calibration_reduces_humid_readings_and_labels_indicative():
    assert calibrate_pm25(200, 30) < 200
    assert calibrate_pm25(200, 90) < calibrate_pm25(200, 50)
    assert calibrate_pm25(200, None) == 200
    obs = lowcost_observations(get_config("delhi-ncr"))
    assert all(o["indicative"] and o["is_simulated"] for o in obs)
    assert all(o["pm25_calibrated"] <= o["pm25_raw"] for o in obs)


def test_sample_data_is_labelled():
    for cid in configs():
        for name in ("satellite_h3.json", "sensors_lowcost_feed.json", "official_stations.json", "weather.json"):
            meta = load(f"{cid}/{name}")["metadata"]
            assert meta["is_sample"] is True
            for key in ("source", "reference_timestamp", "dataset_version", "geographic_scope"):
                assert meta[key]


def test_cpcb_client_pivots_rows_and_picks_nearest(monkeypatch):
    rows = [
        {"station": "ITO, Delhi - CPCB", "latitude": "28.628", "longitude": "77.241", "pollutant_id": "PM2.5",
         "avg_value": "187", "last_update": "05-11-2026 03:00:00"},
        {"station": "ITO, Delhi - CPCB", "latitude": "28.628", "longitude": "77.241", "pollutant_id": "PM10",
         "avg_value": "301", "last_update": "05-11-2026 03:00:00"},
        {"station": "Far station", "latitude": "28.9", "longitude": "77.0", "pollutant_id": "PM2.5",
         "avg_value": "90", "last_update": "05-11-2026 03:00:00"},
        {"station": "Broken", "latitude": "NA", "longitude": "NA", "pollutant_id": "PM2.5", "avg_value": "NA"},
    ]
    seen = {}

    def handler(request: httpx.Request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"records": rows})

    monkeypatch.setattr(settings, "data_gov_in_api_key", "k")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    st = cpcb.fetch_nearest_station("DL", 28.63, 77.29, client=client)
    assert seen["params"]["filters[state]"] == "Delhi"
    assert st["name"] == "ITO, Delhi - CPCB"
    assert st["pm25"] == 187 and st["pm10"] == 301 and st["is_sample"] is False
    assert st["observed_at"].startswith("2026-11-05T03:00")


def test_demo_mode_falls_back_to_labelled_samples():
    assert integrations.status()["demo_mode"] is True
    assert not integrations.enabled("gemini") and not integrations.enabled("earth_engine")
    cfg = get_config("punjab")
    st = official_station(cfg)
    assert st["is_sample"] is True
    layers = geo.layers(cfg, [])
    assert layers["meta"]["mode"] == "sample"
    assert all(r["is_sample"] for r in layers["satellite"].values())


def test_earth_engine_failure_is_recorded_as_fallback(monkeypatch):
    monkeypatch.setitem(integrations._REGISTRY["earth_engine"].__dict__, "configured", True)
    from app.geospatial_gee import earth_engine

    def boom(*_a, **_k):
        raise RuntimeError("EE not initialised")

    monkeypatch.setattr(earth_engine, "fetch_weather", boom)
    geo._cache.clear()
    out = geo.layers(get_config("delhi-ncr"), [])
    assert out["meta"]["mode"] == "sample"
    item = next(i for i in integrations.status()["integrations"] if i["name"] == "earth_engine")
    assert item["mode"] == "fallback" and "EE not initialised" in item["last_error"]
    integrations.clear_error("earth_engine")


def test_json_schemas_in_sync():
    for name, model in SCHEMAS.items():
        on_disk = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text())
        assert on_disk == model.model_json_schema(), f"run `uv run python -m app.ai.schemas` ({name})"


def test_photo_fixtures_and_irrelevant_image_flagged():
    photos = settings.sample_data_dir / "photos"
    v, prov = ai.verify_photo((photos / "clear_sky_park.jpg").read_bytes(), "image/jpeg", {}, "industrial_emission")
    assert v.is_pollution_event is False
    assert prov["mode"] == "demo_fixture" and prov["prompt_version"] == "photo_verification_v1"
    v, _ = ai.verify_photo((photos / "crop_burning_field.jpg").read_bytes(), "image/jpeg", {}, "industrial_emission")
    assert v.source_type == "crop_residue_burning" and v.confidence > 0.8
    v, prov = ai.verify_photo(b"tiny", "image/png", {}, "industrial_emission")
    assert v.image_quality_ok is False and v.requires_human_review
    unknown = hashlib.sha256(b"x" * 5000).hexdigest()
    assert unknown not in load("ai_fixtures/photo_verification.json", replay=False)["by_sha256"]
    v, prov = ai.verify_photo(b"x" * 5000, "image/jpeg", {}, "construction_dust")
    assert v.requires_human_review and "NOT analysed" in v.explanation


def _brief(value: str, action_id: str = "DL-STACK-MONITOR") -> ActionBrief:
    return ActionBrief.model_validate({
        "summary": "s", "risk_level": "high",
        "likely_sources": [{"type": "industrial_emission", "confidence": 0.6, "rationale": "r"}],
        "evidence": [{"signal": "NO2", "value": value, "source": "S5P", "observed": "t"}],
        "forecast_outlook": "", "recommended_actions": [{"action_id": action_id, "action": "a", "priority": "high"}],
        "uncertainties": [], "confidence": 0.6, "requires_human_review": False})


def test_brief_validation_grounding_and_action_rules():
    bundle = {"satellite": {"no2_column_anomaly_pct": 42.0}}
    assert ai.grounding_warnings(_brief("+42%"), bundle) == []
    assert ai.grounding_warnings(_brief("+97%"), bundle)  # invented number flagged
    b = _brief("+42%", action_id="MADE-UP")
    rules = [r.model_dump() for r in get_config("delhi-ncr").action_rules]
    warnings = ai.enforce_rules(b, rules)
    assert b.recommended_actions == [] and warnings and b.requires_human_review is True


def test_forecast_model_and_backtest():
    m = trained()
    for cid in ("delhi-ncr", "punjab", "maharashtra"):
        for h in (24, 48, 72):
            assert m["metrics"][cid][h]["test_days"] == 20
    steps = load("delhi-ncr/weather.json")["forecast"]["steps"]
    fc = forecast("delhi-ncr", "igp-smog-forecast-v1", 200, steps)
    assert [h["horizon_hours"] for h in fc["horizons"]] == [24, 48, 72]
    for h in fc["horizons"]:
        assert h["pm25_low"] <= h["pm25_expected"] <= h["pm25_high"]
    assert aqi_category(25) == "Good" and aqi_category(300) == "Severe" and aqi_category(110) == "Poor"
