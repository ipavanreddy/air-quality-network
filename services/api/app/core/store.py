"""Operational store: local JSON file (demo) with best-effort mirroring to Firestore / BigQuery.

The local file (services/api/.localdata/store.json) is always the source of truth for the MVP so the
demo works offline. When FIREBASE_PROJECT_ID / GOOGLE_CLOUD_PROJECT+BIGQUERY_DATASET are set, every
write is mirrored (Firestore collection per record type; BigQuery table `records`, see
infrastructure/bigquery/schema.sql).
"""
import json
import threading
from datetime import UTC, datetime

from app.config import settings
from app.core import integrations

COLLECTIONS = ("reports", "hotspots", "alerts", "advisories", "observations")


class Store:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.path = settings.local_data_dir / "store.json"
        self.data: dict[str, dict[str, dict]] = {c: {} for c in COLLECTIONS}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                for c in COLLECTIONS:
                    self.data[c] = raw.get(c, {})
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, default=str))
        tmp.replace(self.path)

    def all(self, collection: str) -> list[dict]:
        with self._lock:
            return list(self.data[collection].values())

    def get(self, collection: str, key: str) -> dict | None:
        with self._lock:
            return self.data[collection].get(key)

    def put(self, collection: str, key: str, record: dict) -> dict:
        with self._lock:
            self.data[collection][key] = record
            self._save()
        mirror(collection, key, record)
        return record

    def delete(self, collection: str, key: str) -> None:
        with self._lock:
            self.data[collection].pop(key, None)
            self._save()

    def reset(self) -> None:
        with self._lock:
            self.data = {c: {} for c in COLLECTIONS}
            self._save()


_fs_client = None
_bq_client = None


def mirror(collection: str, key: str, record: dict) -> None:
    global _fs_client, _bq_client
    payload = json.loads(json.dumps(record, default=str))
    if integrations.enabled("firestore"):
        try:
            if _fs_client is None:
                from google.cloud import firestore  # provided by firebase-admin

                _fs_client = firestore.Client(project=settings.firebase_project_id)
            _fs_client.collection(collection).document(key).set(payload)
            integrations.clear_error("firestore")
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("firestore", exc)
    if integrations.enabled("bigquery"):
        try:
            if _bq_client is None:
                from google.cloud import bigquery

                _bq_client = bigquery.Client(project=settings.google_cloud_project)
            table = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.records"
            errors = _bq_client.insert_rows_json(table, [{
                "record_type": collection, "record_id": key, "state": payload.get("state"),
                "recorded_at": datetime.now(UTC).isoformat(), "payload": json.dumps(payload),
            }])
            if errors:
                raise RuntimeError(str(errors)[:200])
            integrations.clear_error("bigquery")
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("bigquery", exc)
