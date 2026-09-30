# Data

Every dataset (file or table) must carry: `source`, `reference_timestamp`, `dataset_version`,
`geographic_scope`, and `is_sample` / `is_synthetic`. Labelled in the UI as well.

- `schemas/`: canonical schema (PRD §21)
- `adapters/`: state adapters mapping state data → canonical schema (≥ 2 states)
- `sample/`: small, committed, labelled demo data
- `transformations/`: loaders into BigQuery

## What is here now

- `adapters/<state>.json`: Delhi NCR, Punjab and Maharashtra configs. Each holds the jurisdiction, hotspot threshold,
  action rules, languages, the shared model choice, cross-boundary neighbours and the vendor-feed field map.
- `schemas/canonical_cell_snapshot.schema.json`: the canonical grid-cell record (PRD §21).
- `sample/`: SIMULATED data from `generate_sample.py`
  (`cd services/api && uv run python ../../data/generate_sample.py`, fixed seed), plus AI fixtures in
  `sample/ai_fixtures/`.
