from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_engine, not_found

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AckIn(BaseModel):
    officer: str = Field(min_length=1)
    approved_action_ids: list[str] = []
    note: str = ""


class ActionIn(BaseModel):
    officer: str = Field(min_length=1)
    action_taken: str = Field(min_length=1)


class CloseIn(BaseModel):
    officer: str = Field(min_length=1)
    resolution: str = Field(min_length=1)


class CrossIn(BaseModel):
    officer: str = Field(min_length=1)
    note: str = ""


def _call(fn, *args):
    try:
        return fn(*args)
    except KeyError as exc:
        raise not_found("alert", str(exc)) from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None


@router.get("")
def list_alerts(jurisdiction: str | None = None, status: str | None = None):
    rows = [a for a in get_engine().store.all("alerts")
            if (jurisdiction is None or a["jurisdiction_id"] == jurisdiction)
            and (status is None or a["status"] == status)]
    return sorted(rows, key=lambda a: a["sent_at"], reverse=True)


@router.get("/{alert_id}")
def get_alert(alert_id: str):
    a = get_engine().store.get("alerts", alert_id)
    if a is None:
        raise not_found("alert", alert_id)
    return a


@router.post("/{alert_id}/acknowledge")
def acknowledge(alert_id: str, body: AckIn):
    return _call(get_engine().acknowledge, alert_id, body.officer, body.approved_action_ids, body.note)


@router.post("/{alert_id}/action")
def action(alert_id: str, body: ActionIn):
    return _call(get_engine().record_action, alert_id, body.officer, body.action_taken)


@router.post("/{alert_id}/close")
def close(alert_id: str, body: CloseIn):
    return _call(get_engine().close, alert_id, body.officer, body.resolution)


@router.post("/{alert_id}/cross-boundary")
def cross_boundary(alert_id: str, body: CrossIn):
    return _call(get_engine().send_cross_boundary, alert_id, body.officer, body.note)
