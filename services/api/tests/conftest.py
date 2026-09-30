"""Tests always run in demo mode with an isolated local store, whatever is in .env."""
import os
import tempfile

os.environ["FORCE_DEMO_MODE"] = "true"
os.environ["LOCAL_DATA_DIR"] = tempfile.mkdtemp(prefix="vayu-test-")
os.environ["SENSOR_INGEST_TOKEN"] = "test-token"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fresh(client):
    res = client.post("/api/demo/reset")
    assert res.status_code == 200
    return client
