import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    project_name: str = "air-quality-network"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    google_genai_use_vertexai: bool = False
    google_cloud_project: str = ""
    # Gemini on Vertex AI: "global" endpoint (asia-south1 returned 429s under load)
    google_cloud_location: str = "global"
    # API key for Speech-to-Text / Text-to-Speech / Translation. Deliberately NOT named GOOGLE_API_KEY:
    # the google-genai SDK treats GOOGLE_API_KEY as a Gemini key, which breaks Vertex AI mode.
    google_cloud_api_key: str = ""
    google_application_credentials: str = ""  # local dev only; Cloud Run uses its service account
    bigquery_dataset: str = "air_quality_network"
    gcs_bucket: str = ""
    firebase_project_id: str = ""
    maps_api_key: str = ""
    earth_engine_project: str = ""
    data_gov_in_api_key: str = ""
    sensor_ingest_token: str = ""
    cors_origins: str = "http://localhost:3020,http://localhost:3021"
    cors_origin_regex: str = ""  # e.g. https://.*\.vercel\.app for preview deployments

    # Demo / local fallbacks
    force_demo_mode: bool = False  # true = ignore all keys and use sample data + fixtures
    sample_data_dir: Path = REPO_ROOT / "data" / "sample"
    adapters_dir: Path = REPO_ROOT / "data" / "adapters"
    local_data_dir: Path = REPO_ROOT / "services" / "api" / ".localdata"


settings = Settings()

# Google client libraries (ADC) read GOOGLE_APPLICATION_CREDENTIALS from the process environment, not from
# pydantic's .env parsing, so export it when it only lives in .env.
if settings.google_application_credentials and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
