# Third-party datasets, models, services and libraries

Every reused dataset, model, service, map source, image and library is cited here (hackathon rule).
"Live" means it is called for real in the deployed prototype; "wired, demo" means the adapter is written
but runs on labelled sample data until credentials or registration are available.

## AI models and Google Cloud services

| Name | Type | Terms | Source URL | Used for | Status |
|---|---|---|---|---|---|
| Gemini 2.5 Flash (`gemini-2.5-flash`) on Vertex AI | Foundation model | Google Cloud / Vertex AI Generative AI terms | https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash | Photo verification (multimodal), action brief, health advisory, advisory translation fallback. Structured JSON output, prompts in `ai/prompts/` | Live |
| Cloud Translation API (v2 Basic with API key, v3 with ADC) | Service | Google Cloud terms | https://cloud.google.com/translate | English → Hindi / Punjabi advisories, free-text translation | Live |
| Cloud Text-to-Speech API | Service | Google Cloud terms | https://cloud.google.com/text-to-speech | Spoken advisories (en-IN, hi-IN, pa-IN) | Live |
| Cloud Speech-to-Text API (v1) | Service | Google Cloud terms | https://cloud.google.com/speech-to-text | Citizen voice notes → report description | Live |
| Google Maps Platform Geocoding API | Service | Google Maps Platform terms | https://developers.google.com/maps/documentation/geocoding | Report address (reverse geocoding) and locality search | Live |
| Google Maps JavaScript API | Service / map tiles | Google Maps Platform terms | https://developers.google.com/maps/documentation/javascript | Officer hotspot map basemap | Live when the browser key allows the domain |
| BigQuery | Service | Google Cloud terms | https://cloud.google.com/bigquery | Append-only analytics mirror (`air_quality_network.records`) | Live |
| Cloud Storage | Service | Google Cloud terms | https://cloud.google.com/storage | Citizen report photos (`air-quality-network/reports/`) | Live |
| Cloud Run, Cloud Build, Secret Manager, Artifact Registry | Services | Google Cloud terms | https://cloud.google.com/run | API hosting, build, key storage | Live |
| Google Earth Engine (Python API) | Service | Earth Engine terms | https://earthengine.google.com | Satellite and weather layers aggregated to H3 | Wired, demo (registration pending) |
| Cloud Firestore | Service | Google Cloud / Firebase terms | https://firebase.google.com/docs/firestore | Operational mirror | Wired, demo (Firebase not added yet) |
| Vercel | Hosting | Vercel terms | https://vercel.com | Hosting of the two Next.js apps | Live |

## Datasets

| Name | Type | Licence / terms | Source URL | Used for | Status |
|---|---|---|---|---|---|
| Sentinel-5P TROPOMI OFFL L3 NO2 (`COPERNICUS/S5P/OFFL/L3_NO2`) | Satellite dataset | Copernicus Sentinel data terms (free, open) | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2 | NO2 column anomaly per cell | Wired, demo |
| NASA FIRMS active fires (`FIRMS`) | Satellite dataset | NASA open data | https://developers.google.com/earth-engine/datasets/catalog/FIRMS | Fires upwind | Wired, demo |
| MODIS MAIAC AOD (`MODIS/061/MCD19A2_GRANULES`) | Satellite dataset | NASA LP DAAC open data | https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES | Aerosol optical depth per cell | Wired, demo |
| ERA5-Land hourly (`ECMWF/ERA5_LAND/HOURLY`) | Reanalysis | Copernicus C3S licence | https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY | Current wind, temperature, humidity | Wired, demo |
| NOAA GFS 0.25 (`NOAA/GFS0P25`) | Weather forecast | NOAA public domain | https://developers.google.com/earth-engine/datasets/catalog/NOAA_GFS0P25 | 24/48/72 h forecast drivers | Wired, demo |
| CPCB real-time AQI via data.gov.in (resource `3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69`) | Dataset (API) | Government Open Data Licence – India | https://data.gov.in | Official station readings | Wired, demo (no key yet) |
| India National AQI PM2.5 breakpoints | Standard | Public (CPCB) | https://cpcb.nic.in | AQI category labels | Used |
| κ-Köhler humidity correction (Crilley et al., 2018, AMT 11, 709–720) | Method | Paper, CC BY 4.0 | https://doi.org/10.5194/amt-11-709-2018 | Low-cost sensor calibration | Used |

## Map tiles and basemaps

| Name | Licence / terms | Source URL | Used for |
|---|---|---|---|
| Google Maps (JavaScript API tiles) | Google Maps Platform terms | https://developers.google.com/maps | Officer map when `NEXT_PUBLIC_MAPS_API_KEY` is set and accepted |
| OpenStreetMap standard tiles | Data ODbL; OSMF Tile Usage Policy (light demo use) | https://www.openstreetmap.org/copyright | Fallback basemap (attribution shown on the map) |

## Images

Sample citizen photos in `data/sample/photos/` are real photographs from Wikimedia Commons, resized to
640 px and re-encoded as JPEG. They were not taken at the demo locations. Full records are in
`data/sample/photos/ATTRIBUTION.json`, and `/api/samples/photos` returns the credit with each photo.

| File | Original | Author | Licence |
|---|---|---|---|
| `industrial_chimney_smoke.jpg` | [Smoke factory - panoramio - Alireza Shakernia.jpg](https://commons.wikimedia.org/wiki/File:Smoke_factory_-_panoramio_-_Alireza_Shakernia.jpg) | Alireza Shakernia | CC BY-SA 3.0 |
| `crop_burning_field.jpg` | [NP India burning 8 (6314802183).jpg](https://commons.wikimedia.org/wiki/File:NP_India_burning_8_(6314802183).jpg) | Neil Palmer (CIAT) | CC BY-SA 2.0 |
| `construction_dust_site.jpg` | [Another beam bites the dust - geograph.org.uk - 279756.jpg](https://commons.wikimedia.org/wiki/File:Another_beam_bites_the_dust_-_geograph.org.uk_-_279756.jpg) | Walter Baxter | CC BY-SA 2.0 |
| `clear_sky_park.jpg` | [Blue sky in highlands park.jpg](https://commons.wikimedia.org/wiki/File:Blue_sky_in_highlands_park.jpg) | MaxixKatana | CC BY-SA 4.0 |

## Libraries: frontend (`apps/citizen-web`, `apps/officer-dashboard`)

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| Next.js 16 | MIT | https://nextjs.org | App framework |
| React 19 / React DOM | MIT | https://react.dev | UI |
| TypeScript | Apache-2.0 | https://www.typescriptlang.org | Types |
| Tailwind CSS 4, @tailwindcss/postcss | MIT | https://tailwindcss.com | Styling |
| shadcn/ui (CLI + generated components) | MIT | https://ui.shadcn.com | UI components |
| Base UI (`@base-ui/react`) | MIT | https://base-ui.com | Headless primitives behind shadcn components |
| class-variance-authority | Apache-2.0 | https://cva.style | Component variants |
| cn | MIT | https://www.npmjs.com/package/cn | Class-name helper |
| lucide-react | ISC | https://lucide.dev | Icons |
| next-themes | MIT | https://github.com/pacocoursey/next-themes | Theme handling |
| sonner | MIT | https://sonner.emilkowal.ski | Toasts |
| tw-animate-css | MIT | https://github.com/Wombosvideo/tw-animate-css | Animations |
| Leaflet | BSD-2-Clause | https://leafletjs.com | Map fallback when the Maps key is absent or rejected |
| ESLint, eslint-config-next | MIT | https://eslint.org | Linting |

## Libraries: API (`services/api`)

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| FastAPI | MIT | https://fastapi.tiangolo.com | API framework |
| Uvicorn | BSD-3-Clause | https://www.uvicorn.org | ASGI server |
| Pydantic / pydantic-settings | MIT | https://docs.pydantic.dev | Schemas, settings, AI output validation |
| python-multipart | Apache-2.0 | https://github.com/Kludex/python-multipart | Photo and audio uploads |
| Google Gen AI SDK (`google-genai`) | Apache-2.0 | https://github.com/googleapis/python-genai | Gemini on Vertex AI |
| google-cloud-bigquery, google-cloud-storage, google-auth | Apache-2.0 | https://github.com/googleapis/google-cloud-python | BigQuery / GCS mirrors, ADC |
| firebase-admin | Apache-2.0 | https://github.com/firebase/firebase-admin-python | Firestore mirror (wired) |
| Earth Engine Python API | Apache-2.0 | https://github.com/google/earthengine-api | Satellite + weather jobs (wired) |
| H3 (h3-py) | Apache-2.0 | https://github.com/uber/h3-py | Hexagonal grid (res 8, ~1 km) |
| httpx | BSD-3-Clause | https://www.python-httpx.org | CPCB, Translation, TTS, STT, Geocoding REST calls |
| pytest, ruff | MIT | https://pytest.org · https://docs.astral.sh/ruff | Tests and linting |
| uv | MIT / Apache-2.0 | https://github.com/astral-sh/uv | Python packaging, Docker build |

## Tooling for submission materials

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| python-pptx | MIT | https://github.com/scanny/python-pptx | Generates `docs/pitch/VayuDrishti_pitch.pptx` |

## Generated / sample data (not third-party)

Everything else in `data/sample/` is **synthetic**, produced by `data/generate_sample.py` (fixed seed), or
hand-written (`ai_fixtures/advisory_templates.json`). Station names are real places, but the values are
**not** real CPCB readings. Every file carries `source`, `reference_timestamp`, `dataset_version`,
`geographic_scope` and `is_sample` / `is_synthetic`.
