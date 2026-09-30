# Third-party datasets, models and libraries

Every reused dataset, model and library must be cited here (hackathon rule).

## Libraries

| Name | Type | Licence | Source URL | Used for |
|---|---|---|---|---|
| Next.js | Library | MIT | https://nextjs.org | Frontend |
| shadcn/ui | Library | MIT | https://ui.shadcn.com | UI components |
| FastAPI | Library | MIT | https://fastapi.tiangolo.com | API |
| Google Gen AI SDK | Library | Apache-2.0 | https://github.com/googleapis/python-genai | Gemini calls |
| H3 (h3-py) | Library | Apache-2.0 | https://github.com/uber/h3-py | Hexagonal grid (res 8, ~1 km) for evidence fusion |
| Earth Engine Python API | Library | Apache-2.0 | https://github.com/google/earthengine-api | Satellite + weather jobs aggregated to H3 |
| google-cloud-bigquery / -storage, firebase-admin | Library | Apache-2.0 | https://github.com/googleapis/google-cloud-python | Optional BigQuery / GCS / Firestore mirrors |
| httpx | Library | BSD-3-Clause | https://www.python-httpx.org | CPCB, Translation and TTS REST calls |
| Leaflet | Library | BSD-2-Clause | https://leafletjs.com | Map fallback when `NEXT_PUBLIC_MAPS_API_KEY` is empty |
| Google Maps JavaScript API | Service | Google Maps Platform ToS | https://developers.google.com/maps | Officer map when a Maps key is set |

## Datasets and services

| Name | Type | Licence / terms | Source URL | Used for |
|---|---|---|---|---|
| OpenStreetMap tiles | Map data / tiles | ODbL (data); OSMF Tile Usage Policy (tiles, light demo use only) | https://www.openstreetmap.org/copyright | Fallback basemap (attribution shown on map) |
| CPCB real-time AQI (data.gov.in resource 3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69) | Dataset (API) | Government Open Data Licence - India | https://data.gov.in | Official station readings (live when `DATA_GOV_IN_API_KEY` is set) |
| Sentinel-5P TROPOMI OFFL L3 NO2 (`COPERNICUS/S5P/OFFL/L3_NO2`) | Dataset | Copernicus Sentinel data terms (free, open) | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2 | NO2 column anomaly per cell |
| NASA FIRMS (`FIRMS`) | Dataset | NASA open data | https://developers.google.com/earth-engine/datasets/catalog/FIRMS | Active fires upwind |
| MODIS MAIAC AOD (`MODIS/061/MCD19A2_GRANULES`) | Dataset | NASA LP DAAC open data | https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES | Aerosol optical depth per cell |
| ERA5-Land hourly (`ECMWF/ERA5_LAND/HOURLY`) | Dataset | Copernicus C3S licence | https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY | Current wind, temperature, humidity |
| NOAA GFS 0.25 (`NOAA/GFS0P25`) | Dataset | NOAA public domain | https://developers.google.com/earth-engine/datasets/catalog/NOAA_GFS0P25 | 24/48/72 h weather forecast |
| India National AQI PM2.5 breakpoints | Standard | Public (CPCB) | https://cpcb.nic.in | AQI category labels |
| kappa-Kohler humidity correction (Crilley et al., 2018, AMT 11, 709-720) | Method | Paper (CC BY 4.0) | https://doi.org/10.5194/amt-11-709-2018 | Low-cost sensor calibration |

## Generated / sample data (not third-party)

Everything in `data/sample/` is **synthetic**, produced by `data/generate_sample.py` (fixed seed) or
hand-written (`ai_fixtures/advisory_templates.json`). Station names are real places, but the values are
**not** actual CPCB readings. Sample citizen photos are simple generated images, not real photographs.
