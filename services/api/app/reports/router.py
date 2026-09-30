from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.deps import get_engine, not_found
from app.reports.service import create_report
from app.reports.storage import load_photo

router = APIRouter(prefix="/api/reports", tags=["citizen reports"])
MAX_BYTES = 10 * 1024 * 1024


def public(r: dict) -> dict:
    return {k: v for k, v in r.items() if k != "photo_url"}


@router.post("")
async def submit_report(
    photo: UploadFile = File(...),
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(""),
    language: str = Form("en"),
    reporter_id: str = Form("anonymous"),
):
    data = await photo.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "photo larger than 10 MB")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(422, "invalid coordinates")
    r = create_report(get_engine(), photo=data, mime_type=photo.content_type or "application/octet-stream",
                      lat=lat, lon=lon, description=description, language=language, reporter_id=reporter_id)
    return public(r)


@router.get("")
def list_reports(state: str | None = None, limit: int = 50):
    rows = [r for r in get_engine().store.all("reports") if state is None or r["state"] == state]
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return [public(r) for r in rows[:limit]]


@router.get("/{report_id}")
def get_report(report_id: str):
    r = get_engine().store.get("reports", report_id)
    if r is None:
        raise not_found("report", report_id)
    return public(r)


@router.get("/{report_id}/photo")
def get_photo(report_id: str):
    r = get_engine().store.get("reports", report_id)
    data = load_photo(r["photo_url"]) if r else None
    if data is None:
        raise not_found("photo", report_id)
    media = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
    return Response(content=data, media_type=media)
