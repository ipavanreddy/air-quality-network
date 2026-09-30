"""Google Maps Platform Geocoding (server-side key MAPS_API_KEY) for citizen location capture (PRD §27, FR-01).

- reverse(lat, lon): a readable place name to confirm the report location.
- search(query): forward geocoding so a citizen can type a locality instead of sharing GPS.
Demo mode (no key): nearest pilot area name only / no search.
"""
from functools import lru_cache

import httpx

from app.config import settings
from app.core import integrations

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def _call(params: dict) -> list[dict]:
    res = httpx.get(GEOCODE_URL, params={**params, "key": settings.maps_api_key}, timeout=10)
    res.raise_for_status()
    body = res.json()
    if body.get("status") not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Geocoding {body.get('status')}: {body.get('error_message', '')}"[:200])
    return body.get("results", [])


def _locality(result: dict) -> str | None:
    wanted = ("sublocality_level_1", "sublocality", "locality", "administrative_area_level_3")
    for kind in wanted:
        for c in result.get("address_components", []):
            if kind in c.get("types", []):
                return c["long_name"]
    return None


@lru_cache(maxsize=512)
def _reverse_cached(lat: float, lon: float) -> dict | None:
    results = _call({"latlng": f"{lat},{lon}", "region": "in"})
    if not results:
        return None
    top = results[0]
    return {"formatted_address": top["formatted_address"], "locality": _locality(top),
            "place_id": top.get("place_id"), "source": "Google Maps Geocoding API"}


def reverse(lat: float, lon: float) -> dict | None:
    """Readable address for a point, or None in demo mode / on failure (never blocks a report)."""
    if not integrations.enabled("maps"):
        return None
    try:
        out = _reverse_cached(round(lat, 4), round(lon, 4))
        integrations.clear_error("maps")
        return out
    except Exception as exc:  # noqa: BLE001
        integrations.record_fallback("maps", exc)
        return None


def search(query: str, limit: int = 5) -> list[dict]:
    results = _call({"address": query, "components": "country:IN", "region": "in"})
    integrations.clear_error("maps")
    return [{"formatted_address": r["formatted_address"], "locality": _locality(r),
             "lat": r["geometry"]["location"]["lat"], "lon": r["geometry"]["location"]["lng"],
             "place_id": r.get("place_id"), "source": "Google Maps Geocoding API"} for r in results[:limit]]
