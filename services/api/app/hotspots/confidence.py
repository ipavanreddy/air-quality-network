"""Hotspot Confidence (PRD §13): transparent weighted model, every factor scored 0-100.

    Hotspot Confidence = Sensor anomaly x 35% + Satellite x 25% + Citizen reports x 25%
                         + Weather plausibility x 15%

Pure functions only: no I/O, easy to test and to explain on screen.
"""
from dataclasses import asdict, dataclass

MODEL_VERSION = "hotspot-confidence-v1"
WEIGHTS = {"sensor_anomaly": 0.35, "satellite": 0.25, "citizen_reports": 0.25, "weather": 0.15}
SOURCE_LAND_USES = {"industrial", "construction", "agricultural_burn_scar", "major_road"}


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class Factor:
    name: str
    score: float  # 0-100
    weight: float
    detail: str
    available: bool = True

    @property
    def contribution(self) -> float:
        return round(self.score * self.weight, 1)

    def to_dict(self) -> dict:
        return {**asdict(self), "score": round(self.score, 1), "contribution": self.contribution}


def sensor_anomaly(pm25: float | None, expected_pm25: float | None,
                   pm10: float | None = None, expected_pm10: float | None = None) -> Factor:
    """How far local (calibrated) PM is above the expected level from the nearest official station.
    Ratio 1.0 -> 0, ratio >= 2.0 -> 100. Uses the larger of the PM2.5 and PM10 ratios."""
    w = WEIGHTS["sensor_anomaly"]
    if pm25 is None or not expected_pm25:
        return Factor("sensor_anomaly", 0, w, "No sensor within 1.2 km: no ground evidence", False)
    ratios = [pm25 / expected_pm25]
    if pm10 is not None and expected_pm10:
        ratios.append(pm10 / expected_pm10)
    r = max(ratios)
    detail = (f"Local PM2.5 {pm25:.0f} ug/m3 vs {expected_pm25:.0f} expected "
              f"({(pm25 / expected_pm25 - 1) * 100:+.0f}%)")
    if len(ratios) > 1:
        detail += f"; PM10 {pm10:.0f} vs {expected_pm10:.0f}"
    return Factor("sensor_anomaly", clamp((r - 1) * 100), w, detail)


def satellite(no2_anomaly_pct: float | None, fire_count_upwind: int | None, aod: float | None) -> Factor:
    """Strongest of: NO2 anomaly (60% -> 100), upwind fires (20 -> 100), AOD (0.4 -> 0, 1.6 -> 100)."""
    w = WEIGHTS["satellite"]
    parts = {}
    if no2_anomaly_pct is not None:
        parts["NO2 column anomaly"] = (clamp(no2_anomaly_pct / 60 * 100), f"NO2 {no2_anomaly_pct:+.0f}% vs 30-day median")
    if fire_count_upwind is not None:
        parts["Upwind fires"] = (clamp(fire_count_upwind / 20 * 100), f"{fire_count_upwind} fire detections upwind (100 km)")
    if aod is not None:
        parts["Aerosol optical depth"] = (clamp((aod - 0.4) / 1.2 * 100), f"AOD {aod:.2f}")
    if not parts:
        return Factor("satellite", 0, w, "No recent satellite pass", False)
    best = max(parts.values(), key=lambda p: p[0])
    detail = "; ".join(p[1] for p in parts.values())
    return Factor("satellite", best[0], w, f"{detail} (strongest signal counts)")


def citizen_reports(reports: list[tuple[float, int, int]]) -> Factor:
    """reports: (ai_confidence 0-1, visual_severity 0-5, ring distance 0 = same cell, 1 = neighbour).
    Each verified report contributes confidence x severity/5 x proximity; combined as 1 - prod(1 - c)."""
    w = WEIGHTS["citizen_reports"]
    if not reports:
        return Factor("citizen_reports", 0, w, "No verified citizen reports nearby")
    miss = 1.0
    for conf, severity, ring in reports:
        proximity = 1.0 if ring == 0 else 0.6 if ring == 1 else 0.3
        miss *= 1 - clamp(conf * severity / 5 * proximity, 0, 1)
    n = len(reports)
    return Factor("citizen_reports", (1 - miss) * 100, w,
                  f"{n} verified report{'s' if n != 1 else ''} in/near cell")


def weather(wind_speed_ms: float | None, boundary_layer_m: float | None,
            upwind_source_consistent: bool) -> Factor:
    """Half stagnation (calm wind, shallow boundary layer -> pollution accumulates),
    half plausibility (a candidate source lies upwind / in the cell)."""
    w = WEIGHTS["weather"]
    if wind_speed_ms is None:
        return Factor("weather", 0, w, "No weather data", False)
    wind_f = clamp((4 - wind_speed_ms) / 3, 0, 1)
    if boundary_layer_m is None:
        stagnation = wind_f
        blh_txt = "boundary layer n/a"
    else:
        stagnation = 0.5 * wind_f + 0.5 * clamp((1000 - boundary_layer_m) / 800, 0, 1)
        blh_txt = f"boundary layer {boundary_layer_m:.0f} m"
    plaus = 1.0 if upwind_source_consistent else 0.2
    score = 100 * (0.5 * stagnation + 0.5 * plaus)
    detail = (f"Wind {wind_speed_ms:.1f} m/s, {blh_txt}; "
              f"{'candidate source upwind or in cell' if upwind_source_consistent else 'no candidate source upwind'}")
    return Factor("weather", score, w, detail)


def band(confidence: float) -> str:
    return "High" if confidence >= 75 else "Medium" if confidence >= 50 else "Low"


def combine(factors: list[Factor]) -> dict:
    total = round(sum(f.score * f.weight for f in factors), 1)
    return {
        "confidence": total,
        "band": band(total),
        "factors": [f.to_dict() for f in factors],
        "evidence_types": sum(1 for f in factors if f.available and f.score > 0),
        "model_version": MODEL_VERSION,
    }


def bearing_deg(lat0: float, lon0: float, lat: float, lon: float) -> float:
    import math

    x = (lon - lon0) * 111.32 * math.cos(math.radians(lat0))
    y = (lat - lat0) * 110.57
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)
