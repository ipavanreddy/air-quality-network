# sensors-calibration

Sensor ingestion (Pub/Sub) and calibration

Starts as a router/module in `services/api/app/` (e.g. `app/sensors_calibration/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
