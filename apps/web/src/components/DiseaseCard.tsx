/**
 * Disease wedge card — surfaces the worst-of (DM, PM, Botrytis) per day.
 * Each model carries its own `inputs`; we pluck the headline value off
 * each (DSV, GT index, infection probability) for the metric line.
 */
import { Sparkline } from "./Sparkline";
import { WedgeCard } from "./WedgeCard";
import type { FrostLevel, ScoreRow } from "../types";

const LEVEL_RANK: Record<FrostLevel, number> = {
  low: 0,
  elevated: 1,
  high: 2,
  extreme: 3,
};

interface Props {
  dm: ScoreRow[];
  pm: ScoreRow[];
  botrytis: ScoreRow[];
}

export function DiseaseCard({ dm, pm, botrytis }: Props): JSX.Element {
  const all = [...dm, ...pm, ...botrytis];
  const worst = all.reduce<ScoreRow | null>(
    (acc, s) =>
      acc === null || LEVEL_RANK[s.level] > LEVEL_RANK[acc.level] ? s : acc,
    null,
  );

  // Latest readings — last row of each wedge, if present.
  const dmLast = dm.at(-1);
  const pmLast = pm.at(-1);
  const botLast = botrytis.at(-1);
  const dsv = typeof dmLast?.inputs.dsv === "number" ? dmLast.inputs.dsv : null;
  const pmIdx = typeof pmLast?.inputs.index === "number" ? pmLast.inputs.index : null;
  const botProb =
    typeof botLast?.inputs.probability === "number"
      ? botLast.inputs.probability
      : null;

  return (
    <WedgeCard
      title="Disease"
      level={worst?.level ?? "low"}
      metric={
        all.length === 0 ? (
          <span className="text-slate-400">No disease data yet</span>
        ) : (
          <>
            DSV {dsv ?? "—"} · PM {pmIdx ?? "—"} · Bot{" "}
            {botProb !== null ? botProb.toFixed(2) : "—"}
          </>
        )
      }
      sparkline={
        <Sparkline
          values={dm.map((s) => s.score)}
          width={180}
          height={36}
          stroke="#0d9488"
          domain={[0, 1]}
          ariaLabel="downy mildew DSV trend"
        />
      }
      detail={<>DM (downy) · PM (powdery, BBCH ≥ 53) · Botrytis (post-bloom)</>}
    />
  );
}
