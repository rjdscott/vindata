import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DiseaseCard } from "./DiseaseCard";
import { FrostCard } from "./FrostCard";
import { PhenologyCard } from "./PhenologyCard";
import { SmokeCard } from "./SmokeCard";
import type { PhenologyStateRow, ScoreRow } from "../types";

const ROW = (overrides: Partial<ScoreRow> = {}): ScoreRow => ({
  ts: "2026-05-07T00:00:00Z",
  lead_h: 0,
  score: 0.4,
  level: "elevated",
  wedge: "frost",
  model_version: "test@0.1.0",
  inputs: {},
  ...overrides,
});

describe("<FrostCard />", () => {
  it("renders 'no frost data' when scores is empty", () => {
    render(<FrostCard scores={[]} />);
    expect(screen.getByText(/no frost data/i)).toBeTruthy();
  });

  it("renders peak score when populated", () => {
    render(
      <FrostCard
        scores={[ROW({ score: 0.2 }), ROW({ score: 0.7, level: "high" })]}
      />,
    );
    expect(screen.getByText(/0\.70/)).toBeTruthy();
  });
});

describe("<DiseaseCard />", () => {
  it("renders empty state with no rows", () => {
    render(<DiseaseCard dm={[]} pm={[]} botrytis={[]} />);
    expect(screen.getByText(/no disease data/i)).toBeTruthy();
  });

  it("surfaces DSV / PM / Botrytis values", () => {
    render(
      <DiseaseCard
        dm={[ROW({ wedge: "dm", inputs: { dsv: 3, lwd_hours: 12 } })]}
        pm={[ROW({ wedge: "pm", inputs: { index: 45 } })]}
        botrytis={[ROW({ wedge: "botrytis", inputs: { probability: 0.42 } })]}
      />,
    );
    expect(screen.getByText(/DSV 3/)).toBeTruthy();
    expect(screen.getByText(/PM 45/)).toBeTruthy();
    expect(screen.getByText(/Bot 0\.42/)).toBeTruthy();
  });
});

describe("<SmokeCard />", () => {
  it("renders empty state", () => {
    render(<SmokeCard scores={[]} />);
    expect(screen.getByText(/no smoke data/i)).toBeTruthy();
  });

  it("shows PM2.5 mean and max from the inputs JSON", () => {
    render(
      <SmokeCard
        scores={[
          ROW({
            wedge: "smoke",
            inputs: { pm25_mean: 22, pm25_max: 80, dose: 320 },
          }),
        ]}
      />,
    );
    expect(screen.getByText(/PM2\.5 mean/)).toBeTruthy();
    expect(screen.getByText(/22/)).toBeTruthy();
  });
});

describe("<PhenologyCard />", () => {
  const phenoRow = (bbch: number, gdd: number): PhenologyStateRow => ({
    block_id: 1,
    date: "2026-05-07",
    doy: 127,
    chill_units: 50,
    forcing_dd: 100,
    gdd_from_budbreak: gdd,
    bbch,
    model_version: "caffarra_eccel@0.1.0",
  });

  it("renders empty state", () => {
    render(<PhenologyCard states={[]} />);
    expect(screen.getByText(/no phenology data/i)).toBeTruthy();
  });

  it("labels BBCH stage", () => {
    render(<PhenologyCard states={[phenoRow(65, 400)]} />);
    expect(screen.getByText(/Flowering/i)).toBeTruthy();
    expect(screen.getByText(/BBCH/)).toBeTruthy();
  });
});
