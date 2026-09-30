# VayuDrishti: Federated Hyper-local Air Quality Platform

Build with AI (Google) hackathon, Track 2. Full spec: [docs/PRD.md](docs/PRD.md).

## Core journey (build this first; PRD §57)

```text
Citizen Photo → Gemini Verification
 ↓
Sensor + Satellite + Weather on Grid
 ↓
Hotspot Confidence
 ↓
Likely Source + Action Brief
 ↓
Officer Alert
```

**Headline score:** Hotspot Confidence (Sensor anomaly 35 · Satellite 25 · Citizen reports 25 · Weather plausibility 15)
**Users:** Citizen Reporter (`apps/citizen-web`) · Environmental Officer (`apps/officer-dashboard`)
**Languages:** English, Hindi, Punjabi
**Demo states:** Delhi NCR (industrial / smog), Punjab (crop burning → cross-boundary alert), Maharashtra (construction dust)

## Stack

Next.js + TypeScript + Tailwind + shadcn/ui (pnpm workspace) · FastAPI on Cloud Run (uv, Python 3.12) ·
Gemini API / Vertex AI · BigQuery · Firebase · Cloud Storage · Google Maps Platform · Earth Engine ·
Speech-to-Text / Text-to-Speech / Translation · region `asia-south1`.

## Run locally

```bash
cp .env.example .env                      # fill in keys
for a in apps/*; do cp $a/.env.example $a/.env.local; done
pnpm install
(cd services/api && uv sync)

pnpm dev:api          # http://localhost:8020  (docs at /docs)
pnpm dev:citizen-web   # http://localhost:3020
pnpm dev:officer-dashboard   # http://localhost:3021
```

With **no keys at all** everything runs in a clearly labelled **demo mode** (amber "Demo mode · sample data"
badge in both apps; click it for a per-integration breakdown). Checks: `pnpm test:api`, `pnpm lint`, `pnpm build`.

## 5-minute demo script (PRD §44)

1. **Officer dashboard** (:3021) → jurisdiction *Delhi NCR*. Grid shows elevated cells near Patparganj (≈66/100),
   below the 70 alert threshold: no Delhi alert yet. Official station (6 km away) reads ~112 µg/m³.
2. **Citizen app** (:3020) → *East Delhi (Patparganj)* → pick the night-smoke sample photo → Submit.
   Verification: industrial emission, severity 4/5, 86 %, visible indicators. The page shows
   *Hotspot Confidence 66 → 83* and *sent to the environmental officer*.
3. **Dashboard**: the alert appears in the inbox within ~4 s. Open it to see the Hotspot Confidence breakdown
   (sensor 35 % · satellite 25 % · citizen 25 % · weather 15 %), the likely source with evidence (source + time),
   the forecast outlook, uncertainties, data freshness and the audit trail.
4. Tick the recommended inspection(s) → **Acknowledge & approve** → record the action → close.
5. Forecast slider (now / +24 / +48 / +72 h) re-colours the grid; the forecast card shows range and drivers.
6. **Advisory**: *Generate advisory draft* → switch English / हिन्दी / ਪੰਜਾਬੀ → *Approve & publish*. The citizen app
   shows it in the chosen language with 🔊 *Listen* (Cloud TTS, or the browser voice in demo mode).
7. **Interoperability**: switch to *Punjab*. A crop-burning hotspot (seeded sample report + 38 upwind fires) is
   waiting. Acknowledge it → **Send cross-boundary alert to Delhi NCR**. Switch back to Delhi: the incoming
   cross-boundary alert is in the DPCC inbox. The model registry shows `igp-smog-forecast-v1` shared by Delhi NCR
   and Punjab, with MAE against a persistence baseline. *Maharashtra* shows a construction-dust hotspot with a
   different threshold (65) and the persistence model.

Use *Reset demo* (or `POST /api/demo/reset`) to start again.

## Real integrations vs demo mode

Each integration sits behind a small adapter. It is used for real when its env vars are set, and otherwise falls
back to labelled sample data. A failed real call falls back too and shows `fallback` plus the error in `GET /api/config`.

| Integration | Turn on with | Code | Demo-mode fallback |
|---|---|---|---|
| Gemini (photo verification, action brief, advisory, translation) | `GEMINI_API_KEY`, or `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT` (model from `GEMINI_MODEL`) | `app/ai/services.py`, prompts `ai/prompts/*_v1.md`, schemas `ai/schemas/` | Fixture verification for sample photos (by SHA-256). Other photos get the location's scenario fixture, flagged "image NOT analysed", plus a deterministic templated brief built from the evidence bundle |
| Earth Engine (Sentinel-5P NO2, FIRMS, MODIS AOD, ERA5-Land, GFS → H3) | `EARTH_ENGINE_PROJECT` + ADC / `GOOGLE_APPLICATION_CREDENTIALS` | `app/geospatial_gee/earth_engine.py` | `data/sample/<state>/{satellite_h3,weather}.json` |
| CPCB real-time AQ | `DATA_GOV_IN_API_KEY` | `app/sensors_calibration/cpcb.py` | `data/sample/<state>/official_stations.json` |
| Cloud Translation v3 / Text-to-Speech | `GOOGLE_CLOUD_PROJECT` + ADC (APIs enabled) | `app/localization/google_cloud.py` | Gemini translation (if Gemini is on), else hand-written en/hi/pa templates; browser `speechSynthesis` |
| BigQuery mirror | `GOOGLE_CLOUD_PROJECT` + `BIGQUERY_DATASET` (create `infrastructure/bigquery/schema.sql`) | `app/core/store.py` | Local JSON store `services/api/.localdata/` |
| Firestore mirror | `FIREBASE_PROJECT_ID` | `app/core/store.py` | same |
| Cloud Storage (photos) | `GCS_BUCKET` | `app/reports/storage.py` | `services/api/.localdata/photos/` |
| Google Maps (officer map) | `NEXT_PUBLIC_MAPS_API_KEY` in `apps/officer-dashboard/.env.local` (rebuild) | `components/hex-map.tsx` | Leaflet + OpenStreetMap tiles |
| Sensor ingest auth | `SENSOR_INGEST_TOKEN` (header `X-Ingest-Token`) | `POST /api/sensors/{id}/observations` | open endpoint when unset |

`FORCE_DEMO_MODE=true` ignores all keys (the test suite uses this).

## How it works

- **Grid**: H3 resolution 8 (~1 km), 37 cells per demo area. Each cell fuses calibrated low-cost sensors
  (IDW within 1.2 km, labelled *indicative*), the nearest official station (the expected level), satellite
  NO2 / AOD / upwind fires, weather, land use and verified citizen reports.
- **Hotspot Confidence** (`app/hotspots/confidence.py`): transparent 0–100 per factor, weighted 35/25/25/15.
  Connected cells ≥ the configured threshold become a hotspot. A fast path covers severe, clearly visible reports.
- **Action brief**: Gemini gets only the structured evidence bundle and the jurisdiction's action rules. Output is
  schema-validated, actions not in the rules are dropped, and numbers not found in the bundle are flagged. Every
  AI record stores `model_name`, `model_version` and `prompt_version`.
- **Human approval**: alerts start as `pending_review`. Acknowledging approves the selected actions, and
  action/close follow. Cross-boundary transfers and public advisories each need an explicit officer approval.
- **State adapters** (`data/adapters/*.json`): jurisdiction, threshold, action rules, languages, shared model and
  the field map of each state's (differently formatted) sensor feed → canonical schema
  (`data/schemas/canonical_cell_snapshot.schema.json`, `GET /api/cells/{id}`).
- **Forecast**: `igp-smog-forecast-v1`, a per-horizon linear model on standardised features. It is pooled over
  Delhi NCR and Punjab and fine-tuned per configuration, then backtested against persistence on 20 held-out days
  (see `GET /api/models`).

## Sample data

`cd services/api && uv run python ../../data/generate_sample.py` regenerates `data/sample/` deterministically:
simulated low-cost sensor feeds (with humidity over-read bias), sample station, satellite and weather extracts,
90-day corridor histories, and four generated sample photos. Every file carries `source`, `reference_timestamp`,
`dataset_version`, `geographic_scope` and `is_sample/is_synthetic`. At load time, timestamps are replayed
relative to "now".

## Known gaps

- The forecast model is trained on simulated histories, so its accuracy numbers only demonstrate the method.
  Vertex AI Model Registry and forecasting are not wired in; the registry is local.
- Land-use labels are synthetic in both modes. Boundary-layer height is missing from ERA5-Land and GFS in real mode,
  so it is reported as n/a and the ventilation index is a labelled proxy.
- Real Earth Engine, CPCB, Translation, TTS, BigQuery, Firestore, GCS and Gemini paths are written but untested
  against live services (no keys available). The CPCB client is unit-tested with a mocked HTTP transport.
- There is no authentication or role enforcement: the two roles are separate apps. Alerts go to the dashboard
  only, with no email or SMS. Speech-to-Text voice notes are not implemented.

## Layout

| Path | Purpose |
|---|---|
| `apps/citizen-web/` | Citizen Reporter app |
| `apps/officer-dashboard/` | Environmental Officer dashboard |
| `services/api/` | FastAPI gateway (all domain logic starts here as modules) |
| `services/reports/` | Citizen photo reports + Gemini multimodal verification |
| `services/sensors-calibration/` | Sensor ingestion (Pub/Sub) and calibration |
| `services/geospatial-gee/` | Earth Engine jobs: Sentinel-5P, FIRMS, MODIS AOD, ERA5/GFS → H3 grid |
| `services/hotspots/` | Hotspot detection and Hotspot Confidence |
| `services/forecasting/` | Corridor AQ forecast (Vertex AI / BigQuery ML) |
| `services/alerts/` | Alert generation, routing, cross-boundary alerts |
| `services/localization/` | Speech-to-Text, Text-to-Speech, Translation |
| `ai/` | Prompts, JSON schemas, models, evaluation |
| `data/` | Canonical schema, state adapters, sample data |
| `infrastructure/` | Cloud Run, BigQuery, Firebase config |
| `docs/` | PRD and architecture notes |
