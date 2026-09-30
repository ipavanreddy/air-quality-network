from fastapi import APIRouter, HTTPException, Query

from app.core import integrations
from app.geo import maps

router = APIRouter(prefix="/api/geocode", tags=["location"])


@router.get("")
def search(q: str = Query(min_length=2, max_length=200)):
    """Forward geocoding (India only) so a citizen can confirm a location by typing a locality."""
    if not integrations.enabled("maps"):
        return {"mode": "demo", "results": [], "note": "Maps key not configured: pick a pilot area instead."}
    try:
        return {"mode": "real", "results": maps.search(q)}
    except Exception as exc:  # noqa: BLE001
        integrations.record_fallback("maps", exc)
        raise HTTPException(502, "geocoding unavailable") from None


@router.get("/reverse")
def reverse(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)):
    out = maps.reverse(lat, lon)
    return {"mode": "real" if out else "demo", "result": out}
