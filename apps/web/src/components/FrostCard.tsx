/**
 * Frost wedge card. Required to be rendered inside a page that imports
 * AdvisoryBanner — enforced by the no-unwrapped-score ESLint rule.
 */
import { Sparkline } from "./Sparkline";
import { WedgeCard } from "./WedgeCard";
import type { ScoreRow } from "../types";
import { formatTimeShort } from "../lib/format";

export function FrostCard({ scores }: { scores: ScoreRow[] }): JSX.Element {
  const peak = scores.reduce<ScoreRow | null>(
    (acc, s) => (acc === null || s.score > acc.score ? s : acc),
    null,
  );

  return (
    <WedgeCard
      title="Frost"
      level={peak?.level ?? "low"}
      metric={
        peak ? (
          <>
            Peak score{" "}
            <span className="text-base">{peak.score.toFixed(2)}</span> @{" "}
            {formatTimeShort(peak.ts)}
          </>
        ) : (
          <span className="text-slate-400">No frost data yet</span>
        )
      }
      sparkline={
        <Sparkline
          values={scores.map((s) => s.score)}
          width={180}
          height={36}
          stroke="#dc2626"
          referenceY={0.5}
          domain={[0, 1]}
          ariaLabel="frost score 72h"
        />
      }
      detail={<>72 h frost score range; reference at 0.50</>}
    />
  );
}
