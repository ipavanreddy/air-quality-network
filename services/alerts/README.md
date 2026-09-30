# alerts

Alert generation, routing, cross-boundary alerts

Starts as a router/module in `services/api/app/` (e.g. `app/alerts/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
