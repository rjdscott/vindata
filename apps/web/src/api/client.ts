// Stage 00 stub: hand-rolled fetch helpers. Stage 01 regenerates this file
// from /openapi.json via `openapi-typescript`.

import type {
  ForecastRow,
  ScoreRow,
  VineyardDetail,
  VineyardSummary,
  Wedge,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText} on ${path}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => getJson<{ status: string }>("/v1/health"),
  listVineyards: () => getJson<VineyardSummary[]>("/v1/vineyards"),
  getVineyard: (id: number) => getJson<VineyardDetail>(`/v1/vineyards/${id}`),
  getForecast: (id: number, hours = 72) =>
    getJson<ForecastRow[]>(`/v1/vineyards/${id}/forecast?hours=${hours}`),
  getScores: (id: number, wedge: Wedge = "frost", hours = 72) =>
    getJson<ScoreRow[]>(
      `/v1/vineyards/${id}/scores?wedge=${wedge}&hours=${hours}`,
    ),
};

export const queryKeys = {
  vineyards: ["vineyards"] as const,
  vineyard: (id: number) => ["vineyards", id] as const,
  forecast: (id: number) => ["vineyards", id, "forecast"] as const,
  scores: (id: number, wedge: Wedge) =>
    ["vineyards", id, "scores", wedge] as const,
};
