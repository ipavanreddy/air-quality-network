"""AI adapters: Gemini when configured, clearly-labelled fixtures/templates otherwise.

Every function returns (result, provenance) where provenance always carries model_name,
model_version, prompt_version and `mode` in {"gemini", "demo_fixture", "fallback"}.
"""
import hashlib
import json
import re
from datetime import UTC, datetime

from app.ai.schemas import (
    ActionBrief,
    EvidenceItem,
    HealthAdvisory,
    LikelySource,
    PhotoVerification,
    RecommendedAction,
    TranslatedAdvisory,
)
from app.core import integrations
from app.core.samples import load
from app.hotspots.sources import rank_sources
from app.localization.google_cloud import LANGUAGE_NAMES

FIXTURE_MODEL = "demo-fixture"
FIXTURE_VERSION = "fixture-v1"


def _fixture_prov(prompt_version: str, note: str, mode: str = "demo_fixture") -> dict:
    return {"model_name": FIXTURE_MODEL, "model_version": FIXTURE_VERSION, "prompt_version": prompt_version,
            "generated_at": datetime.now(UTC).isoformat(), "mode": mode, "note": note}


def _fill(template: str, **values: str) -> str:
    for k, v in values.items():
        template = template.replace("{" + k + "}", v)
    return template


def _gemini(prompt_name: str, prompt_version: str, values: dict, schema, parts=None):
    from app.ai.gemini import generate_structured, load_prompt

    prompt = _fill(load_prompt(prompt_name, prompt_version), **values)
    result, prov = generate_structured(prompt, schema, f"{prompt_name}_{prompt_version}", parts=parts)
    integrations.clear_error("gemini")
    return result, {**prov.model_dump(mode="json"), "mode": "gemini", "note": None}


# --- photo verification (FR-02) -------------------------------------------------------------
def verify_photo(image: bytes, mime_type: str, context: dict, scenario_source: str
                 ) -> tuple[PhotoVerification, dict]:
    pv = "photo_verification_v1"
    if len(image) < 1024 or not mime_type.startswith("image/"):
        v = PhotoVerification(is_pollution_event=False, source_type="other_unknown", visual_severity=0,
                              observed_indicators=[], confidence=0.0, image_quality_ok=False,
                              requires_human_review=True,
                              explanation="Image too small or not an image; please retake the photo.")
        return v, _fixture_prov(pv, "Rejected by pre-check before AI (size/type)", "precheck")

    if integrations.enabled("gemini"):
        try:
            from google.genai import types

            return _gemini("photo_verification", "v1", {"context_json": json.dumps(context, indent=1)},
                           PhotoVerification, parts=[types.Part.from_bytes(data=image, mime_type=mime_type)])
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("gemini", exc)

    fixtures = load("ai_fixtures/photo_verification.json", replay=False)
    sha = hashlib.sha256(image).hexdigest()
    if sha in fixtures["by_sha256"]:
        hit = fixtures["by_sha256"][sha]
        return (PhotoVerification.model_validate(hit["verification"]),
                _fixture_prov(pv, f"Demo mode: stored fixture result for sample photo {hit['file']}"))
    data = dict(fixtures["default_by_source"][scenario_source])
    data["requires_human_review"] = True
    data["explanation"] = ("Demo mode: image NOT analysed (no Gemini key). Fixture result for this "
                           "location's demo scenario; officer review required.")
    return PhotoVerification.model_validate(data), _fixture_prov(pv, "Demo mode: image not analysed")


# --- action brief (FR-06, FR-08) ------------------------------------------------------------
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def grounding_warnings(brief: ActionBrief, bundle: dict) -> list[str]:
    """Every number cited in evidence must exist in the evidence bundle (PRD §32 validation)."""
    bundle_nums = [float(n) for n in _NUM.findall(json.dumps(bundle))]
    warnings = []
    for ev in brief.evidence:
        for n in _NUM.findall(ev.value):
            x = float(n)
            if abs(x) < 1:
                continue
            if not any(abs(abs(x) - abs(b)) <= max(0.51, 0.01 * abs(b)) for b in bundle_nums):
                warnings.append(f"'{ev.signal}' value {n} not found in the evidence bundle")
    return warnings


def enforce_rules(brief: ActionBrief, rules: list[dict]) -> list[str]:
    allowed = {r["id"]: r["action"] for r in rules}
    dropped = [a.action_id for a in brief.recommended_actions if a.action_id not in allowed]
    brief.recommended_actions = [a for a in brief.recommended_actions if a.action_id in allowed]
    brief.requires_human_review = True
    return [f"Dropped action '{d}' (not in jurisdiction action rules)" for d in dropped]


def _pick_actions(rules: list[dict], sources: list[dict], severe: bool) -> list[RecommendedAction]:
    out = []
    for i, src in enumerate(sources[:2]):
        for r in rules:
            if src["type"] in r["applies_to"] and r["stage"] == "any" and r["id"] not in {a.action_id for a in out}:
                out.append(RecommendedAction(action_id=r["id"], action=r["action"],
                                             priority="high" if i == 0 and not out else "medium"))
    if severe:
        for r in rules:
            if r["stage"] == "severe" and ("*" in r["applies_to"] or sources and sources[0]["type"] in r["applies_to"]):
                out.append(RecommendedAction(action_id=r["id"], action=r["action"], priority="medium"))
    return out[:4]


def _template_brief(bundle: dict, rules: list[dict]) -> ActionBrief:
    sources = rank_sources(bundle)
    hs = bundle["hotspot"]
    sensor, sat, wx = bundle.get("sensor") or {}, bundle.get("satellite") or {}, bundle.get("weather") or {}
    evidence = []
    if sensor.get("pm25_calibrated") is not None:
        evidence.append(EvidenceItem(
            signal="Local PM2.5 (calibrated low-cost, indicative)",
            value=f"{sensor['pm25_calibrated']} ug/m3 vs {sensor['expected_pm25']} at {sensor['station_name']}",
            source=sensor["source"], observed=sensor["observed_at"]))
    if sat.get("no2_column_anomaly_pct") is not None:
        evidence.append(EvidenceItem(signal="NO2 column anomaly", value=f"{sat['no2_column_anomaly_pct']:+}%",
                                     source=sat["no2_source"], observed=sat["no2_observed_at"]))
    if sat.get("fire_count_upwind_100km") is not None:
        evidence.append(EvidenceItem(signal="Active fires upwind (100 km)", value=str(sat["fire_count_upwind_100km"]),
                                     source=sat["fire_source"], observed=sat["fire_observed_at"]))
    if sat.get("aod") is not None:
        evidence.append(EvidenceItem(signal="Aerosol optical depth", value=str(sat["aod"]),
                                     source=sat["aod_source"], observed=sat["aod_observed_at"]))
    if wx:
        blh = wx.get("boundary_layer_m")
        evidence.append(EvidenceItem(
            signal="Wind / mixing", value=f"{wx['wind_speed_ms']} m/s from {wx['wind_dir_deg']} deg"
                                          + (f", boundary layer {blh} m" if blh is not None else ""),
            source=wx["source"], observed=wx["observed_at"]))
    for r in bundle.get("citizen_reports", []):
        evidence.append(EvidenceItem(signal=f"Citizen photo report ({r['source_type']})",
                                     value=f"AI confidence {r['confidence']}, severity {r['visual_severity']}/5",
                                     source="Citizen report + AI photo verification", observed=r["created_at"]))
    conf = hs["confidence"]
    risk = "severe" if conf >= 85 else "high" if conf >= 70 else "medium" if conf >= 50 else "low"
    top = sources[0]["type"].replace("_", " ") if sources else "unknown source"
    fc = bundle.get("forecast") or {}
    h24 = next((h for h in fc.get("horizons", []) if h["horizon_hours"] == 24), None)
    outlook = (f"Next 24h: {h24['category']} (PM2.5 ~{h24['pm25_expected']} ug/m3, range "
               f"{h24['pm25_low']}-{h24['pm25_high']}); drivers: {', '.join(h24['drivers'])}."
               if h24 else "Forecast unavailable.")
    uncertainties = ["Low-cost sensor values are calibrated but indicative."]
    if sensor.get("station_distance_km"):
        uncertainties.append(f"Nearest official station is {sensor['station_distance_km']} km away.")
    if wx.get("boundary_layer_m") is None:
        uncertainties.append("Boundary-layer height unavailable.")
    uncertainties.append("Satellite signals are from the latest available pass, not real-time.")
    uncertainties.append("Attribution is a likely source to guide inspection, not a confirmed polluter.")
    return ActionBrief(
        summary=(f"Likely {top} affecting {len(hs['h3_cells'])} grid cell(s) in {bundle['area']}. "
                 f"Hotspot Confidence {conf:.0f}/100; recommended inspection below."),
        risk_level=risk,
        likely_sources=[LikelySource(type=s["type"], confidence=s["confidence"],
                                     rationale="Rule-based prior from satellite, land-use, sensor and report evidence")
                        for s in sources],
        evidence=evidence,
        forecast_outlook=outlook,
        recommended_actions=_pick_actions(rules, sources, risk == "severe"),
        uncertainties=uncertainties,
        confidence=round(min(0.95, conf / 100 * (sources[0]["confidence"] + 0.5) if sources else 0.3), 2),
        requires_human_review=True,
    )


def action_brief(bundle: dict, rules: list[dict], jurisdiction_name: str) -> tuple[ActionBrief, dict]:
    pv = "action_brief_v1"
    if integrations.enabled("gemini"):
        try:
            brief, prov = _gemini("action_brief", "v1", {
                "bundle_json": json.dumps(bundle, indent=1, default=str),
                "rules_json": json.dumps(rules, indent=1),
                "jurisdiction_name": jurisdiction_name,
            }, ActionBrief)
            warnings = enforce_rules(brief, rules) + grounding_warnings(brief, bundle)
            prov["validation_warnings"] = warnings
            return brief, prov
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("gemini", exc)
    brief = _template_brief(bundle, rules)
    prov = _fixture_prov(pv, "Demo mode: deterministic templated brief built from the evidence bundle "
                             "(no Gemini key); numbers are copied from observed data")
    prov["validation_warnings"] = grounding_warnings(brief, bundle)
    return brief, prov


# --- health advisory + translation (FR-09) --------------------------------------------------
def _templates() -> dict:
    return load("ai_fixtures/advisory_templates.json", replay=False)


def _template_advisory(lang: str, place: str, category: str, pm: float) -> dict:
    t = _templates()
    bucket = t["bucket_by_category"].get(category, "poor")
    tpl = t["templates"][bucket][lang]
    values = {"place": place, "category": t["category_names"][lang].get(category, category), "pm": f"{pm:.0f}"}
    return {
        "headline": _fill(tpl["headline"], **values),
        "summary": _fill(tpl["summary"], **values),
        "protective_steps": [_fill(s, **values) for s in tpl["protective_steps"]],
        "sensitive_groups": _fill(tpl["sensitive_groups"], **values),
    }


def health_advisory(context: dict) -> tuple[HealthAdvisory, dict]:
    if integrations.enabled("gemini"):
        try:
            return _gemini("health_advisory", "v1", {"place": context["place"],
                                                     "context_json": json.dumps(context, indent=1)}, HealthAdvisory)
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("gemini", exc)
    base = _template_advisory("en", context["place"], context["category_now"], context["pm25_now"])
    return (HealthAdvisory(category=context["category_now"], **base),
            _fixture_prov("health_advisory_v1", "Demo mode: advisory template (no Gemini key)"))


def translate_advisory(adv: HealthAdvisory, lang: str, context: dict, base_mode: str) -> tuple[dict, dict]:
    """Localise once-generated advisory. Cloud Translation -> Gemini -> template (demo)."""
    payload = adv.model_dump(exclude={"category"})
    if lang == "en":
        return payload, {"engine": "source", "mode": "real" if base_mode == "gemini" else "demo"}
    if integrations.enabled("translation"):
        try:
            from app.localization.google_cloud import (
                translate_texts,
                translation_engine,
            )

            texts = [payload["headline"], payload["summary"], payload["sensitive_groups"], *payload["protective_steps"]]
            out = translate_texts(texts, lang)
            integrations.clear_error("translation")
            return ({"headline": out[0], "summary": out[1], "sensitive_groups": out[2],
                     "protective_steps": out[3:]}, {"engine": translation_engine(), "mode": "real"})
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("translation", exc)
    if integrations.enabled("gemini") and base_mode == "gemini":
        try:
            res, prov = _gemini("translate_advisory", "v1", {
                "language_name": LANGUAGE_NAMES[lang], "language_code": lang,
                "advisory_json": json.dumps(payload, ensure_ascii=False)}, TranslatedAdvisory)
            return res.model_dump(), {"engine": "gemini", "mode": "real", **prov}
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("gemini", exc)
    return (_template_advisory(lang, context["place"], context["category_now"], context["pm25_now"]),
            {"engine": "template", "mode": "demo", "note": "Pre-written demo translation template"})
