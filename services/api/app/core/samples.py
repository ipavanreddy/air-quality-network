"""Load committed sample data (data/sample) and replay it relative to 'now'.

Sample files carry a fixed `reference_timestamp`. At load time every timestamp is shifted by
(now - reference) so freshness reads naturally in a live demo; the original reference timestamp
and the shift are kept in the metadata (`time_mode: replayed`).
"""
import json
from datetime import UTC, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from app.config import settings

IST = timezone(timedelta(hours=5, minutes=30))
TS_KEYS = ("observed_at", "issued_at", "installed_at", "ts", "no2_observed_at", "aod_observed_at",
           "fire_observed_at", "timestamp_utc", "time_ist")


def now() -> datetime:
    return datetime.now(UTC)


def parse_ts(value: str, fmt: str = "iso8601", tz: str = "+05:30") -> datetime:
    if fmt == "iso8601":
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        dt = datetime.strptime(value, fmt)
    if dt.tzinfo is None:
        sign = 1 if tz[0] == "+" else -1
        hh, mm = tz[1:].split(":")
        dt = dt.replace(tzinfo=timezone(sign * timedelta(hours=int(hh), minutes=int(mm))))
    return dt


def age_minutes(ts: datetime | str | None) -> int | None:
    if ts is None:
        return None
    if isinstance(ts, str):
        ts = parse_ts(ts)
    return max(0, int((now() - ts).total_seconds() // 60))


@lru_cache
def _replay_shift() -> timedelta:
    ref = _reference()
    shift = now() - ref
    return timedelta(minutes=int(shift.total_seconds() // 60))


def _reference() -> datetime:
    meta = json.loads((settings.sample_data_dir / "delhi-ncr" / "weather.json").read_text())["metadata"]
    return datetime.fromisoformat(meta["reference_timestamp"])


def _shift_value(key: str, value: str) -> str:
    shift = _replay_shift()
    if key == "time_ist":
        dt = datetime.strptime(value, "%d-%m-%Y %H:%M") + shift
        return dt.strftime("%d-%m-%Y %H:%M")
    if key == "timestamp_utc":
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")) + shift
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (datetime.fromisoformat(value) + shift).isoformat()


def _shift(obj):
    if isinstance(obj, dict):
        return {k: (_shift_value(k, v) if k in TS_KEYS and isinstance(v, str) else _shift(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_shift(v) for v in obj]
    return obj


@lru_cache
def load(rel_path: str, replay: bool = True) -> dict:
    """Load a sample JSON file. `replay=False` keeps the original timestamps (e.g. daily history)."""
    path: Path = settings.sample_data_dir / rel_path
    data = json.loads(path.read_text())
    meta = dict(data.get("metadata", {}))
    body = {k: v for k, v in data.items() if k != "metadata"}
    if replay:
        body = _shift(body)
        meta["time_mode"] = "replayed"
        meta["replay_shift_minutes"] = int(_replay_shift().total_seconds() // 60)
    return {"metadata": meta, **body}


def sample_meta(rel_path: str) -> dict:
    return load(rel_path)["metadata"]
