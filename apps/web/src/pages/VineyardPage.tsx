import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api, queryKeys } from "../api/client";
import { AdvisoryBanner } from "../components/AdvisoryBanner";
import { DiseaseCard } from "../components/DiseaseCard";
import { FrostCard } from "../components/FrostCard";
import { FrostChart } from "../components/FrostChart";
import { PhenologyCard } from "../components/PhenologyCard";
import { SmokeCard } from "../components/SmokeCard";
import type { ScoreRow } from "../types";

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
  const frostQ = useQuery<ScoreRow[]>({
    queryKey: queryKeys.scores(id, "frost"),
    queryFn: () => api.getScores(id, "frost", 72),
    enabled: Number.isFinite(id),
  });
  const dmQ = useQuery<ScoreRow[]>({
    queryKey: queryKeys.scores(id, "dm"),
    queryFn: () => api.getScores(id, "dm", 168),
    enabled: Number.isFinite(id),
  });
  const pmQ = useQuery<ScoreRow[]>({
    queryKey: queryKeys.scores(id, "pm"),
    queryFn: () => api.getScores(id, "pm", 168),
    enabled: Number.isFinite(id),
  });
  const botrytisQ = useQuery<ScoreRow[]>({
    queryKey: queryKeys.scores(id, "botrytis"),
    queryFn: () => api.getScores(id, "botrytis", 168),
    enabled: Number.isFinite(id),
  });
  const smokeQ = useQuery<ScoreRow[]>({
    queryKey: queryKeys.scores(id, "smoke"),
    queryFn: () => api.getScores(id, "smoke", 168),
    enabled: Number.isFinite(id),
  });

  // Phenology is per-block; for the card we show the first block of the
  // vineyard. Multi-block UX lands in Stage 01.
  const firstBlockId = vineyardQ.data?.blocks[0]?.id;
  const phenoQ = useQuery({
    queryKey: queryKeys.blockPhenology(firstBlockId ?? -1),
    queryFn: () => api.getBlockPhenology(firstBlockId!, 200),
    enabled: firstBlockId !== undefined,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4">
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
      </header>

      <section
        aria-label="Wedge overview"
        className="grid grid-cols-1 gap-4 md:grid-cols-2"
      >
        <FrostCard scores={frostQ.data ?? []} />
        <DiseaseCard
          dm={dmQ.data ?? []}
          pm={pmQ.data ?? []}
          botrytis={botrytisQ.data ?? []}
        />
        <SmokeCard scores={smokeQ.data ?? []} />
        <PhenologyCard states={phenoQ.data ?? []} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Frost forecast — next 72 h
        </h2>
        {forecastQ.data && frostQ.data ? (
          <FrostChart forecast={forecastQ.data} scores={frostQ.data} />
        ) : forecastQ.isLoading || frostQ.isLoading ? (
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
