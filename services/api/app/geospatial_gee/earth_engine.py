"""Earth Engine jobs: satellite + weather signals aggregated to H3 cells (PRD §11, FR-04).

Enabled when EARTH_ENGINE_PROJECT is set (credentials from GOOGLE_APPLICATION_CREDENTIALS / ADC;
the project must be registered for Earth Engine). Output has the same shape as the committed
sample extracts in data/sample/<state>/{satellite_h3,weather}.json, so switching is transparent.

Datasets (see THIRD_PARTY.md):
  COPERNICUS/S5P/OFFL/L3_NO2      tropospheric NO2 column (3-day mean vs prior 30-day median)
  MODIS/061/MCD19A2_GRANULES      MAIAC AOD 0.47 um (scale 0.001)
  FIRMS                           active fire pixels (T21) in a 100 km upwind wedge, last 24 h
  ECMWF/ERA5_LAND/HOURLY          latest 10 m wind, 2 m temperature / dewpoint, precipitation
  NOAA/GFS0P25                    +24/48/72 h wind, humidity, precipitation forecast
"""
import math
from datetime import UTC, datetime

import ee
import h3

from app.config import settings

_initialized = False
SCOPES = ["https://www.googleapis.com/auth/earthengine", "https://www.googleapis.com/auth/cloud-platform"]


def initialize() -> None:
    global _initialized
    if _initialized:
        return
    import google.auth

    credentials, _ = google.auth.default(scopes=SCOPES)
    ee.Initialize(credentials=credentials, project=settings.earth_engine_project)
    _initialized = True


def cells_fc(cells: list[str]) -> ee.FeatureCollection:
    feats = []
    for c in cells:
        ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(c)]
        ring.append(ring[0])
        feats.append(ee.Feature(ee.Geometry.Polygon([ring]), {"h3_cell": c}))
    return ee.FeatureCollection(feats)


def upwind_wedge(lat: float, lon: float, wind_from_deg: float, radius_km: float = 100,
                 half_angle: float = 45) -> ee.Geometry:
    """Sector polygon pointing into the wind (where upwind sources would be)."""
    pts = [[lon, lat]]
    for step in range(-int(half_angle), int(half_angle) + 1, 10):
        b = math.radians(wind_from_deg + step)
        dlat = radius_km * math.cos(b) / 110.57
        dlon = radius_km * math.sin(b) / (111.32 * math.cos(math.radians(lat)))
        pts.append([lon + dlon, lat + dlat])
    pts.append([lon, lat])
    return ee.Geometry.Polygon([pts])


def _iso(ms) -> str | None:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).isoformat() if ms else None


def fetch_weather(lat: float, lon: float) -> dict:
    initialize()
    point = ee.Geometry.Point([lon, lat])
    end = ee.Date(datetime.now(UTC).isoformat())
    era = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterDate(end.advance(-10, "day"), end)
           .sort("system:time_start", False).first())
    vals = era.select(["u_component_of_wind_10m", "v_component_of_wind_10m", "temperature_2m",
                       "dewpoint_temperature_2m", "total_precipitation"]).reduceRegion(
        ee.Reducer.first(), point, 11132).getInfo()
    t_ms = era.get("system:time_start").getInfo()
    u, v = vals["u_component_of_wind_10m"], vals["v_component_of_wind_10m"]
    t_c, td_c = vals["temperature_2m"] - 273.15, vals["dewpoint_temperature_2m"] - 273.15
    rh = 100 * math.exp(17.625 * td_c / (243.04 + td_c)) / math.exp(17.625 * t_c / (243.04 + t_c))
    current = {
        "wind_speed_ms": round(math.hypot(u, v), 2),
        "wind_dir_deg": round((math.degrees(math.atan2(-u, -v)) + 360) % 360),
        "humidity": round(rh),
        "temperature_c": round(t_c, 1),
        "boundary_layer_m": None,  # not in ERA5-Land; reported as missing, never invented
        "rain_mm": round(vals["total_precipitation"] * 1000, 1),
        "observed_at": _iso(t_ms),
        "source": "ERA5-Land hourly (Earth Engine ECMWF/ERA5_LAND/HOURLY)",
    }

    gfs = ee.ImageCollection("NOAA/GFS0P25").filterDate(end.advance(-1, "day"), end)
    latest = gfs.aggregate_max("creation_time")
    run = gfs.filter(ee.Filter.eq("creation_time", latest))
    steps = []
    for hours in (24, 48, 72):
        img = run.filter(ee.Filter.eq("forecast_hours", hours)).first()
        f = img.select(["u_component_of_wind_10m_above_ground", "v_component_of_wind_10m_above_ground",
                        "relative_humidity_2m_above_ground", "total_precipitation_surface"]).reduceRegion(
            ee.Reducer.first(), point, 27830).getInfo()
        ws = math.hypot(f["u_component_of_wind_10m_above_ground"], f["v_component_of_wind_10m_above_ground"])
        steps.append({
            "horizon_hours": hours,
            "wind_speed_ms": round(ws, 2),
            "humidity": round(f["relative_humidity_2m_above_ground"]),
            "rain_mm": round(f["total_precipitation_surface"], 1),
            # Proxy: GFS in EE has no mixing height; assume a nominal 500 m and say so.
            "ventilation_index_m2s": round(ws * 500),
            "ventilation_index_note": "proxy = 10 m wind x nominal 500 m mixing height",
            "fire_count_upwind_forecast": None,  # filled by persistence of today's fire count
        })
    return {"current": current, "forecast": {"issued_at": _iso(latest.getInfo()),
                                             "source": "NOAA GFS 0.25 (Earth Engine NOAA/GFS0P25)",
                                             "steps": steps}}


def fetch_satellite(cells: list[str], center: tuple[float, float], wind_from_deg: float) -> list[dict]:
    initialize()
    fc = cells_fc(cells)
    end = ee.Date(datetime.now(UTC).isoformat())

    no2_col = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2").select("tropospheric_NO2_column_number_density")
    recent = no2_col.filterDate(end.advance(-3, "day"), end)
    baseline = no2_col.filterDate(end.advance(-33, "day"), end.advance(-3, "day")).median()
    recent_mean = recent.mean()
    no2 = ee.Image.cat([
        recent_mean.multiply(1e6).rename("no2_umol"),
        recent_mean.subtract(baseline).divide(baseline).multiply(100).rename("no2_anom"),
    ])
    aod_col = (ee.ImageCollection("MODIS/061/MCD19A2_GRANULES").select("Optical_Depth_047")
               .filterDate(end.advance(-3, "day"), end))
    aod = aod_col.mean().multiply(0.001).rename("aod")

    stats = no2.addBands(aod).reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=1000).getInfo()

    fires_col = ee.ImageCollection("FIRMS").select("T21").filterDate(end.advance(-1, "day"), end)
    fire_mask = fires_col.max().gt(0).unmask(0)
    wedge = upwind_wedge(center[0], center[1], wind_from_deg)
    fire_count = fire_mask.reduceRegion(ee.Reducer.sum(), wedge, 1000, maxPixels=1e9).get("T21").getInfo() or 0

    no2_obs = _iso(recent.aggregate_max("system:time_start").getInfo())
    aod_obs = _iso(aod_col.aggregate_max("system:time_start").getInfo())
    fire_obs = _iso(fires_col.aggregate_max("system:time_start").getInfo())

    out = []
    for f in stats["features"]:
        p = f["properties"]
        out.append({
            "h3_cell": p["h3_cell"],
            "no2_column_umol_m2": _round(p.get("no2_umol"), 1),
            "no2_column_anomaly_pct": _round(p.get("no2_anom"), 1),
            "no2_source": "Sentinel-5P TROPOMI OFFL L3 NO2 (Earth Engine)",
            "no2_observed_at": no2_obs,
            "aod": _round(p.get("aod"), 2),
            "aod_source": "MODIS MAIAC MCD19A2 AOD 0.47um (Earth Engine)",
            "aod_observed_at": aod_obs,
            "fire_count_upwind_100km": round(fire_count),
            "fire_source": "NASA FIRMS active fire T21 (Earth Engine)",
            "fire_observed_at": fire_obs,
        })
    return out


def _round(v, n):
    return None if v is None else round(v, n)
