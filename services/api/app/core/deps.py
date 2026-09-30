"""Process-wide engine singleton (local store + evidence fusion)."""
from functools import lru_cache

from fastapi import HTTPException

from app.core.engine import Engine
from app.core.store import Store
from app.interop.adapters import configs


@lru_cache
def get_engine() -> Engine:
    return Engine(Store())


def check_state(state: str) -> str:
    if state not in configs():
        raise HTTPException(404, f"unknown city/state config '{state}'. Known: {sorted(configs())}")
    return state


def not_found(kind: str, key: str) -> HTTPException:
    return HTTPException(404, f"{kind} '{key}' not found")
