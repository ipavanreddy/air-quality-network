"""Report photo storage: Cloud Storage when GCS_BUCKET is set, else local disk."""
from app.config import settings
from app.core import integrations

EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic"}


def _local_path(report_id: str, mime: str):
    d = settings.local_data_dir / "photos"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{report_id}.{EXT.get(mime, 'bin')}"


def save_photo(report_id: str, data: bytes, mime: str) -> str:
    """Returns the storage URI (gs://... or local://...)."""
    if integrations.enabled("cloud_storage"):
        try:
            from google.cloud import storage

            blob = storage.Client().bucket(settings.gcs_bucket).blob(f"air-quality-network/reports/{report_id}.{EXT.get(mime, 'bin')}")
            blob.upload_from_string(data, content_type=mime)
            integrations.clear_error("cloud_storage")
            return f"gs://{settings.gcs_bucket}/{blob.name}"
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("cloud_storage", exc)
    path = _local_path(report_id, mime)
    path.write_bytes(data)
    return f"local://photos/{path.name}"


def load_photo(uri: str) -> bytes | None:
    if uri.startswith("gs://"):
        from google.cloud import storage

        bucket, _, name = uri[5:].partition("/")
        return storage.Client().bucket(bucket).blob(name).download_as_bytes()
    if uri.startswith("local://"):
        path = settings.local_data_dir / uri[len("local://"):]
        return path.read_bytes() if path.exists() else None
    if uri.startswith("sample://"):
        path = settings.sample_data_dir / uri[len("sample://"):]
        return path.read_bytes() if path.exists() else None
    return None
