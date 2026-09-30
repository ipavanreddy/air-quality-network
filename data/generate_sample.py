"""Deterministic generator for VayuDrishti demo/sample data (PRD §42).

Everything written here is SAMPLE / SIMULATED data, labelled as such in every file's
`metadata` block. It is NOT real CPCB, satellite or weather data. The real integrations
(`services/api/app/sensors_calibration/cpcb.py`, `services/api/app/geospatial_gee/earth_engine.py`)
replace these files when their keys are configured.

Run (uses the API venv because it needs `h3`):
    cd services/api && uv run python ../../data/generate_sample.py

Output is byte-for-byte reproducible (fixed seed, fixed reference timestamp).
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import h3

DATASET_VERSION = "sample-2026.11-v1"
REFERENCE_TS = datetime.fromisoformat("2026-11-05T03:00:00+05:30")
H3_RES = 8
GRID_K = 3
SEED = 20261105
KAPPA = 0.3  # humidity growth factor used to SIMULATE low-cost sensor over-reading

OUT = Path(__file__).resolve().parent / "sample"
GENERATOR = "data/generate_sample.py"

# --- scenario definitions (PRD §43) --------------------------------------------------------
SCENARIOS = {
    "delhi-ncr": {
        "scope": "Delhi NCR - East Delhi industrial + traffic corridor (sample)",
        "center": (28.6280, 77.2950),
        "background_pm25": 110.0,
        "peak_pm25": 185.0,
        "sigma_km": 1.1,
        "plume_to_deg": 110.0,  # wind FROM 290 blows TOWARD 110
        "weather": {"wind_speed_ms": 1.1, "wind_dir_deg": 290, "humidity": 78, "temperature_c": 12.0,
                    "boundary_layer_m": 220, "rain_mm": 0.0},
        "no2_peak_pct": 42.0, "no2_bg_pct": 8.0, "aod_peak": 1.2, "aod_bg": 0.8, "fire_count": 0,
        "land_use_default": "residential",
        "land_use_rules": [("industrial", 250, 330, 1, 2), ("major_road", 60, 120, 1, 3)],
        "center_land_use": "industrial",
        "station": {"station_id": "DL-ITO-SAMPLE", "name": "ITO, Delhi (sample station)",
                    "lat": 28.6285, "lon": 77.2410, "pm25": 112.0, "pm10": 230.0, "no2": 68.0,
                    "pm25_30d_median": 104.0},
        "raw_format": "delhi",
        "sensor_prefix": "DL-LC",
        "forecast": {"vent": [240, 210, 380], "fire": [5, 9, 6], "rain": [0, 0, 0.5]},
        "history": {"base": 120.0, "fire_scale": 1.2},
    },
    "punjab": {
        "scope": "Punjab - Sangrur district village cluster (sample)",
        "center": (30.2458, 75.8421),
        "background_pm25": 120.0,
        "peak_pm25": 115.0,
        "sigma_km": 1.4,
        "plume_to_deg": 135.0,
        "weather": {"wind_speed_ms": 3.2, "wind_dir_deg": 315, "humidity": 55, "temperature_c": 17.0,
                    "boundary_layer_m": 450, "rain_mm": 0.0},
        "no2_peak_pct": 12.0, "no2_bg_pct": 4.0, "aod_peak": 1.6, "aod_bg": 1.0, "fire_count": 38,
        "land_use_default": "agricultural",
        "land_use_rules": [("agricultural_burn_scar", 280, 350, 1, 3)],
        "center_land_use": "agricultural",
        "station": {"station_id": "PB-PATIALA-SAMPLE", "name": "Patiala (sample station)",
                    "lat": 30.3398, "lon": 76.3869, "pm25": 118.0, "pm10": 205.0, "no2": 22.0,
                    "pm25_30d_median": 96.0},
        "raw_format": "punjab",
        "sensor_prefix": "PB-LC",
        "forecast": {"vent": [900, 700, 820], "fire": [42, 55, 35], "rain": [0, 0, 0]},
        "history": {"base": 95.0, "fire_scale": 1.0},
    },
    "maharashtra": {
        "scope": "Maharashtra - Mumbai-Pune corridor, Panvel (sample)",
        "center": (18.9894, 73.1175),
        "background_pm25": 58.0,
        "peak_pm25": 62.0,
        "sigma_km": 0.9,
        "plume_to_deg": 70.0,
        "weather": {"wind_speed_ms": 2.5, "wind_dir_deg": 250, "humidity": 70, "temperature_c": 27.0,
                    "boundary_layer_m": 600, "rain_mm": 0.0},
        "no2_peak_pct": 15.0, "no2_bg_pct": 5.0, "aod_peak": 0.95, "aod_bg": 0.55, "fire_count": 0,
        "land_use_default": "urban",
        "land_use_rules": [("construction", 200, 290, 1, 2)],
        "center_land_use": "construction",
        "station": {"station_id": "MH-NAVIMUMBAI-SAMPLE", "name": "Navi Mumbai (sample station)",
                    "lat": 19.0330, "lon": 73.0297, "pm25": 60.0, "pm10": 118.0, "no2": 31.0,
                    "pm25_30d_median": 52.0},
        "raw_format": "maharashtra",
        "sensor_prefix": "MH-LC",
        "forecast": {"vent": [1500, 1650, 1400], "fire": [0, 0, 0], "rain": [0, 0, 0]},
        "history": {"base": 55.0, "fire_scale": 0.0},
    },
}


def meta(scope: str, source: str, *, synthetic: bool = True, notes: str = "") -> dict:
    return {
        "source": source,
        "reference_timestamp": REFERENCE_TS.isoformat(),
        "dataset_version": DATASET_VERSION,
        "geographic_scope": scope,
        "is_sample": True,
        "is_synthetic": synthetic,
        "generator": GENERATOR,
        "notes": notes,
    }


def iso(dt: datetime) -> str:
    return dt.isoformat()


def local_xy_km(lat0: float, lon0: float, lat: float, lon: float) -> tuple[float, float]:
    """Equirectangular projection: x east, y north, in km."""
    x = (lon - lon0) * 111.32 * math.cos(math.radians(lat0))
    y = (lat - lat0) * 110.57
    return x, y


def bearing_deg(lat0: float, lon0: float, lat: float, lon: float) -> float:
    x, y = local_xy_km(lat0, lon0, lat, lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def plume(sc: dict, lat: float, lon: float, peak: float, bg: float) -> float:
    """Gaussian plume elongated along the downwind direction."""
    lat0, lon0 = sc["center"]
    x, y = local_xy_km(lat0, lon0, lat, lon)
    theta = math.radians(sc["plume_to_deg"])
    along = x * math.sin(theta) + y * math.cos(theta)
    cross = x * math.cos(theta) - y * math.sin(theta)
    s = sc["sigma_km"]
    along_s = s * (2.0 if along > 0 else 0.8)
    return bg + peak * math.exp(-(along**2) / (2 * along_s**2) - (cross**2) / (2 * s**2))


def humidity_growth(rh_pct: float) -> float:
    rh = min(rh_pct, 95) / 100
    return 1 + (KAPPA / 1.65) / (-1 + 1 / rh)


def angle_in(b: float, lo: float, hi: float) -> bool:
    return lo <= b <= hi if lo <= hi else (b >= lo or b <= hi)


# --- per-scenario generation ---------------------------------------------------------------
def gen_grid_layers(state: str, sc: dict, rng: random.Random) -> tuple[list, list]:
    lat0, lon0 = sc["center"]
    center = h3.latlng_to_cell(lat0, lon0, H3_RES)
    cells = sorted(h3.grid_disk(center, GRID_K))
    satellite, land = [], []
    for cell in cells:
        lat, lon = h3.cell_to_latlng(cell)
        ring = h3.grid_distance(center, cell)
        b = bearing_deg(lat0, lon0, lat, lon)
        lu = sc["land_use_default"]
        if cell == center:
            lu = sc["center_land_use"]
        for name, lo, hi, rmin, rmax in sc["land_use_rules"]:
            if rmin <= ring <= rmax and angle_in(b, lo, hi):
                lu = name
        land.append({"h3_cell": cell, "state": state, "land_use": lu})
        no2 = plume(sc, lat, lon, sc["no2_peak_pct"] - sc["no2_bg_pct"], sc["no2_bg_pct"])
        aod = plume(sc, lat, lon, sc["aod_peak"] - sc["aod_bg"], sc["aod_bg"])
        satellite.append({
            "h3_cell": cell,
            "state": state,
            "no2_column_umol_m2": round(95 * (1 + no2 / 100) + rng.uniform(-3, 3), 1),
            "no2_column_anomaly_pct": round(no2 + rng.uniform(-1.5, 1.5), 1),
            "no2_source": "Sentinel-5P TROPOMI L3 NO2 (sample extract)",
            "no2_observed_at": iso(REFERENCE_TS - timedelta(hours=14)),
            "aod": round(aod + rng.uniform(-0.03, 0.03), 2),
            "aod_source": "MODIS MAIAC AOD 0.47um (sample extract)",
            "aod_observed_at": iso(REFERENCE_TS - timedelta(hours=16)),
            "fire_count_upwind_100km": sc["fire_count"] + (rng.randint(0, 2) if sc["fire_count"] else 0),
            "fire_source": "NASA FIRMS VIIRS active fire (sample extract)",
            "fire_observed_at": iso(REFERENCE_TS - timedelta(hours=5)),
        })
    return satellite, land


def raw_record(fmt: str, sensor_id: str, ts: datetime, pm25: float, pm10: float, t: float, rh: float) -> dict:
    """Each state's (simulated) vendor feed has its own field names/units -> state adapters."""
    if fmt == "delhi":
        return {"sensor_id": sensor_id, "ts": iso(ts), "pm25": pm25, "pm10": pm10, "temp_c": t, "rh": rh}
    if fmt == "punjab":
        return {"device": sensor_id, "time_ist": ts.strftime("%d-%m-%Y %H:%M"), "PM2_5": pm25,
                "PM10": pm10, "TEMP": t, "HUM": rh}
    utc = ts - timedelta(hours=5, minutes=30)
    return {"id": sensor_id, "timestamp_utc": utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "pm2_5_ugm3": pm25,
            "pm10_ugm3": pm10, "temperature": t, "humidity_pct": rh}


def gen_sensors(state: str, sc: dict, rng: random.Random) -> tuple[list, list]:
    lat0, lon0 = sc["center"]
    center = h3.latlng_to_cell(lat0, lon0, H3_RES)
    ring1 = sorted(h3.grid_ring(center, 1))
    outer = sorted(set(h3.grid_disk(center, GRID_K)) - set(h3.grid_disk(center, 1)))
    chosen = [center] + rng.sample(ring1, 3) + rng.sample(outer, 4)
    sensors, feed = [], []
    for i, cell in enumerate(chosen):
        lat, lon = h3.cell_to_latlng(cell)
        lat += rng.uniform(-0.001, 0.001)
        lon += rng.uniform(-0.001, 0.001)
        sid = f"{sc['sensor_prefix']}-{i + 1:02d}"
        sensors.append({"sensor_id": sid, "type": "low_cost", "owner": "Community network (simulated)",
                        "state": state, "lat": round(lat, 5), "lon": round(lon, 5),
                        "installed_at": "2026-08-01T00:00:00+05:30", "is_simulated": True})
        for h in range(24):
            ts = REFERENCE_TS - timedelta(hours=23 - h)
            # night-time build-up: the local excess is strongest 01:00-05:00
            night = 1.0 if ts.hour in (1, 2, 3, 4, 5) else 0.35
            true = plume(sc, lat, lon, sc["peak_pm25"] * night, sc["background_pm25"])
            true *= 1 + rng.uniform(-0.05, 0.05)
            rh = min(95, sc["weather"]["humidity"] + rng.uniform(-6, 6) + (6 if night == 1.0 else -8))
            t = sc["weather"]["temperature_c"] + rng.uniform(-1, 1) + (0 if night == 1.0 else 6)
            raw25 = true * humidity_growth(rh)
            pm10 = true * (2.6 if state == "maharashtra" else 1.8) * (1 + rng.uniform(-0.05, 0.05))
            feed.append(raw_record(sc["raw_format"], sid, ts, round(raw25, 1), round(pm10, 1),
                                   round(t, 1), round(rh, 1)))
    return sensors, feed


def gen_history(state: str, sc: dict, rng: random.Random) -> list:
    """90 days of daily corridor PM2.5 + drivers for the forecast model (simulated)."""
    hist, pm = [], sc["history"]["base"]
    start = REFERENCE_TS.date() - timedelta(days=90)
    for d in range(90):
        day = start + timedelta(days=d)
        season = d / 90  # post-monsoon -> winter build-up
        vent = max(150.0, rng.gauss(1400 - 900 * season, 250))
        fire = max(0, int(rng.gauss(30 * sc["history"]["fire_scale"] * math.sin(math.pi * season) , 8)))
        if sc["history"]["fire_scale"] == 0:
            fire = 0
        rain = rng.random() < 0.05
        pm = (0.45 * pm + 0.55 * sc["history"]["base"] * (1 + 0.25 * season)
              + 70 * (1 - min(vent, 2000) / 2000) + 1.8 * fire
              - (35 if rain else 0) + rng.gauss(0, 9))
        pm = max(15.0, pm)
        hist.append({"date": day.isoformat(), "state": state, "pm25": round(pm, 1),
                     "ventilation_index_m2s": round(vent, 0), "fire_count": fire,
                     "rain": rain})
    return hist


# --- sample citizen photos ----------------------------------------------------------------
# Real CC-licensed photographs from Wikimedia Commons (see data/sample/photos/ATTRIBUTION.json and
# THIRD_PARTY.md). They are committed, not generated; this script only fingerprints them so demo mode
# can return a stored verification for each sample photo.
PHOTOS = {
    "industrial_chimney_smoke.jpg": "industrial_emission",
    "crop_burning_field.jpg": "crop_residue_burning",
    "construction_dust_site.jpg": "construction_dust",
    "clear_sky_park.jpg": "irrelevant",
}

VERIFICATIONS = {
    "industrial_emission": {
        "is_pollution_event": True, "source_type": "industrial_emission", "visual_severity": 4,
        "observed_indicators": ["dense smoke plume from a tall stack", "continuous emission",
                                "industrial chimney"],
        "confidence": 0.86, "image_quality_ok": True, "requires_human_review": False,
        "explanation": "A dense smoke plume is rising from an industrial chimney.",
    },
    "crop_residue_burning": {
        "is_pollution_event": True, "source_type": "crop_residue_burning", "visual_severity": 4,
        "observed_indicators": ["dense smoke over a harvested field", "burning stubble", "low visibility"],
        "confidence": 0.87, "image_quality_ok": True, "requires_human_review": False,
        "explanation": "Thick smoke from burning crop residue over a harvested field.",
    },
    "construction_dust": {
        "is_pollution_event": True, "source_type": "construction_dust", "visual_severity": 3,
        "observed_indicators": ["visible dust cloud", "excavator demolishing a structure", "no water spraying"],
        "confidence": 0.82, "image_quality_ok": True, "requires_human_review": False,
        "explanation": "A dust cloud from demolition work with no visible dust suppression.",
    },
    "irrelevant": {
        "is_pollution_event": False, "source_type": "other_unknown", "visual_severity": 0,
        "observed_indicators": ["clear blue sky", "green vegetation"],
        "confidence": 0.93, "image_quality_ok": True, "requires_human_review": False,
        "explanation": "No smoke, dust or haze visible; image does not show a pollution event.",
    },
}


def dump(name: str, obj) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(exist_ok=True)
    for state, sc in SCENARIOS.items():
        sat, land = gen_grid_layers(state, sc, rng)
        sensors, feed = gen_sensors(state, sc, rng)
        dump(f"{state}/satellite_h3.json", {
            "metadata": meta(sc["scope"], "Simulated extract shaped like Earth Engine output "
                             "(Sentinel-5P NO2, MODIS MAIAC AOD, FIRMS) aggregated to H3 res 8"),
            "records": sat})
        dump(f"{state}/land_use_h3.json", {
            "metadata": meta(sc["scope"], "Synthetic demo land-use labels per H3 cell"),
            "records": land})
        dump(f"{state}/sensors_lowcost_meta.json", {
            "metadata": meta(sc["scope"], "Simulated low-cost community sensor registry"),
            "records": sensors})
        dump(f"{state}/sensors_lowcost_feed.json", {
            "metadata": meta(sc["scope"], f"Simulated low-cost sensor vendor feed ({sc['raw_format']} "
                             "format) with humidity over-read bias; last 24h hourly",
                             notes="Raw values are NOT calibrated; see state adapter + calibration."),
            "records": feed})
        st = dict(sc["station"])
        st.update({"state": state, "type": "official", "observed_at": iso(REFERENCE_TS - timedelta(minutes=55))})
        dump(f"{state}/official_stations.json", {
            "metadata": meta(sc["scope"], "Sample official station reading modelled on CPCB CAAQMS "
                             "patterns (not an actual reading)"),
            "records": [st]})
        wf = [{"horizon_hours": 24 * (i + 1), "ventilation_index_m2s": sc["forecast"]["vent"][i],
               "fire_count_upwind_forecast": sc["forecast"]["fire"][i], "rain_mm": sc["forecast"]["rain"][i]}
              for i in range(3)]
        dump(f"{state}/weather.json", {
            "metadata": meta(sc["scope"], "Sample weather shaped like ERA5-Land (current) and GFS "
                             "(72h forecast) output"),
            "current": {**sc["weather"], "state": state, "observed_at": iso(REFERENCE_TS - timedelta(minutes=30)),
                        "source": "ERA5-Land reanalysis (sample extract)"},
            "forecast": {"issued_at": iso(REFERENCE_TS - timedelta(hours=3)),
                         "source": "NOAA GFS 0.25 (sample extract)", "steps": wf}})
        dump(f"{state}/pm25_history_daily.json", {
            "metadata": meta(sc["scope"], "Simulated 90-day daily corridor PM2.5 + drivers for "
                             "forecast training/backtest"),
            "records": gen_history(state, sc, rng)})

    photos_dir = OUT / "photos"
    fixtures = {}
    for name, kind in PHOTOS.items():
        sha = hashlib.sha256((photos_dir / name).read_bytes()).hexdigest()
        fixtures[sha] = {"file": name, "verification": VERIFICATIONS[kind]}
    dump("ai_fixtures/photo_verification.json", {
        "metadata": meta("all demo states", "Fixture Gemini photo-verification outputs for the "
                         "CC-licensed sample photos (demo mode only; live mode sends them to Gemini)"),
        "by_sha256": fixtures,
        "default_by_source": VERIFICATIONS,
    })
    print(f"wrote sample data to {OUT}")


if __name__ == "__main__":
    main()
