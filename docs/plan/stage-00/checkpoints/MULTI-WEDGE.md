# Multi-wedge checkpoint — Stage 00 Phase 0.8

**Date**: 2026-05-07
**Branch**: `feat/wedges-disease-smoke-phenology` (PR #2)
**Hindcast script**: `packages/agronomy/notebooks/hindcast.py`
**Results JSON**: `packages/agronomy/notebooks/results/hindcast.json`

This checkpoint records the post-merge state of the four agronomy wedges against real public-data sources (SILO Orange tile, NSW DPE Air Quality, NASA FIRMS).

## Hindcast — SILO Orange tile (-33.286, 149.103, 2018-05-07 → 2026-05-07)

8 years × 365 days = **2922 daily rows** of `daily_rain`, `max_temp`, `min_temp` from the public SILO BoM-Only tier (no patched-tier fields available without a registered account, so RH and radiation default).

### Frost — Snyder & de Melo-Abreu radiation cooling

| Metric | Stage 01 target | Result |
|---|---|---|
| MAE (Tmin pred vs SILO Tmin) | ≤ 1.2 °C | **2.38 °C** |
| Hit-rate at 0 °C (TP / (TP+FN)) | ≥ 0.80 | **0.44** |
| FAR at 0 °C (FP / (TP+FP)) | ≤ 0.30 | **0.47** |

Confusion matrix (`Tmin ≤ 0 °C`): TP 147 · FP 131 · FN 187 · TN 2457.

**Verdict**: model runs end-to-end on real data; literature-default coefficients (`k=1.6, c_cloud=0.7, c_wind=0.25`) are **not within Stage 01 acceptance**. Calibration on Orange BoM AWS 063303 history is genuine Stage 01 work.

### Phenology — Caffarra-Eccel BBCH

| Stage | Predicted DOY | Calendar | Published Orange |
|---|---|---|---|
| Budbreak | 262 | Sep 19 | Sep 25 – Oct 5 |
| Flowering | 343 | Dec 9 | Nov 25 – Dec 10 |
| Veraison | 32 | Feb 1 | Jan 25 – Feb 15 |
| Maturity | 67 | Mar 8 | Mar 15 – Apr 5 |

**Verdict**: stage transitions are in the right month; budbreak is **~6–16 days early** vs published Orange phenological observations. Stage 01 target is ≤ 5 days. Refit chill_crit and force_crit on observed budbreak data.

### Disease — DMCast / Gubler-Thomas / Broome

Computed by synthesising hourly profiles from daily Tmin/Tmax/rain (treating rainy days as RH ≥ 92% per NEWA CART rule 2):

| Wedge | Statistic | 2922-day total |
|---|---|---|
| DM (DSV) | wet days (DSV ≥ 1) | 417 |
| DM (DSV) | high-pressure days (DSV ≥ 3) | 417 |
| DM (DSV) | cumulative DSV | 1668 |
| PM (Gubler-Thomas) | max index reached | 100 (saturated) |
| PM (Gubler-Thomas) | final index (end of window) | 0 |
| Botrytis (Broome 1995) | LWD ≥ 6 h events | 740 |
| Botrytis (Broome 1995) | high-probability events (P ≥ 0.5) | 703 |

**Verdict**: all three sub-models run end-to-end on the synthesised hourly trace. Quantitative validation against the UC IPM example dataset (Stage 01 acceptance: ±2 index points for PM) is deferred to Stage 01 — that requires the published worked-example test inputs that aren't shipped in SILO.

### Smoke — Coulter 2022 dose

Replay window: 2019-12-01 → 2020-02-28 (90 SILO days). Synthetic PM2.5 trace anchored to 5 Black Summer days documented in NSW Health / BoM reporting (2019-12-21, 2019-12-23, 2019-12-31, 2020-01-04, 2020-01-05) at 220 µg/m³, otherwise 8 µg/m³ background. All hours treated as stable (typical inversion behaviour around Mount Canobolas).

| Metric | Stage 01 target | Result |
|---|---|---|
| Flag-rate of documented PM2.5 events | ≥ 80 % | **5/5 = 100 %** |
| Days flagged "extreme" | — | 5 |

**Verdict**: passes Stage 01 acceptance on the synthetic anchor. Real validation requires the NSW EPA Bathurst PM2.5 record from that window (Stage 01 ingest).

## ETo — sanity check

Annual reference evapotranspiration totals **10117.6 mm over 8 years = ~1265 mm/year**. The accepted Orange-region annual ETo (Bureau of Meteorology, 1976–2005 normals) is ~1100–1200 mm/year. PoC defaults are within ~5–10 % of climatology, which is the right order of magnitude for an uncalibrated FAO-56 implementation defaulting RH and radiation.

## Test posture

| Layer | Tests | Coverage |
|---|---|---|
| `packages/agronomy` | 101 (incl. property tests via Hypothesis) | **97.58 %** |
| `apps/api` | 11 unit + 4 integration markers | mypy --strict clean |
| `apps/ingest` | 11 (asset graph + dependency direction + check registration) | — |
| `apps/web` | 16 (vitest) | typecheck + lint clean |

`bash scripts/smoke.sh` exits 0 against the rebuilt local stack.

## What's left for Stage 01 (gap analysis)

1. **Frost calibration** — refit `k`, `c_cloud`, `c_wind` on Orange BoM AWS 063303 (2019-2024) to bring MAE ≤ 1.2 °C and hit-rate ≥ 0.80.
2. **Phenology calibration** — refit `chill_crit` and `force_crit` for Chardonnay / Shiraz / Pinot Noir using observed Australian budbreak data; budbreak DOY error ≤ 5 days.
3. **Disease validation** — reproduce the UC IPM Gubler-Thomas worked example to ±2 points; reproduce DMCast on a published wet-event dataset; report a Brier score for Broome on observed botrytis incidence.
4. **Smoke validation** — pull the NSW EPA Bathurst PM2.5 record for 2019-12 / 2020-02 and confirm the **real** Black Summer flag-rate matches the synthetic replay.
5. **Multi-block UX** — the dashboard currently surfaces only the first block's phenology card; Stage 01 adds a block selector or a per-block tab.
