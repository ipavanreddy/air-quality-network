"""Shared model registry with model cards (PRD §19, FR-11).

Local registry for the MVP; the same cards would be attached to Vertex AI Model Registry entries.
"""
from app.forecasting.model import (
    HORIZONS,
    PERSISTENCE,
    SHARED_MODEL,
    SHARED_TRAIN_CONFIGS,
    TEST_DAYS,
    trained,
)
from app.hotspots.confidence import MODEL_VERSION as HOTSPOT_MODEL
from app.hotspots.confidence import WEIGHTS
from app.interop.adapters import configs
from app.sensors_calibration.calibration import CALIBRATION_MODEL_VERSION, KAPPA


def _used_by(field: str, model_id: str) -> list[str]:
    return [c.id for c in configs().values() if getattr(c, field) == model_id]


def models() -> list[dict]:
    m = trained()
    metrics = {cid: {f"{h}h": {k: v for k, v in m["metrics"][cid][h].items() if k != "persistence_sigma"}
                     for h in HORIZONS} for cid in m["metrics"]}
    return [
        {
            "id": SHARED_MODEL,
            "name": "Indo-Gangetic Plain smog-season PM2.5 forecast",
            "type": "forecasting",
            "version": "1",
            "registry": "local (demo) - Vertex AI Model Registry target",
            "used_by": _used_by("forecast_model", SHARED_MODEL),
            "card": {
                "description": "Linear model per horizon on standardised features (PM2.5 today, forecast "
                               "ventilation index, forecast upwind fire count), pooled across configurations "
                               "and fine-tuned per configuration with a bias offset.",
                "training_region": ", ".join(SHARED_TRAIN_CONFIGS),
                "training_period": "90 days of daily data up to the reference date (last "
                                   f"{TEST_DAYS} days held out)",
                "training_data": "SIMULATED corridor histories (data/sample/*/pm25_history_daily.json)",
                "features": ["pm25_today", "ventilation_index_m2s[t+h]", "fire_count_upwind[t+h]"],
                "horizons_hours": list(HORIZONS),
                "metrics_mae_vs_persistence": {k: v for k, v in metrics.items() if k in SHARED_TRAIN_CONFIGS},
                "limitations": ["Trained on simulated data: accuracy numbers demonstrate the method only",
                                "Daily resolution; no festival/holiday features",
                                "Ventilation index is a proxy when mixing height is unavailable"],
                "sharing": "Delhi NCR and Punjab reuse the same registered model; each applies its own "
                           "fine-tune offset learned on local data.",
            },
        },
        {
            "id": PERSISTENCE,
            "name": "Persistence baseline",
            "type": "forecasting",
            "version": "1",
            "registry": "local (demo)",
            "used_by": _used_by("forecast_model", PERSISTENCE),
            "card": {"description": "Tomorrow looks like today. Range from historical persistence error.",
                     "metrics_mae": {k: v for k, v in metrics.items() if k not in SHARED_TRAIN_CONFIGS},
                     "limitations": ["Ignores weather and fire drivers"]},
        },
        {
            "id": CALIBRATION_MODEL_VERSION,
            "name": "Low-cost PM2.5 humidity correction",
            "type": "calibration",
            "version": "1",
            "registry": "local (demo)",
            "used_by": _used_by("calibration_model", CALIBRATION_MODEL_VERSION),
            "card": {"description": f"kappa-Kohler humidity growth correction, kappa={KAPPA} (fixed, literature "
                                    "value; not trained on co-located data in the MVP).",
                     "limitations": ["Output is indicative, not regulatory grade",
                                     "Should be re-fitted per sensor model against co-located official stations"]},
        },
        {
            "id": HOTSPOT_MODEL,
            "name": "Hotspot Confidence (transparent weighted score)",
            "type": "scoring",
            "version": "1",
            "registry": "local (demo)",
            "used_by": [c.id for c in configs().values()],
            "card": {"weights": WEIGHTS,
                     "thresholds": {c.id: c.hotspot_threshold for c in configs().values()},
                     "description": "Deterministic rule-based score; each factor 0-100 with explanation."},
        },
    ]


def get_model(model_id: str) -> dict | None:
    return next((m for m in models() if m["id"] == model_id), None)
