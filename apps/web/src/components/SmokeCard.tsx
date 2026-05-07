/**
 * Smoke wedge card. Surfaces 24 h PM2.5 dose with a 35 µg/m³ reference
 * line in the sparkline (the AU "Poor" air-quality threshold).
 */
import { Sparkline } from "./Sparkline";
import { WedgeCard } from "./WedgeCard";
import type { ScoreRow } from "../types";

export function SmokeCard({ scores }: { scores: ScoreRow[] }): JSX.Element {
  const latest = scores.at(-1);
  const pmMax =
    typeof latest?.inputs.pm25_max === "number" ? latest.inputs.pm25_max : null;
  const pmMean =
    typeof latest?.inputs.pm25_mean === "number" ? latest.inputs.pm25_mean : null;
  const dose = typeof latest?.inputs.dose === "number" ? latest.inputs.dose : null;

  // Sparkline plots PM2.5 max per day from the inputs JSON; if absent
  // (older cycles), fall back to the score column.
  const series = scores.map((s) =>
    typeof s.inputs.pm25_max === "number" ? s.inputs.pm25_max : null,
  );
  const fallback = series.every((v) => v === null);

  return (
    <WedgeCard
      title="Smoke"
      level={latest?.level ?? "low"}
      metric={
        scores.length === 0 ? (
          <span className="text-slate-400">No smoke data yet</span>
        ) : (
          <>
            PM2.5 mean{" "}
            <span className="text-base">{pmMean !== null ? pmMean.toFixed(0) : "—"}</span>{" "}
            µg/m³ · max {pmMax !== null ? pmMax.toFixed(0) : "—"} · dose{" "}
            {dose !== null ? dose.toFixed(0) : "—"}
          </>
        )
      }
      sparkline={
        <Sparkline
          values={fallback ? scores.map((s) => s.score) : series}
          width={180}
          height={36}
          stroke="#7c3aed"
          referenceY={fallback ? 0.5 : 35}
          ariaLabel="smoke PM2.5 trend"
        />
      }
      detail={<>Reference 35 µg/m³ "Poor" AU AQ band</>}
    />
  );
}
