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
    google_cloud_location: str = "asia-south1"
    bigquery_dataset: str = "air_quality_network"
    gcs_bucket: str = ""
    firebase_project_id: str = ""
    maps_api_key: str = ""
    earth_engine_project: str = ""
    data_gov_in_api_key: str = ""
    sensor_ingest_token: str = ""
    cors_origins: str = "http://localhost:3020,http://localhost:3021"

    # Demo / local fallbacks
    force_demo_mode: bool = False  # true = ignore all keys and use sample data + fixtures
    sample_data_dir: Path = REPO_ROOT / "data" / "sample"
    adapters_dir: Path = REPO_ROOT / "data" / "adapters"
    local_data_dir: Path = REPO_ROOT / "services" / "api" / ".localdata"


settings = Settings()
