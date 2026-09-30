-- Analytics mirror written by services/api/app/core/store.py when GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET are set.
-- One append-only table; `payload` holds the canonical JSON record (report, hotspot, alert, advisory, observation).
CREATE TABLE IF NOT EXISTS `air_quality_network.records` (
  record_type STRING NOT NULL,   -- reports | hotspots | alerts | advisories | observations
  record_id   STRING NOT NULL,
  state       STRING,            -- config id, e.g. delhi-ncr
  recorded_at TIMESTAMP NOT NULL,
  payload     STRING NOT NULL    -- JSON
)
PARTITION BY DATE(recorded_at)
CLUSTER BY record_type, state;
