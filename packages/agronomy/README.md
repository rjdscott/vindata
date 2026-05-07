# agronomy

Pure-Python viticultural agronomy models for VinData.

## Design rules

1. **No I/O.** No HTTP, no DB, no filesystem reads. Every function takes inputs as arguments and returns outputs as values.
2. **No globals.** Configuration is passed in via dataclasses. Defaults are class-level constants on those dataclasses.
3. **Fully typed.** `mypy --strict` clean. Public types are `frozen=True, slots=True` dataclasses.
4. **Citations as code.** Every model module's docstring cites its canonical paper(s) and the line that implements each equation references the paper section.
5. **Versioned.** `agronomy.version.MODEL_VERSION` is bumped (SemVer) on any change to a model's outputs.

This package is consumed by `apps/ingest` (Dagster scoring assets) and `apps/api` (legacy/manual recompute paths).

## Stage 00 scope

Implemented:
- `agronomy.frost` — radiation-cooling Tmin prediction and 0–1 frost score.

Stubbed (signatures only; raise `NotImplementedError`):
- `agronomy.disease.dmcast`, `gubler_thomas`, `broome_botrytis`
- `agronomy.smoke`
- `agronomy.phenology.gdd`, `caffarra_eccel`, `fao56_eto`, `swb`

Stage 01 fills the stubs.
