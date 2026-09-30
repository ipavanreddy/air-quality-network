"""Which Google / public integrations are live, and which are running in demo mode.

Every adapter asks `enabled(name)` before calling a real service and calls `record_fallback`
when a real call fails, so the UI can show an honest "Demo mode / sample data" badge.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.config import settings


@dataclass
class Integration:
    name: str
    label: str
    env_vars: list[str]
    demo_behaviour: str
    configured: bool = False
    last_error: str | None = None
    last_error_at: datetime | None = None
    extra: dict = field(default_factory=dict)

    @property
    def mode(self) -> str:
        if not self.configured:
            return "demo"
        return "fallback" if self.last_error else "real"


def _configured() -> dict[str, bool]:
    s = settings
    gcp = bool(s.google_cloud_project)
    return {
        "gemini": bool(s.gemini_api_key) or (s.google_genai_use_vertexai and gcp),
        "earth_engine": bool(s.earth_engine_project),
        "cpcb": bool(s.data_gov_in_api_key),
        "translation": gcp,
        "text_to_speech": gcp,
        "bigquery": gcp and bool(s.bigquery_dataset),
        "firestore": bool(s.firebase_project_id),
        "cloud_storage": bool(s.gcs_bucket),
        "vertex_ai_models": False,  # Model Registry sync not implemented in the MVP (local registry)
    }


_REGISTRY: dict[str, Integration] = {
    "gemini": Integration("gemini", "Gemini (photo verification, action briefs, advisories)",
                          ["GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI + GOOGLE_CLOUD_PROJECT"],
                          "Fixture / templated AI outputs from data/sample/ai_fixtures"),
    "earth_engine": Integration("earth_engine", "Earth Engine (Sentinel-5P, FIRMS, MODIS AOD, ERA5-Land, GFS)",
                                ["EARTH_ENGINE_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"],
                                "Cached sample satellite + weather extracts in data/sample/<state>/"),
    "cpcb": Integration("cpcb", "CPCB real-time AQ via data.gov.in", ["DATA_GOV_IN_API_KEY"],
                        "Sample official station readings in data/sample/<state>/official_stations.json"),
    "translation": Integration("translation", "Cloud Translation", ["GOOGLE_CLOUD_PROJECT", "ADC credentials"],
                               "Gemini translation if Gemini is live, else pre-written template translations"),
    "text_to_speech": Integration("text_to_speech", "Cloud Text-to-Speech", ["GOOGLE_CLOUD_PROJECT", "ADC credentials"],
                                  "Browser speechSynthesis voice in the citizen app"),
    "bigquery": Integration("bigquery", "BigQuery (analytics mirror)", ["GOOGLE_CLOUD_PROJECT", "BIGQUERY_DATASET"],
                            "Local JSON store in services/api/.localdata"),
    "firestore": Integration("firestore", "Firestore (operational mirror)", ["FIREBASE_PROJECT_ID"],
                             "Local JSON store in services/api/.localdata"),
    "cloud_storage": Integration("cloud_storage", "Cloud Storage (report photos)", ["GCS_BUCKET"],
                                 "Photos saved under services/api/.localdata/photos"),
    "vertex_ai_models": Integration("vertex_ai_models", "Vertex AI Model Registry", ["(not wired in MVP)"],
                                    "Local model registry with model cards (app/models_registry)"),
    "sensors": Integration("sensors", "Low-cost community sensors", ["POST /api/sensors/{id}/observations"],
                           "Simulated low-cost sensor feeds (data/generate_sample.py)"),
}


def refresh() -> None:
    conf = _configured()
    for name, integ in _REGISTRY.items():
        integ.configured = False if settings.force_demo_mode else conf.get(name, False)


def enabled(name: str) -> bool:
    return _REGISTRY[name].configured


def record_fallback(name: str, error: Exception | str) -> None:
    integ = _REGISTRY[name]
    integ.last_error = str(error)[:300]
    integ.last_error_at = datetime.now(UTC)


def clear_error(name: str) -> None:
    _REGISTRY[name].last_error = None


def status() -> dict:
    items = [
        {
            "name": i.name,
            "label": i.label,
            "mode": i.mode,
            "env_vars": i.env_vars,
            "demo_behaviour": i.demo_behaviour,
            "last_error": i.last_error,
        }
        for i in _REGISTRY.values()
    ]
    return {
        "demo_mode": any(i["mode"] != "real" for i in items),
        "force_demo_mode": settings.force_demo_mode,
        "gemini_model": settings.gemini_model,
        "integrations": items,
    }


refresh()
