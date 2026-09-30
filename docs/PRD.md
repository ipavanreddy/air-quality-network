# AI-Powered Federated Hyper-local Air Quality & Climate Action Platform

## Product Requirements Document (PRD)

**Document Version:** 2.0 (aligned to the PRD 04 template)
**Working Name:** VayuDrishti (वायुदृष्टि)
**Track:** 2: Hyper-local pollution detection & federated climate action
**Product Type:** AI-powered Environmental Intelligence Platform / Interoperable Public Infrastructure
**Target Geography:** India (major cities and economic corridors)
**Primary User:** Environmental Officer (State Pollution Control Board / municipal clean-air cell)
**Secondary User:** Citizen Reporter
**Primary Objective:** Detect hyper-local pollution events that the official monitoring network misses, forecast air-quality spikes, and send evidence-backed alerts to the authority that can act, on an interoperable foundation that lets cities and states share models and coordinate.

---

# 1. Executive Summary

India's major cities monitor air quality through a limited number of official stations. These give a **macro-level** picture but miss **hyper-local events** such as industrial emissions at night, open burning of crop residue or waste, and construction dust. Seasonal smog then builds up across whole regions.

Useful signals already exist but are disconnected:

- Official monitoring stations
- Low-cost community sensors
- Citizen observations (photos of smoke, burning, dust)
- Satellite data (fires, NO₂, aerosols)
- Weather data (wind, humidity, boundary layer)

The proposed solution is an **AI-powered hyper-local air quality intelligence platform** that combines these signals to:

1. **Detect hidden pollution hotspots** on a fine grid.
2. **Identify the likely source type** with evidence.
3. **Forecast air-quality spikes** 24–72 hours ahead across economic corridors.
4. **Alert the relevant authority** with a clear, evidence-backed action brief.
5. **Let citizens report** pollution events by photo and receive health advisories in their language.
6. **Share predictive models** between cities and states through a common data and model structure.

The hackathon MVP will focus on a single, polished end-to-end journey:

> **Citizen Photo + Sensor + Satellite + Weather → AI Hotspot Detection → Likely Source → Forecast → Authority Alert → Action**

The prototype will also show that the same architecture supports several cities and states.

---

# 2. Problem Statement

## 2.1 Core Problem

Major Indian cities monitor macro-level air quality but consistently miss hyper-local pollution events.

Today, authorities often rely on:

- A sparse network of official monitoring stations
- City-wide averages
- Manual complaints that are hard to verify
- Reactive enforcement after pollution has peaked
- Limited cross-boundary coordination

This creates several risks:

- Pollution sources going undetected
- Delayed intervention
- Poor targeting of inspections
- No advance warning for pollution spikes
- Uncoordinated action across cities and states (e.g. transboundary smoke)
- Direct harm to public health

At the same time, useful data (satellite, weather, community sensors, citizen reports) exists but is not combined into actionable intelligence.

---

# 3. Challenge

The challenge is to build an **AI-powered, federated climate action platform** that:

- Combines **citizen-sourced data** (photos, local sensor readings) with **satellite imagery** and **meteorological data**.
- **Detects hidden pollution hotspots**.
- **Forecasts air-quality spikes** across major economic corridors.
- **Alerts relevant authorities** for rapid intervention.
- Is designed for **interoperability**, so Indian cities and states can **share predictive models and coordinate resources**.
- Uses AI meaningfully rather than as a generic chatbot.

---

# 4. Product Vision

> **Build an air-quality intelligence layer that finds pollution before the monitors do and tells the officer who can stop it.**

Long term, the platform should function as shared public infrastructure, where:

- Each city or state keeps its own sensor networks, data and local models.
- A common data contract defines how observations, events, forecasts and alerts are represented.
- Shared APIs expose hotspot, forecast and alert intelligence.
- Predictive models are portable because they consume standardised features.
- New cities are onboarded through data adapters rather than a rebuilt application.

---

# 5. Product Goals

## 5.1 Primary Goals

1. Combine at least four evidence types: citizen photos, sensor readings, satellite data and weather.
2. Use Google AI to verify and classify citizen photo reports.
3. Place all evidence on a common hyper-local grid.
4. Detect pollution hotspots with a transparent confidence score.
5. Suggest a likely source type with supporting evidence.
6. Forecast PM2.5 24–72 hours ahead for at least one corridor.
7. Generate evidence-backed alerts and action briefs for the responsible authority.
8. Deliver health advisories in regional languages.
9. Demonstrate a common data model and a shared model across at least two city/state configurations.
10. Deliver a working, deployed end-to-end prototype.

## 5.2 Secondary Goals

- Calibrate low-cost sensor readings against official stations.
- Track alert acknowledgment and action.
- Show cross-boundary alerts (e.g. crop-burning smoke travelling to a neighbouring city).
- Establish reusable air-quality intelligence APIs.

---

# 6. Non-Goals for the Hackathon MVP

The prototype will not attempt to become a complete regulatory system.

Out of scope for the MVP:

- Replacing official regulatory monitoring. Low-cost sensor data is labelled *indicative*.
- Enforcement, penalties or legal case management
- Industrial compliance / consent management
- Full chemical transport modelling
- Sensor hardware manufacturing or procurement
- Automated public-alert broadcasting without human approval
- Full federated learning infrastructure (roadmap)
- Carbon markets or emissions trading

---

# 7. Target Users

The MVP contains only two application roles.

## 7.1 Primary User: Environmental Officer

The Environmental Officer represents the State Pollution Control Board, a municipal clean-air cell or a district environment officer, scoped to their jurisdiction.

### Characteristics

- Responsible for inspection and intervention
- Limited field staff and time
- Needs prioritised, credible and location-specific information
- Must justify actions with evidence

### Primary Questions

The platform should help answer:

- Where is pollution unusually high right now?
- What is the likely source?
- How confident is the system?
- Will air quality get worse in the next 72 hours?
- Which location should my team inspect first?
- Is pollution coming from outside my jurisdiction?

---

## 7.2 Secondary User: Citizen Reporter

The citizen reporter contributes ground-level observations and receives health information.

### Characteristics

- Mobile-first
- May prefer a regional language
- Wants to report visible pollution quickly
- Wants to know whether the air is safe

### MVP Scope

The citizen experience is intentionally simple:

- Report pollution with a photo and location
- Receive confirmation and report status
- View local air-quality status and forecast
- Receive health advisories in their language (text and voice)

---

# 8. Core Product Experience

The product centres on one high-quality end-to-end journey:

```text
Citizen Reports Smoke (photo + location)
   ↓
AI Photo Verification & Classification
   ↓
Sensor Readings + Satellite Signals + Weather
   ↓
Hyper-local Air Quality Grid
   ↓
AI Hotspot Detection (confidence score)
   ↓
Likely Source Attribution
   ↓
72-hour Forecast
   ↓
AI Action Brief
   ↓
Alert to Environmental Officer
   ↓
Acknowledge → Inspect → Close
   ↓
Health Advisory to Citizens (regional language / voice)
```

This journey is the primary demonstration for the hackathon.

---

# 9. Module 1: Citizen Pollution Reporting

## Purpose

Let citizens report visible pollution events with a photo in a few seconds.

### Report Data

- Report ID
- Photo
- Location (GPS / pin)
- Timestamp
- Optional short description (text or voice)
- Preferred language

### Requirements

The system must allow a citizen or demo user to:

- Upload or take a photo.
- Share or confirm the location.
- Submit the report.
- Receive a confirmation and see the report's status.

---

# 10. Module 2: Sensor Data & Calibration

## Purpose

Bring official and community sensor readings into the platform and make low-cost readings more reliable.

### Inputs

- Official station readings (PM2.5, PM10, NO₂, SO₂, CO, O₃ where available)
- Low-cost community sensor readings (PM2.5, PM10, temperature, humidity)
- Sensor metadata (location, type, owner)

### Calibration

Low-cost sensors can over-read in high humidity. The MVP should:

- Apply a calibration model (Vertex AI or BigQuery ML regression) that corrects low-cost readings using humidity and temperature, trained on co-located official station data where available.
- Label calibrated low-cost readings as **indicative**.

### Requirement

Every reading keeps its source, sensor type, timestamp and calibration status.

---

# 11. Module 3: Satellite & Meteorological Intelligence

## Purpose

Add large-area evidence that ground sensors can't provide.

### Satellite Inputs (Google Earth Engine)

- Active fire detections (crop residue / open burning)
- NO₂ column (combustion / industrial)
- SO₂ and CO (industrial / combustion)
- Aerosol optical depth / aerosol index (smoke, dust, haze)
- Land cover (industrial, agricultural, urban)

### Meteorological Inputs

- Wind speed and direction
- Temperature
- Humidity
- Rainfall
- Boundary-layer height (where available)
- Forecast fields for the next 72 hours

### Requirement

Satellite and weather data are aggregated to the same hyper-local grid as sensor data, and each carries its observation date.

---

# 12. Module 4: Hyper-local Air Quality Grid

## Purpose

Combine all evidence onto one common spatial grid.

### Approach

- Use **H3 hexagonal cells** (about 1 km resolution) as the common unit.
- Each cell holds the latest sensor values, satellite signals, weather, citizen reports and forecast.

### Requirement

The grid must use at least four evidence categories in the MVP:

1. Citizen reports
2. Sensor readings
3. Satellite signals
4. Weather

---

# 13. Hotspot Confidence Score

The prototype should present an easy-to-understand hotspot confidence for each detected event.

Example:

```text
Hotspot Confidence
78 / 100
High
```

### Factors

- Sensor anomaly (how far above expected levels)
- Satellite signal (fire, NO₂, aerosol)
- Citizen reports (number, AI confidence, proximity)
- Weather plausibility (is the wind consistent with the source?)

### MVP Implementation

The score uses a **transparent weighted model**:

```text
Hotspot Confidence =
  Sensor Anomaly × 35%
+ Satellite Signal × 25%
+ Citizen Reports × 25%
+ Weather Plausibility × 15%
```

A hotspot becomes an alert when confidence passes a configurable threshold, or through a fast path when a severe, clearly visible event is reported.

### Future Evolution

The rule-based score can later be replaced or supplemented by a Vertex AI anomaly-detection model.

---

# 14. Module 5: AI Hotspot Detection & Source Attribution

## Purpose

Explain **what** is happening, **where**, and **what the likely source is**.

### Inputs

```json
{
  "cell": {},
  "sensor": {},
  "satellite": {},
  "weather": {},
  "citizen_reports": [],
  "land_use": {}
}
```

### Google AI Role

**Gemini** reasons over the structured evidence bundle and returns a ranked list of **likely source types** with evidence and confidence. It does not invent measurements.

### Source Types (MVP)

```text
crop_residue_burning · waste_burning · industrial_emission ·
construction_dust · traffic · other / unknown
```

### Example

```text
Likely Source: Industrial Emission
Confidence: Medium (0.64)

Evidence
• NO₂ column 42% above 30-day median
• 3 downwind sensors +110 µg/m³ between 02:00–05:00
• No fire detections nearby
• Industrial land use upwind

Recommended Action
Night-time inspection of the industrial area upwind of the affected cells.
```

### Safety Requirement

Attribution is a **likely source to guide inspection**, not an accusation. The interface must use terms such as "likely source" and "recommended inspection".

---

# 15. Module 6: Air Quality Forecasting

## Purpose

Predict air-quality spikes before they happen, so action can be taken early.

### Inputs

- Recent PM2.5 history
- Weather forecast (wind, humidity, temperature, boundary layer, rain)
- Fire activity upwind
- Satellite pollution signals
- Time features (hour, day, season, festivals)

### Output

- PM2.5 forecast for the next 24 / 48 / 72 hours per station and grid cell
- Forecast range (low / expected / high)
- Forecast air-quality category

### MVP Technical Approach

- A Vertex AI forecasting model (AutoML Forecasting or custom gradient boosting) for at least one corridor
- Compared against a simple baseline (persistence: "tomorrow looks like today")

### Example Output

```text
Forecast – East Delhi Corridor

Next 24h: Very Poor (PM2.5 ~ 210 µg/m³)
Next 48h: Severe (PM2.5 ~ 270 µg/m³)
Main drivers: calm winds, low boundary layer, upwind fire activity
```

---

# 16. Module 7: AI Alerts & Action Briefs

## Purpose

Turn a detected hotspot or forecast spike into a clear, actionable alert for the responsible authority.

### Flow

```text
Hotspot / Forecast Spike
        ↓
Jurisdiction Lookup (which city / district / board)
        ↓
Gemini Action Brief
        ↓
Alert to Environmental Officer (dashboard + email / messaging)
        ↓
Acknowledge → Action Taken → Close
```

### Action Brief Output

1. Situation summary
2. Location and affected area
3. Likely source and confidence
4. Supporting evidence (with data sources and times)
5. Forecast outlook
6. Recommended actions (configurable action rules, e.g. graded response stages)
7. Uncertainties
8. Data freshness

---

# 17. Module 8: Multilingual Health Advisories & Voice

## Purpose

Help citizens protect their health in their own language.

### MVP Languages

- English
- Hindi
- Punjabi

The architecture should support additional Indian languages through configuration only.

### Flow

```text
Forecast / Hotspot
     ↓
Gemini Health Advisory (structured)
     ↓
Translation
     ↓
Text + Text-to-Speech Audio
     ↓
Citizen
```

### Requirement

Advisories are generated once and then localised. Changing the language doesn't recompute the analysis. At least one complete voice advisory should be demonstrated.

---

# 18. Module 9: Environmental Officer Dashboard

## Purpose

Give officers one view of hotspots, forecasts and alerts in their jurisdiction.

### Dashboard Levels

```text
India
 ↓
State
 ↓
City / Corridor
 ↓
Ward / Grid Cell
```

### Dashboard Metrics

- Active hotspots
- Alerts (open / acknowledged / closed)
- Current air-quality levels
- 72-hour forecast
- Citizen reports
- Fire activity
- Cross-boundary events

### Map View

The dashboard should visualise:

- Hyper-local air-quality grid
- Hotspots with confidence
- Citizen reports
- Fire detections
- Forecast time-slider
- Wind direction

The MVP can use realistic sample data, clearly labelled, where live feeds are unavailable.

---

# 19. Module 10: Shared Model Registry

## Purpose

Show how cities and states **share predictive models** as the brief requires.

### Approach

- Forecasting and calibration models consume **standardised features** from the common data model.
- Models are registered in **Vertex AI Model Registry** with a model card (training region, period, accuracy, limitations).
- A second city/state configuration can **reuse** a registered model (e.g. a regional smog-season model) and fine-tune it on its own data.

### MVP Scope

- At least one model registered with a model card.
- At least two configurations using the shared model.

### Future

Federated learning (e.g. with the open-source Flower framework), so raw sensor data never leaves a city's node.

---

# 20. Module 11: Interoperability Layer

This is a core architectural requirement and a major differentiator of the solution.

## Objective

Provide a common data and service structure so different cities and states can participate, share models and coordinate without separate applications.

### Core Principle

> **City-specific data, common interfaces.**

Each city or state may have:

- Different sensor networks and vendors
- Different official monitoring data formats
- Different pollution sources and seasons
- Different action rules
- Different models

But the platform exposes a standardised canonical representation.

---

# 21. Common Air Quality Data Model

Example:

```json
{
  "state": "DL",
  "city": "Delhi",
  "cell_id": "H3-8-8a2a1072b59ffff",
  "timestamp": "2026-11-05T02:00:00+05:30",
  "observations": {
    "pm25_calibrated": 312,
    "pm25_source": "low_cost_sensor",
    "no2_column_anomaly_pct": 42,
    "fire_count_upwind_100km": 0,
    "aod": 1.2
  },
  "weather": {
    "wind_speed_ms": 1.1,
    "wind_dir_deg": 290,
    "humidity": 78,
    "boundary_layer_m": 220
  },
  "citizen_reports": 2,
  "hotspot": {
    "confidence": 0.78,
    "likely_source": "industrial_emission"
  },
  "forecast": {
    "pm25_24h": 290,
    "pm25_48h": 270
  }
}
```

The same structure should support examples such as:

```text
Delhi NCR → Industrial + traffic + winter smog
Punjab → Crop residue burning
Maharashtra (Mumbai–Pune) → Construction dust
```

The MVP does not need complete national coverage. It needs to prove that the architecture is city- and state-agnostic.

---

# 22. Interoperability Principles

## 22.1 Common Interfaces

City and state services expose compatible APIs.

## 22.2 Canonical Schema

Core concepts have common definitions for:

- Sensor
- Observation
- Grid Cell
- Citizen Report
- Hotspot / Event
- Forecast
- Alert
- Jurisdiction

## 22.3 City / State Data Adapters

An adapter transforms local sensor feeds and station formats into the canonical schema.

```text
City Dataset / Sensor Feed
     ↓
City Adapter
     ↓
Canonical Air Quality Schema
     ↓
Shared Platform Services
```

## 22.4 Model Portability

Forecasting and calibration models consume standardised features, so a model trained in one city can be reused in another.

## 22.5 Open Standards

- **H3** hexagonal grid for spatial interoperability
- **OGC SensorThings API**-compatible structure for sensor observations (target)
- **CAP (Common Alerting Protocol)**-aligned alert payloads for inter-agency and cross-boundary alerts

## 22.6 API-First Design

External government and partner applications should eventually be able to consume:

- Air-quality grid
- Hotspots
- Forecasts
- Alerts
- Health advisories

---

# 23. System Architecture

```text
      CITIZEN                 SENSORS / STATIONS          SATELLITE / WEATHER
         │                           │                            │
      Web/PWA                   Ingestion API               Earth Engine Jobs
         │                           │                            │
         └───────────────┬───────────┴────────────────────────────┘
                         ▼
                 Next.js Frontend / API Layer
                         │
    ┌──────────────┬─────┴────────┬───────────────┬──────────────┐
    ▼              ▼              ▼               ▼              ▼
 Report       Sensor &        Geospatial      Hotspot &      Forecast
 Service      Calibration     Service (GEE)   Attribution    Service
              Service                         Service
    │              │              │               │              │
    └──────────────┴──────┬───────┴───────────────┴──────────────┘
                          ▼
                 Air Quality Data Layer
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
    BigQuery          Firebase         Cloud Storage
        │
  ┌─────┴───────────────────────────┐
  ▼                                 ▼
Public Data                     City / State Data
 ├── Official stations           ├── Delhi
 ├── Satellite (GEE)             ├── Punjab
 ├── Weather                     ├── Maharashtra
 └── Land use                    └── Other Cities
  └──────────────┬──────────────────┘
                 ▼
            AI / ML Layer
                 │
     ┌───────────┼────────────┐
     ▼           ▼            ▼
  Gemini     Vertex AI     Gemini
 Reasoning   Forecast &    Multimodal
             Calibration   (photos)
     └───────────┼────────────┘
                 ▼
     Hotspot / Forecast / Action Brief
                 │
         ┌───────┴────────┐
         ▼                ▼
   Officer Alert    Citizen Advisory
                  (Translation + Voice)
```

---

# 24. Recommended Technology Stack

## 24.1 Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- PWA capabilities
- Google Maps JavaScript API (+ deck.gl H3 layer)

### Frontend Responsibilities

- Citizen report flow (photo, location)
- Local air-quality status and forecast
- Language switching and voice advisory playback
- Environmental Officer dashboard
- Hotspot map and forecast time-slider
- Alert inbox and action tracking

---

# 25. Backend

## Recommended

**Google Cloud Run** (+ Cloud Scheduler for periodic jobs, Pub/Sub for sensor streams)

Backend may be implemented using:

- FastAPI / Python for AI, geospatial and data services
- Node.js where application services benefit from it

### Responsibilities

- API routing
- Report intake
- Sensor ingestion and calibration
- Earth Engine data jobs
- Grid aggregation
- Hotspot detection and scoring
- Forecast serving
- Alert generation and routing
- City/state adapters
- Authentication / authorisation

---

# 26. Google AI Technology Stack

## Gemini Multimodal

Use for:

- Citizen photo verification (is this a pollution event?)
- Source-type classification from photos
- Visual severity estimation

## Gemini API / Vertex AI

Use for:

- Evidence reasoning and likely-source attribution
- Action briefs for officers
- Health advisories for citizens
- Explaining forecasts

## Vertex AI

Use for:

- PM2.5 forecasting
- Low-cost sensor calibration
- Model registry and shared models
- Model training and serving

## Google AI Studio

Use for:

- Prompt experimentation
- Evaluating photo classification behaviour
- Initial prompt development

---

# 27. Geospatial Stack

## Google Earth Engine

- Active fire detections
- Satellite NO₂, SO₂, CO, aerosol
- Land cover
- Historical weather reanalysis and forecast fields
- Aggregation to the H3 grid

## Google Maps Platform

- Location capture
- Hotspot and grid visualisation
- Jurisdiction context
- Air Quality API as an optional comparison layer (subject to its terms of use)

---

# 28. Data Platform

## BigQuery

Primary analytical store for:

- Sensor observations
- Satellite-derived grid data
- Weather data
- Hotspots and events
- Forecasts
- Alerts and actions
- Model features

## Firebase

Use for:

- Authentication (officers)
- Citizen report status
- Real-time alert updates

## Cloud Storage

Use for:

- Citizen photos
- Model artifacts
- Exported reports

---

# 29. Public Data Sources

The architecture should be able to consume data from sources such as:

- **CPCB** official monitoring station data (data.gov.in real-time air-quality API)
- **Sentinel-5P** NO₂, SO₂, CO, aerosol index (Earth Engine)
- **FIRMS** active fire detections (Earth Engine)
- **MODIS** aerosol optical depth (Earth Engine)
- **ERA5 / GFS** weather reanalysis and forecast (Earth Engine)
- **IMD** and national meteorological services
- **ESA WorldCover / Dynamic World** land cover (Earth Engine)
- State pollution control board open data where available

Where live APIs are unavailable during the hackathon, use realistic sample or cached public data.

Every dataset must keep its source metadata and timestamps.

---

# 30. Data Architecture

```text
Citizen Reports   Sensors / Stations   Satellite (GEE)   Weather
      │                  │                   │              │
      ▼                  ▼                   ▼              ▼
                     Data Ingestion
                           │
                           ▼
                Validation / Calibration
                           │
                           ▼
              City / State Adapter (where needed)
                           │
                           ▼
            Canonical Air Quality Schema (H3 grid)
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
          BigQuery                Feature Data
              │                         │
              └────────────┬────────────┘
                           ▼
                   AI / ML Services
                           │
                           ▼
          Hotspots / Forecasts / Alerts / Advisories
```

---

# 31. Core Data Entities

## Sensor

```text
sensor_id
type (official / low_cost)
owner
city
state
location
h3_cell
installed_at
```

## Observation

```text
sensor_id
timestamp
pm25_raw
pm25_calibrated
pm10
no2
temperature
humidity
calibration_model_version
source
```

## Grid Cell Snapshot

```text
h3_cell
timestamp
pm25_estimate
no2_column
aod
fire_count_upwind
wind_speed
wind_dir
humidity
boundary_layer
citizen_report_count
source_freshness
```

## Citizen Report

```text
report_id
reporter_id (pseudonymous)
photo_url
location
h3_cell
created_at
is_pollution_event
source_type
visual_severity
confidence
model_name
model_version
prompt_version
status
```

## Hotspot

```text
hotspot_id
h3_cells[]
detected_at
confidence
likely_sources
evidence
jurisdiction_id
status
model_name
model_version
prompt_version
```

## Forecast

```text
location_id (station / h3_cell)
issued_at
horizon_hours
pm25_low
pm25_expected
pm25_high
model_name
model_version
```

## Alert

```text
alert_id
hotspot_id / forecast_id
jurisdiction_id
action_brief
sent_at
acknowledged_at
action_taken
closed_at
language
model_name
model_version
prompt_version
```

---

# 32. AI Orchestration Architecture

AI services follow a predictable pipeline.

```text
New Evidence (report / sensor / satellite / weather)
      ↓
Retrieve Grid Cell Context
      ↓
Validate Data (freshness, calibration)
      ↓
Gemini Multimodal (for citizen photos)
      ↓
Hotspot Confidence Score (deterministic)
      ↓
Vertex AI Forecast
      ↓
Gemini Reasoning: Likely Source + Action Brief
      ↓
Structured JSON Output
      ↓
Validation (numbers grounded in evidence)
      ↓
Jurisdiction Routing
      ↓
Localisation (advisories)
      ↓
Presentation / Alert / Voice
```

The AI layer never depends on uncontrolled free text as its only source of context.

---

# 33. Structured AI Output

AI services return structured outputs rather than free text.

## Photo Verification

```json
{
  "is_pollution_event": true,
  "source_type": "crop_residue_burning",
  "visual_severity": 4,
  "observed_indicators": ["open flames", "dense grey smoke", "stubble rows"],
  "confidence": 0.87,
  "image_quality_ok": true,
  "requires_human_review": false
}
```

## Action Brief

```json
{
  "summary": "Probable industrial emission affecting 4 cells in East Delhi.",
  "risk_level": "high",
  "likely_sources": [
    { "type": "industrial_emission", "confidence": 0.64 },
    { "type": "traffic", "confidence": 0.21 }
  ],
  "evidence": [
    { "signal": "NO2 column anomaly", "value": "+42%", "source": "Sentinel-5P", "observed": "2026-11-04" }
  ],
  "forecast_outlook": "Likely to worsen over next 48h due to calm winds.",
  "recommended_actions": [
    { "action": "Night-time inspection of upwind industrial area", "priority": "high" }
  ],
  "uncertainties": ["No official station within 3 km"],
  "confidence": 0.7,
  "requires_human_review": true
}
```

---

# 34. Prompt Architecture

Use specialised prompts for distinct capabilities.

## 34.1 Photo Verification Prompt

### Inputs

- Photo
- Location and time
- Nearby land use (if available)

### Requirements

- Decide whether the photo shows a pollution event.
- Classify the source type from a fixed list.
- Describe visible evidence.
- Provide confidence.
- Flag low-quality or irrelevant images.
- Return structured JSON.

## 34.2 Source Attribution & Action Brief Prompt

### Inputs

- Grid cell evidence bundle
- Weather and wind direction
- Fire detections
- Citizen reports
- Forecast
- Action rules for the jurisdiction

### Requirements

- Reason only from supplied evidence.
- Return likely sources, not certainties.
- Cite the source and time for each piece of evidence.
- Recommend actions from the configured action rules.
- State uncertainties and missing data.
- Return structured JSON.

## 34.3 Health Advisory Prompt

### Inputs

- Current and forecast air-quality category
- Location
- Target audience (general / sensitive groups)

### Requirements

- Use simple, non-alarming language.
- Give practical protective steps.
- Return structured JSON for localisation.

---

# 35. AI Safety & Trust

The platform must distinguish between:

```text
Observed Data
      ↓
AI Interpretation
      ↓
Recommendation
```

### Requirements

- Never fabricate sensor, satellite or weather values.
- Never present a likely source as a confirmed polluter.
- Label low-cost sensor data as indicative.
- Include confidence for hotspots, sources and photo classification.
- Show data freshness for every signal.
- Require an officer's acknowledgment before any action is recorded.
- Don't send public alerts without human approval.

---

# 36. Data Freshness

Every data source should expose freshness metadata.

Example:

```text
Sensor (low-cost, calibrated)
Updated: 4 minutes ago

Official Station
Updated: 1 hour ago

Satellite NO₂
Observed: yesterday

Fire Detections
Observed: 6 hours ago

Weather Forecast
Issued: 3 hours ago
```

The officer should understand whether a hotspot is based on:

- Current data
- Recent satellite passes
- Latest available observation

---

# 37. API Architecture

## Citizen Reports

```http
POST /api/reports
GET  /api/reports/:id
```

## Sensors & Observations

```http
POST /api/sensors/:id/observations
GET  /api/sensors?city=
```

## Grid & Intelligence

```http
GET /api/grid?city=&time=
GET /api/cells/:id
GET /api/cells/:id/forecast
```

## Hotspots & Alerts

```http
GET  /api/hotspots?city=&status=
GET  /api/hotspots/:id
POST /api/hotspots/:id/brief
GET  /api/alerts?jurisdiction=
POST /api/alerts/:id/acknowledge
POST /api/alerts/:id/close
```

## Language / Voice

```http
POST /api/advisories/generate
POST /api/translate
POST /api/text-to-speech
```

## Models / Cities / Analytics

```http
GET /api/models
GET /api/models/:id/card
GET /api/cities
GET /api/cities/:id/analytics
```

---

# 38. Functional Requirements

## FR-01: Citizen Photo Report

The system must allow a citizen or demo user to submit a pollution report.

### Acceptance Criteria

- Photo upload works.
- Location is captured or confirmed.
- A report ID is returned.

---

## FR-02: AI Photo Verification

### Acceptance Criteria

- Photo is sent to Gemini multimodal.
- Pollution event yes/no, source type and confidence are returned.
- Visible indicators are displayed.
- Irrelevant images are flagged.

---

## FR-03: Sensor Ingestion & Calibration

### Acceptance Criteria

- Sensor readings can be ingested via the API.
- Calibrated values are stored alongside raw values.
- Low-cost readings are labelled indicative.

---

## FR-04: Satellite & Weather Integration

### Acceptance Criteria

At least these inputs are aggregated to the grid:

- Fire detections
- NO₂ or aerosol signal
- Wind and humidity

---

## FR-05: Hotspot Detection

### Acceptance Criteria

- Hotspots are detected from grid data.
- Hotspot confidence is displayed with a factor breakdown.
- At least four evidence types contribute.

---

## FR-06: Source Attribution

### Acceptance Criteria

- Likely sources are ranked with confidence.
- Evidence is listed with source and time.
- Language uses "likely" / "recommended inspection".

---

## FR-07: Forecasting

### Acceptance Criteria

- 24 / 48 / 72-hour PM2.5 forecast is displayed for at least one corridor.
- Forecast range is shown.
- Accuracy compared with a persistence baseline is documented.

---

## FR-08: Alert & Action Brief

### Acceptance Criteria

- An alert is routed to the correct jurisdiction.
- The action brief includes a summary, evidence, recommended actions and uncertainties.
- The officer can acknowledge and close the alert.

---

## FR-09: Multilingual Health Advisory

### Acceptance Criteria

- Advisory is displayed in English, Hindi and Punjabi.
- At least one advisory is played as audio.
- The meaning is retained across languages.

---

## FR-10: Environmental Officer Dashboard

### Acceptance Criteria

Officer can view:

- Hyper-local grid map
- Hotspots with confidence
- Forecast time-slider
- Alert inbox
- Citizen reports

---

## FR-11: Interoperability & Shared Models

### Acceptance Criteria

The prototype demonstrates:

- Canonical air-quality schema.
- At least two city/state configurations.
- Local data mapped into the common model.
- At least one registered model with a model card, reused by a second configuration.
- A cross-boundary alert between two configurations.

---

# 39. Non-Functional Requirements

## Performance

- Fast initial application load
- Standard API response under about 2 seconds where practical
- Corroborated citizen report → alert within minutes
- Clear loading states for AI operations

## Scalability

The system should support:

- Multiple cities and states
- Thousands of sensors
- Continuous satellite and weather updates
- Horizontal cloud scaling

## Reliability

- Handle satellite gaps (clouds, night) gracefully by relying on other evidence.
- Keep working if one data source fails, and show which sources are missing.
- Cache satellite and weather layers.
- Buffer sensor data through queues so it isn't lost.

## Accessibility

- Mobile-first citizen experience
- Regional-language capable
- Voice-capable advisories
- Simple officer workflows

## Security

- HTTPS
- Protect API secrets
- Authenticated sensor ingestion
- Role-based access
- Secure uploaded photos
- Least-privilege cloud permissions

---

# 40. City / State Onboarding Architecture

A new city or state can be onboarded without rewriting the core application.

## Onboarding Flow

```text
Register City / State
      ↓
Define Boundary & Jurisdictions
      ↓
Register Sensor & Station Feeds
      ↓
Map Local Fields to Canonical Schema
      ↓
Validate Data
      ↓
Configure Action Rules & Languages
      ↓
Select / Fine-tune Shared Model
      ↓
Enable APIs & Alerts
      ↓
City Becomes Available
```

## Example

```text
City: Ludhiana (Punjab)

Local Sensor Feed + Official Stations
     ↓
Punjab Adapter
     ↓
Canonical Schema
     ↓
Shared Forecast Model (fine-tuned) + Shared AI Services
```

Satellite and weather layers are available for any Indian city from day one, even before local sensors are connected.

---

# 41. Repository Structure

```text
air-quality-network/
│
├── apps/
│   ├── citizen-web/
│   └── officer-dashboard/
│
├── services/
│   ├── api/
│   ├── reports/
│   ├── sensors-calibration/
│   ├── geospatial-gee/
│   ├── hotspots/
│   ├── forecasting/
│   ├── alerts/
│   └── localization/
│
├── ai/
│   ├── prompts/
│   ├── schemas/
│   ├── models/
│   └── evaluation/
│
├── data/
│   ├── schemas/
│   ├── adapters/
│   ├── sample/
│   └── transformations/
│
├── infrastructure/
│   ├── cloud-run/
│   ├── bigquery/
│   └── firebase/
│
├── docs/
│
└── README.md
```

---

# 42. MVP Data Strategy

Prioritise **real or realistic** data over complicated ingestion.

## Use real / public data where feasible

- Official station history (CPCB)
- Satellite layers (Earth Engine)
- Weather reanalysis / forecast (Earth Engine)
- Fire detections

## Use realistic sample data where needed

- **Low-cost sensor feeds**: simulate them from official station patterns with realistic noise and humidity bias, **clearly labelled simulated**.
- **Citizen photos**: team-captured or openly licensed photos.
- **Alerts / actions**: sample workflow data.

## Data Source Metadata

Every dataset retains:

- Source
- Observation timestamp
- Dataset version
- Geographic scope
- "Simulated / sample" flag where applicable

---

# 43. Recommended MVP Demo Scenarios

## Scenario A

```text
State: Delhi NCR
Area: East Delhi industrial + traffic corridor
Language: Hindi
Event: Night-time industrial emission + winter smog forecast
```

## Scenario B

```text
State: Punjab
District: Sangrur / Ludhiana
Language: Punjabi
Event: Crop residue burning → cross-boundary smoke alert to Delhi
```

## Scenario C

```text
State: Maharashtra
Corridor: Mumbai–Pune
Language: English
Event: Construction dust hotspot
```

The number of demo cities doesn't matter much. The point is to prove that one platform structure supports different city, source and language combinations.

---

# 44. Hackathon Demo Flow

The demo should be one continuous story rather than a collection of disconnected features.

## 0:00–0:30: Introduce the Problem

> An official station 6 km away reads "Poor", but residents near an industrial area are breathing far worse air at 3 a.m.

## 0:30–1:10: Citizen Report

Show:

- Photo upload
- Gemini verification: event type, severity, confidence

## 1:10–1:50: Evidence Fusion

Show:

- Sensor anomaly
- Satellite NO₂ / fire signal
- Wind direction
- Hotspot confidence score and breakdown

## 1:50–2:30: Likely Source & Action Brief

Generate a Gemini action brief with evidence, a likely source and a recommended inspection.

## 2:30–3:00: Forecast

Show the 72-hour corridor forecast and its drivers.

## 3:00–3:30: Officer Alert

Show the alert arriving, the officer acknowledging it and the action being recorded.

## 3:30–3:50: Citizen Advisory

Show a Hindi / Punjabi health advisory with voice playback.

## 3:50–4:30: Interoperability & Shared Models

Switch to Punjab: crop-burning hotspot → cross-boundary alert to Delhi. Show the shared model card reused in both configurations.

## 4:30–5:00: Scale & Deployment

```text
One Street
   ↓
One Ward
   ↓
One City
   ↓
One Corridor
   ↓
Multiple States
   ↓
National Air Quality Intelligence Network
```

Show the Google AI / Cloud stack powering the solution.

---

# 45. Deployment Architecture

```text
                         Internet
                            │
                            ▼
                    Google Cloud Platform
                            │
                         Cloud Run
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     Next.js App       API Layer         AI Services
          │                 │                 │
          │         Pub/Sub + Scheduler       │
          ▼                 ▼                 ▼
       Firebase         BigQuery          Vertex AI
                                              │
                                              ▼
                                           Gemini
                            │
                            ▼
                      External Data
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    CPCB / Stations    Earth Engine      City Sensor APIs
```

Primary region: `asia-south1` (Mumbai).

---

# 46. Environment & Secrets

Secrets must never be committed to GitHub.

Example configuration:

```text
GEMINI_API_KEY
GOOGLE_CLOUD_PROJECT
GOOGLE_APPLICATION_CREDENTIALS
BIGQUERY_DATASET
FIREBASE_PROJECT_ID
EARTH_ENGINE_PROJECT
MAPS_API_KEY
DATA_GOV_IN_API_KEY
SENSOR_INGEST_TOKEN
```

Store them in Secret Manager for Cloud Run.

---

# 47. Observability

The system should log:

- API latency
- AI request latency
- AI failures and schema-validation failures
- Sensor ingestion gaps
- Satellite / weather job failures
- Dataset freshness
- Model and prompt version
- Hotspot detection events
- Alert delivery, acknowledgment and closure times

Future production metrics:

- Hotspots detected outside official station coverage
- Alert-to-action time
- Forecast accuracy over time
- Citizen reporting activity

---

# 48. AI Evaluation

A basic internal evaluation layer should test:

## Photo Verification

- Agreement with a small labelled photo set
- False-positive rate (non-pollution images)

## Sensor Calibration

- Error reduction against official co-located readings

## Hotspot Detection

- Agreement with known historical events (e.g. crop-burning season, festival spikes)

## Forecasting

- Accuracy compared with a persistence baseline (internal target: clearly better at 24 h)

## Action Briefs & Advisories

- Evidence adherence (every number traceable)
- Actionability
- Translation quality

The hackathon MVP doesn't need a formal scientific evaluation system, but the architecture should make evaluation possible.

---

# 49. Success Metrics

## 49.1 Hackathon Success

The prototype should demonstrate:

- Complete end-to-end evidence → alert flow
- Meaningful Google AI integration
- Four evidence types fused on a common grid
- Working photo verification
- Explainable hotspot confidence
- Likely-source attribution with evidence
- Corridor forecast
- Officer alert with acknowledgment
- Multilingual voice advisory
- Multiple city/state configurations
- Shared model with model card
- Public deployment
- Public or access-granted GitHub repository

## 49.2 Long-Term Impact Metrics

### Public Health Impact

- Population covered by hyper-local forecasts
- Advisories delivered
- Reduction in exposure during spike events

### Governance Impact

- Hotspots detected that the official network missed
- Alert-to-action time
- Inspections guided by the platform

### Platform Impact

- Cities and states integrated
- Sensors connected
- Shared models reused
- API consumers

---

# 50. Scalability Strategy

## Phase 1: Hackathon

```text
2–3 city/state configurations
1 forecast corridor
3 languages
Real satellite/weather + realistic sensor data
```

## Phase 2: City Pilot

```text
1 city clean-air cell + pollution control board
10–20 low-cost sensors co-located for calibration
Live alerts to field teams
```

## Phase 3: State Deployment

```text
Multiple cities
State-specific models
Integration with official alert and action workflows
More languages
```

## Phase 4: National Network

```text
Clean-air programme cities across India
Shared data contracts
Shared model registry
Cross-state (transboundary) alert exchange
Federated learning
```

---

# 51. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Satellite gaps (cloud, night) | Multi-source fusion. Confidence reflects missing data. |
| Low-cost sensor drift | Calibration and periodic recalibration against official stations |
| False or irrelevant photo reports | Gemini verification plus corroboration before alerting |
| Wrong source attribution | "Likely source" framing, confidence, evidence list, inspection recommendation only |
| Forecast underperforms | Report accuracy honestly against a baseline, and focus the demo on detection and alerting |
| Incomplete live data | Realistic simulated feeds, clearly labelled, with freshness shown |
| City data incompatibility | Canonical schema + city/state adapters |
| High AI cost | Call Gemini only for verified events and briefs, and cache layers |
| Vendor coupling | Abstract AI and data providers behind internal service interfaces |

---

# 52. Security & Privacy

## Citizen Data

Collect only what the product needs. Reporters are pseudonymous.

## Location Data

Report locations are used for hotspot detection. Precise reporter locations aren't exposed publicly.

## Photos

Store securely with retention controls. Blur faces and number plates before any public display (roadmap).

## Access Control

The MVP supports two roles:

```text
Environmental Officer (scoped by jurisdiction)
Citizen Reporter
```

Role permissions should ensure:

- Citizens see their own reports and public air-quality information.
- Officers see detailed hotspots and alerts only for their authorised jurisdiction.

---

# 53. Future Roadmap

## Air Quality Intelligence

- Federated learning across cities
- Construction-site detection from satellite imagery
- Action-effectiveness analysis (did air quality improve after intervention?)
- Personal exposure alerts along commute routes

## Government Intelligence

- Graded response automation with approval workflows
- Inter-state coordination dashboards
- Health-system early warning (hospital preparedness)

## Ecosystem

- Open air-quality intelligence APIs
- Community sensor network onboarding
- Research datasets
- Model marketplace for cities

---

# 54. Google AI Integration Map

| Google Technology | Product Role |
|---|---|
| Gemini Multimodal | Citizen photo verification and source classification |
| Gemini API | Source attribution reasoning, action briefs, health advisories |
| Vertex AI | Forecasting, sensor calibration, model registry and serving |
| Google AI Studio | Prompt experimentation and evaluation |
| Google Earth Engine | Fire, NO₂, aerosol, land cover, weather layers |
| BigQuery | Observations, grid data, hotspots, forecasts, analytics |
| Firebase | Authentication, report status, real-time alerts |
| Cloud Run | Backend, AI and data services |
| Google Maps Platform | Location capture and hotspot visualisation |
| Text-to-Speech | Spoken health advisories |
| Translation API | Multilingual advisories |

---

# 55. Alignment with Hackathon Evaluation

## Problem-Solution Fit: 20%

The product directly addresses:

- Missed hyper-local pollution events
- Lack of granular, real-time data
- Absence of early warning
- Slow, uncoordinated intervention
- Public health risk

## AI / Technical Execution: 25%

The prototype shows meaningful roles for:

- Gemini multimodal (photo verification)
- Gemini reasoning (attribution and briefs)
- Vertex AI (forecasting, calibration, model registry)
- Earth Engine (satellite evidence)
- Structured AI orchestration

## Depth & Reach Across India: 20%

The architecture shows:

- A city- and state-independent data model
- Satellite coverage for all of India from day one
- Multi-city configuration
- Multi-language advisories
- Cross-boundary coordination

## Impact Potential: 15%

The solution targets urban and peri-urban populations in India's most polluted corridors, where air pollution is a leading public health risk.

## Deployability & Scalability: 20%

The prototype shows:

- Cloud-native services
- API-first architecture
- City/state adapters
- Standardised schemas
- Shared, portable models
- A deployable application

---

# 56. Definition of Done: Hackathon MVP

## Citizen Experience

- [ ] Citizen can submit a photo report with a location.
- [ ] Citizen receives confirmation and status.
- [ ] Citizen can view local air-quality status and forecast.

## AI Experience

- [ ] Gemini multimodal verifies and classifies photos.
- [ ] Sensor calibration is applied.
- [ ] Satellite and weather data are shown on the grid.
- [ ] Hotspot confidence is displayed with a breakdown.
- [ ] Likely source is displayed with evidence and confidence.
- [ ] Forecast is displayed for at least one corridor.
- [ ] Gemini generates an action brief.

## Language & Voice

- [ ] English supported.
- [ ] Hindi supported.
- [ ] Punjabi supported.
- [ ] At least one voice health advisory works.

## Environmental Officer

- [ ] Officer dashboard exists.
- [ ] Hotspot map is visible.
- [ ] Alert inbox works (acknowledge / close).
- [ ] Data freshness is visible.

## Interoperability

- [ ] Canonical schema is documented.
- [ ] At least two city/state configurations exist.
- [ ] Local data maps to the common schema.
- [ ] A shared model with a model card is reused.
- [ ] A cross-boundary alert is demonstrated.

## Deployment & Submission

- [ ] Prototype is publicly deployed.
- [ ] Source code is available through GitHub.
- [ ] README contains setup and architecture documentation.
- [ ] Demo data is available and labelled.
- [ ] 3–5 minute demo video is prepared.
- [ ] 10–12 slide pitch deck is prepared.
- [ ] 2–3 line product description is prepared.

---

# 57. Recommended Build Priority

Prioritise **one polished end-to-end journey over many disconnected features**.

## Priority 1: Core Experience

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

## Priority 2: Prediction & Accessibility

```text
Corridor Forecast
 ↓
Multilingual Voice Advisory
```

## Priority 3: Scale Story

```text
Officer Dashboard
 ↓
Multi-city configurations
 ↓
Shared model + cross-boundary alert
```

## Priority 4: Future / Optional

```text
Sensor calibration model (use a simple correction if time is short)
Federated learning
Action-effectiveness analytics
```

Don't sacrifice the core evidence-to-alert journey to add lower-priority features.

---

# 58. Final Product Definition

The solution is an **AI-powered interoperable hyper-local air quality intelligence network** for India.

At the ground level:

```text
   CITIZEN PHOTO    SENSORS    SATELLITE    WEATHER
         │             │           │           │
         └─────────────┴─────┬─────┴───────────┘
                             ▼
                   HYPER-LOCAL GRID (H3)
                             │
                             ▼
                      AI AIR BRAIN
               Gemini + Vertex AI + Earth Engine
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
          Hotspot       Likely Source     Forecast
             │               │               │
             └───────────────┼───────────────┘
                             ▼
              Officer Alert + Citizen Advisory
                             │
                             ▼
                        RAPID ACTION
```

At the infrastructure level:

```text
       NATIONAL AIR QUALITY NETWORK
                    │
           COMMON DATA MODEL
                    │
       ┌────────────┼────────────┐
       │            │            │
     Delhi        Punjab     Maharashtra
       │            │            │
   Local Data   Local Data   Local Data
       │            │            │
       └────────────┼────────────┘
                    │
      Shared Models + Shared AI Services
                    │
      Shared APIs + Cross-boundary Alerts
```

The platform combines:

**Citizen sensing + satellite intelligence + AI reasoning + predictive modelling + multilingual advisories + interoperable climate infrastructure**

in one scalable architecture.

The hackathon MVP should prove that the solution can move from:

> **One street → One ward → One city → One corridor → Multiple Indian states**
