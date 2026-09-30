"""Deterministic likely-source prior from the evidence bundle.

Used (a) to build the demo-mode action brief and (b) as a sanity cross-check shown next to the
Gemini attribution. Always 'likely' sources to guide inspection, never an accusation.
"""
SOURCE_TYPES = ["crop_residue_burning", "waste_burning", "industrial_emission", "construction_dust",
                "traffic", "other_unknown"]


def rank_sources(bundle: dict) -> list[dict]:
    sat = bundle.get("satellite") or {}
    sensor = bundle.get("sensor") or {}
    land = bundle.get("land_use") or {}
    reports = bundle.get("citizen_reports") or []
    upwind = set(land.get("upwind_land_uses", [])) | {land.get("cell_land_use")}

    s = dict.fromkeys(SOURCE_TYPES, 0.05)
    fires = sat.get("fire_count_upwind_100km") or 0
    no2 = sat.get("no2_column_anomaly_pct") or 0
    pm25, pm10 = sensor.get("pm25_calibrated"), sensor.get("pm10")

    s["crop_residue_burning"] += min(fires / 20, 1.0) * 0.8 + (0.2 if "agricultural_burn_scar" in upwind else 0)
    s["industrial_emission"] += min(max(no2, 0) / 60, 1.0) * 0.6 + (0.3 if "industrial" in upwind else 0)
    if pm25 and pm10 and pm10 / pm25 >= 2.2:
        s["construction_dust"] += 0.4
    s["construction_dust"] += 0.4 if "construction" in upwind else 0
    s["traffic"] += 0.25 if "major_road" in upwind else 0
    s["traffic"] += min(max(no2, 0) / 60, 1.0) * 0.15
    for r in reports:
        if r.get("source_type") in s:
            s[r["source_type"]] += 0.3 * (r.get("confidence") or 0)

    total = sum(s.values())
    ranked = sorted(({"type": k, "confidence": round(v / total, 2)} for k, v in s.items()),
                    key=lambda x: -x["confidence"])
    return [r for r in ranked if r["confidence"] >= 0.08][:3]
