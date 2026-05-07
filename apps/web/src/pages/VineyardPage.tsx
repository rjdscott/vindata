import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api, queryKeys } from "../api/client";
import { AdvisoryBanner } from "../components/AdvisoryBanner";
import { FrostChart } from "../components/FrostChart";
import { LevelChip } from "../components/LevelChip";
import { formatTime } from "../lib/format";

export function VineyardPage(): JSX.Element {
  const { id: idParam } = useParams<{ id: string }>();
  const id = Number(idParam);

  const vineyardQ = useQuery({
    queryKey: queryKeys.vineyard(id),
    queryFn: () => api.getVineyard(id),
    enabled: Number.isFinite(id),
  });
  const forecastQ = useQuery({
    queryKey: queryKeys.forecast(id),
    queryFn: () => api.getForecast(id, 72),
    enabled: Number.isFinite(id),
  });
  const scoresQ = useQuery({
    queryKey: queryKeys.scores(id, "frost"),
    queryFn: () => api.getScores(id, "frost", 72),
    enabled: Number.isFinite(id),
  });

  const peak = (scoresQ.data ?? []).reduce<
    { score: number; level: import("../types").FrostLevel; ts: string } | null
  >((acc, s) => (acc === null || s.score > acc.score ? s : acc), null);

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4">
      <Link to="/" className="text-sm text-emerald-700 hover:underline">
        ← All vineyards
      </Link>

      <AdvisoryBanner />

      <header className="flex flex-wrap items-baseline justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{vineyardQ.data?.name ?? "…"}</h1>
          <div className="text-sm text-slate-500">
            {vineyardQ.data?.region} ·{" "}
            {vineyardQ.data &&
              `${vineyardQ.data.centroid.lat.toFixed(3)}, ${vineyardQ.data.centroid.lon.toFixed(3)}`}
          </div>
        </div>
        {peak && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">72 h peak:</span>
            <LevelChip level={peak.level} />
            <span className="font-mono text-slate-700">{peak.score.toFixed(2)}</span>
            <span className="text-slate-500">at {formatTime(peak.ts)}</span>
          </div>
        )}
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Frost forecast — next 72 h
        </h2>
        {forecastQ.data && scoresQ.data ? (
          <FrostChart forecast={forecastQ.data} scores={scoresQ.data} />
        ) : forecastQ.isLoading || scoresQ.isLoading ? (
          <div className="py-12 text-center text-slate-500">Loading forecast…</div>
        ) : (
          <div className="py-12 text-center text-slate-500">
            No forecast available yet — Dagster has not run.
          </div>
        )}
      </section>

      {vineyardQ.data && vineyardQ.data.blocks.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Blocks
          </h2>
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-1">Name</th>
                <th>Cultivar</th>
                <th>Elevation</th>
                <th>Slope</th>
                <th>Aspect</th>
              </tr>
            </thead>
            <tbody>
              {vineyardQ.data.blocks.map((b) => (
                <tr key={b.id} className="border-t border-slate-100">
                  <td className="py-1.5 font-medium">{b.name}</td>
                  <td>{b.cultivar ?? "—"}</td>
                  <td>{b.elevation_m ? `${b.elevation_m} m` : "—"}</td>
                  <td>{b.slope_deg ? `${b.slope_deg}°` : "—"}</td>
                  <td>{b.aspect_deg ? `${b.aspect_deg}°` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
