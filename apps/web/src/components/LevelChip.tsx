import clsx from "clsx";

import { LEVEL_COLORS, LEVEL_LABELS } from "../lib/format";
import type { FrostLevel } from "../types";

export function LevelChip({ level }: { level: FrostLevel }): JSX.Element {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        LEVEL_COLORS[level],
      )}
    >
      {LEVEL_LABELS[level]}
    </span>
  );
}
