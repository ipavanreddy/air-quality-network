export type Factor = {
  name: string;
  score: number;
  weight: number;
  contribution: number;
  detail: string;
  available: boolean;
};

export type Freshness = {
  signal: string;
  observed_at: string | null;
  age_minutes: number | null;
  source: string | null;
  is_sample: boolean;
};

export type GridCell = {
  h3_cell: string;
  lat: number;
  lon: number;
  boundary: [number, number][];
  pm25: number | null;
  category: string | null;
  confidence: number;
  band: string;
  land_use: string | null;
  report_count: number;
  fire_count_upwind_100km: number | null;
  hotspot_id: string | null;
};

export type Observation = {
  sensor_id: string;
  lat: number;
  lon: number;
  pm25_raw: number;
  pm25_calibrated: number;
  timestamp: string;
  is_simulated: boolean;
};

export type Grid = {
  state: string;
  name: string;
  center: [number, number];
  threshold: number;
  cells: GridCell[];
  sensors: Observation[];
  station: { name: string; pm25: number; lat: number; lon: number; observed_at: string; is_sample: boolean };
  weather: { wind_speed_ms: number; wind_dir_deg: number; humidity: number; boundary_layer_m: number | null };
  freshness: Freshness[];
  is_sample_data: boolean;
};

export type Evidence = { signal: string; value: string; source: string; observed: string };
export type Action = { action_id: string; action: string; priority: string };

export type Brief = {
  summary: string;
  risk_level: string;
  likely_sources: { type: string; confidence: number; rationale: string }[];
  evidence: Evidence[];
  forecast_outlook: string;
  recommended_actions: Action[];
  uncertainties: string[];
  confidence: number;
  requires_human_review: boolean;
};

export type Provenance = {
  model_name: string;
  model_version: string;
  prompt_version: string;
  mode: string;
  note?: string | null;
  validation_warnings?: string[];
};

export type CrossBoundary = {
  target_config: string;
  target_jurisdiction_id: string;
  target_name: string;
  distance_km: number;
  eta_hours: number;
  reason: string;
};

export type Alert = {
  alert_id: string;
  kind: "hotspot" | "cross_boundary";
  hotspot_id: string;
  state: string;
  jurisdiction_id: string;
  jurisdiction_name: string;
  origin_jurisdiction_id: string | null;
  sent_at: string;
  status: "pending_review" | "acknowledged" | "action_taken" | "closed";
  confidence: number;
  band: string;
  fast_path: boolean;
  action_brief: Brief;
  brief_provenance: Provenance;
  approved_action_ids: string[];
  action_taken: string | null;
  resolution: string | null;
  cross_boundary_suggestion: CrossBoundary | null;
  cross_boundary_alert_id: string | null;
  cross_boundary?: CrossBoundary;
  history: { at: string; actor: string; event: string; note: string }[];
  is_sample_data: boolean;
};

export type Hotspot = {
  hotspot_id: string;
  state: string;
  h3_cells: string[];
  peak_cell: string;
  center: [number, number];
  confidence: number;
  band: string;
  factors: Factor[];
  threshold: number;
  fast_path: boolean;
  status: string;
  alert_id: string | null;
  evidence_bundle?: {
    data_freshness: Freshness[];
    citizen_reports: { report_id: string; source_type: string; confidence: number; created_at: string }[];
  };
};

export type ForecastHorizon = {
  horizon_hours: number;
  pm25_low: number;
  pm25_expected: number;
  pm25_high: number;
  category: string;
  drivers: string[];
};

export type Forecast = {
  model_id: string;
  pm25_now: number;
  category_now: string;
  horizons: ForecastHorizon[];
  location_id: string;
  basis: string;
  is_sample_data: boolean;
};

export type Report = {
  report_id: string;
  location: { lat: number; lon: number };
  h3_cell: string;
  state: string | null;
  created_at: string;
  status: string;
  source_type?: string;
  confidence?: number;
  is_sample: boolean;
};

export type City = {
  id: string;
  name: string;
  city: string;
  corridor: string;
  center: [number, number];
  default_language: string;
  jurisdiction: { id: string; name: string; district: string };
  hotspot_threshold: number;
  forecast_model: string;
};

export type Analytics = {
  active_hotspots: number;
  alerts_by_status: Record<string, number>;
  cross_boundary_in: number;
  cross_boundary_out: number;
  citizen_reports: number;
  verified_reports: number;
};

export type Advisory = {
  advisory_id: string;
  state: string;
  category: string;
  status: "draft" | "approved";
  translations: Record<
    string,
    {
      headline: string;
      summary: string;
      protective_steps: string[];
      sensitive_groups: string;
      translation: { engine: string; mode: string };
    }
  >;
  provenance: Provenance;
  approved_by: string | null;
  created_at: string;
};

export type ModelCard = {
  id: string;
  name: string;
  type: string;
  used_by: string[];
  registry: string;
  card: Record<string, unknown>;
};

export type IntegrationStatus = {
  demo_mode: boolean;
  gemini_model: string;
  integrations: { name: string; label: string; mode: string; env_vars: string[]; demo_behaviour: string; last_error: string | null }[];
};
