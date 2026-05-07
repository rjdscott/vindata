// Stage 00 hand-written type surface. In Stage 01 these are regenerated from
// /openapi.json by `openapi-typescript`; the shapes match exactly so the
// migration is a one-line swap of imports.

export type FrostLevel = "low" | "elevated" | "high" | "extreme";

export type Wedge = "frost" | "dm" | "pm" | "botrytis" | "smoke" | "pheno";

export interface VineyardSummary {
  id: number;
  slug: string;
  name: string;
  region: string;
  centroid: { lat: number; lon: number };
}

export interface Block {
  id: number;
  name: string;
  cultivar: string | null;
  elevation_m: number | null;
  aspect_deg: number | null;
  slope_deg: number | null;
}

export type VineyardDetail = VineyardSummary & { blocks: Block[] };

export interface ScoreRow {
  ts: string; // ISO8601
  lead_h: number;
  score: number;
  level: FrostLevel;
  wedge: Wedge;
  model_version: string;
  inputs: Record<string, number | string | boolean | null>;
}

export interface ForecastRow {
  valid_ts: string;
  init_ts: string;
  t2m: number | null;
  dewpoint: number | null;
  rh: number | null;
  wind_ms: number | null;
  wind_dir: number | null;
  precip_mm: number | null;
  cloud_frac: number | null;
  sw_rad: number | null;
}

export interface PhenologyStateRow {
  block_id: number;
  date: string; // ISO8601 date
  doy: number;
  chill_units: number;
  forcing_dd: number;
  gdd_from_budbreak: number;
  bbch: number;
  model_version: string;
}
