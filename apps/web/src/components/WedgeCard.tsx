/**
 * Generic wedge card shell.
 *
 * Used by FrostCard / DiseaseCard / SmokeCard / PhenologyCard. Layout:
 *
 *     ┌──────────────────────┐
 *     │ Title       LevelChip│
 *     │ Key metric line      │
 *     │ [sparkline]          │
 *     └──────────────────────┘
 *
 * A bare `level` prop drives the chip; pass `level={null}` to suppress
 * (useful for phenology, which doesn't have a low/elevated/high band).
 */
import type { ReactNode } from "react";

import type { FrostLevel } from "../types";
import { LevelChip } from "./LevelChip";

interface WedgeCardProps {
  title: string;
  level: FrostLevel | null;
  metric: ReactNode;
  sparkline: ReactNode;
  detail?: ReactNode;
}

export function WedgeCard({
  title,
  level,
  metric,
  sparkline,
  detail,
}: WedgeCardProps): JSX.Element {
  return (
    <section className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <header className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          {title}
        </h3>
        {level !== null && <LevelChip level={level} />}
      </header>
      <div className="font-mono text-sm text-slate-700">{metric}</div>
      <div>{sparkline}</div>
      {detail !== undefined && (
        <div className="text-xs text-slate-500">{detail}</div>
      )}
    </section>
  );
}
