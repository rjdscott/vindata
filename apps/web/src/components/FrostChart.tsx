import {
  Area,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatTime, formatTimeShort } from "../lib/format";
import type { ForecastRow, ScoreRow } from "../types";

interface Props {
  forecast: ForecastRow[];
  scores: ScoreRow[];
}

interface ChartPoint {
  ts: string;
  t2m: number | null;
  dewpoint: number | null;
  tmin_pred: number | null;
  score: number | null;
}

/**
 * Combines the hourly forecast (t2m, dewpoint) with the per-hour frost
 * prediction (tmin_pred from the inputs JSON, score) into a single chart.
 * The 0 °C line is highlighted.
 */
export function FrostChart({ forecast, scores }: Props): JSX.Element {
  const data: ChartPoint[] = forecast.map((f) => {
    const matched = scores.find((s) => s.ts === f.valid_ts);
    return {
      ts: f.valid_ts,
      t2m: f.t2m,
      dewpoint: f.dewpoint,
      tmin_pred: matched ? matched.score : null,
      score: matched ? matched.score : null,
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="ts"
            tickFormatter={formatTimeShort}
            stroke="#475569"
            fontSize={11}
            interval={Math.max(0, Math.floor(data.length / 8) - 1)}
          />
          <YAxis
            yAxisId="temp"
            stroke="#475569"
            fontSize={11}
            label={{ value: "°C", angle: -90, position: "insideLeft", fontSize: 11 }}
          />
          <YAxis
            yAxisId="score"
            orientation="right"
            domain={[0, 1]}
            stroke="#475569"
            fontSize={11}
            label={{ value: "score", angle: 90, position: "insideRight", fontSize: 11 }}
          />
          <Tooltip
            labelFormatter={(label: string) => formatTime(label)}
            formatter={(value: number, name: string) => [value?.toFixed?.(2), name]}
          />
          <ReferenceLine
            yAxisId="temp"
            y={0}
            stroke="#0ea5e9"
            strokeDasharray="4 4"
            label={{ value: "0 °C", fontSize: 10, fill: "#0ea5e9" }}
          />
          <Area
            yAxisId="temp"
            type="monotone"
            dataKey="t2m"
            name="t2m"
            stroke="#0ea5e9"
            fill="#0ea5e9"
            fillOpacity={0.12}
          />
          <Line
            yAxisId="temp"
            type="monotone"
            dataKey="dewpoint"
            name="dewpoint"
            stroke="#0284c7"
            strokeDasharray="3 3"
            dot={false}
          />
          <Line
            yAxisId="score"
            type="monotone"
            dataKey="score"
            name="frost score"
            stroke="#dc2626"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
