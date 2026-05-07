/**
 * Tiny pure-SVG sparkline. No recharts dependency — the wedge cards each
 * have one and we want them to render in <1 frame on a list view.
 *
 * Renders a polyline scaled to the component's width × height, with
 * optional horizontal reference line (e.g., 0 °C for frost, 35 µg/m³
 * for smoke). Non-numeric / null values are skipped.
 */
interface SparklineProps {
  values: ReadonlyArray<number | null>;
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
  ariaLabel?: string;
  /** Y-value at which to draw a dashed reference line (skipped if nullish). */
  referenceY?: number;
  /** Optional explicit y-domain (else min/max of values). */
  domain?: [number, number];
}

export function Sparkline({
  values,
  width = 120,
  height = 32,
  stroke = "#0ea5e9",
  fill = "none",
  ariaLabel = "trend",
  referenceY,
  domain,
}: SparklineProps): JSX.Element {
  const numeric = values.filter((v): v is number => typeof v === "number" && Number.isFinite(v));
  if (numeric.length < 2) {
    return (
      <div
        role="img"
        aria-label={ariaLabel}
        style={{ width, height }}
        className="text-xs text-slate-400"
      >
        n/a
      </div>
    );
  }
  const [yMin, yMax] = domain ?? [Math.min(...numeric), Math.max(...numeric)];
  const yRange = yMax - yMin || 1;

  const stepX = width / Math.max(1, values.length - 1);
  const points: string[] = [];
  values.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) return;
    const x = i * stepX;
    const y = height - ((v - yMin) / yRange) * height;
    points.push(`${x},${y}`);
  });

  const refY =
    referenceY !== undefined && referenceY >= yMin && referenceY <= yMax
      ? height - ((referenceY - yMin) / yRange) * height
      : null;

  return (
    <svg
      role="img"
      aria-label={ariaLabel}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="overflow-visible"
    >
      {refY !== null && (
        <line
          x1={0}
          x2={width}
          y1={refY}
          y2={refY}
          stroke="#94a3b8"
          strokeDasharray="2 2"
          strokeWidth={1}
        />
      )}
      <polyline
        points={points.join(" ")}
        fill={fill}
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
