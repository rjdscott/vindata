/**
 * Phenology wedge card. No level chip — phenology is a *state* (BBCH),
 * not a risk band — so the card uses the BBCH stage name as its
 * headline rather than a Low/Elevated/High pill.
 */
import { Sparkline } from "./Sparkline";
import { WedgeCard } from "./WedgeCard";
import type { PhenologyStateRow } from "../types";

const STAGE_NAME: Array<[number, string]> = [
  [89, "Maturity"],
  [81, "Veraison"],
  [65, "Flowering"],
  [53, "Inflorescences emerging"],
  [9, "Budbreak"],
  [0, "Dormant"],
];

function bbchLabel(bbch: number): string {
  for (const [threshold, name] of STAGE_NAME) {
    if (bbch >= threshold) return name;
  }
  return "Dormant";
}

export function PhenologyCard({
  states,
}: {
  states: PhenologyStateRow[];
}): JSX.Element {
  const latest = states.at(-1);
  const bbch = latest?.bbch ?? 0;
  const gddPost = latest?.gdd_from_budbreak ?? 0;
  const chill = latest?.chill_units ?? 0;

  // Sparkline plots GDD-from-budbreak across the trace — visually shows
  // the season ramp-up. Pre-budbreak rows are null so the line starts
  // at the budbreak inflection.
  const values = states.map((s) =>
    s.bbch >= 9 ? s.gdd_from_budbreak : null,
  );

  return (
    <WedgeCard
      title="Phenology"
      level={null}
      metric={
        states.length === 0 ? (
          <span className="text-slate-400">No phenology data yet</span>
        ) : (
          <>
            BBCH <span className="text-base">{bbch}</span> · {bbchLabel(bbch)}
          </>
        )
      }
      sparkline={
        <Sparkline
          values={values}
          width={180}
          height={36}
          stroke="#16a34a"
          ariaLabel="GDD from budbreak"
        />
      }
      detail={
        states.length > 0 ? (
          <>
            Chill {chill.toFixed(0)} u · GDD post-budbreak {gddPost.toFixed(0)} °C·d
          </>
        ) : null
      }
    />
  );
}
