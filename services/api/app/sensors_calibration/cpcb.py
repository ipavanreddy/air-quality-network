"""CPCB real-time air quality via the data.gov.in Open Government Data API.

Dataset: "Real time Air Quality Index from various locations" (CPCB), resource
3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69. One row per (station, pollutant) with min/max/avg values.
Enabled when DATA_GOV_IN_API_KEY is set.
"""
import math
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings

RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
IST = timezone(timedelta(hours=5, minutes=30))
STATE_NAMES = {"DL": "Delhi", "PB": "Punjab", "MH": "Maharashtra"}
POLLUTANT_KEYS = {"PM2.5": "pm25", "PM10": "pm10", "NO2": "no2", "SO2": "so2", "CO": "co", "OZONE": "o3"}


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_state_rows(state_name: str, client: httpx.Client | None = None) -> list[dict]:
    params = {
        "api-key": settings.data_gov_in_api_key,
        "format": "json",
        "limit": 1000,
        "filters[state]": state_name,
    }
    own = client is None
    client = client or httpx.Client(timeout=20)
    try:
        res = client.get(BASE_URL, params=params)
        res.raise_for_status()
        return res.json().get("records", [])
    finally:
        if own:
            client.close()


def rows_to_stations(rows: list[dict]) -> list[dict]:
    """Pivot (station, pollutant) rows into canonical official-station readings."""
    stations: dict[str, dict] = {}
    for r in rows:
        name = r.get("station")
        if not name:
            continue
        st = stations.setdefault(name, {
            "station_id": f"CPCB-{name}",
            "name": name,
            "lat": _num(r.get("latitude")),
            "lon": _num(r.get("longitude")),
            "type": "official",
            "source": "CPCB CAAQMS via data.gov.in",
            "is_sample": False,
            "observed_at": None,
        })
        key = POLLUTANT_KEYS.get(str(r.get("pollutant_id", "")).upper())
        if key:
            st[key] = _num(r.get("avg_value"))
        if r.get("last_update"):
            try:
                ts = datetime.strptime(r["last_update"], "%d-%m-%Y %H:%M:%S").replace(tzinfo=IST)
                st["observed_at"] = ts.isoformat()
            except ValueError:
                pass
    return [s for s in stations.values() if s.get("pm25") is not None and s["lat"] is not None]


def nearest_station(stations: list[dict], lat: float, lon: float) -> dict | None:
    def dist(s):
        return math.hypot(s["lat"] - lat, (s["lon"] - lon) * math.cos(math.radians(lat)))

    return min(stations, key=dist) if stations else None


def fetch_nearest_station(state_code: str, lat: float, lon: float,
                          client: httpx.Client | None = None) -> dict | None:
    rows = fetch_state_rows(STATE_NAMES.get(state_code, state_code), client=client)
    return nearest_station(rows_to_stations(rows), lat, lon)
