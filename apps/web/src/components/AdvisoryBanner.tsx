/**
 * AdvisoryBanner — required by every page that renders an agronomy score.
 *
 * Stage 01 enforces presence via a custom ESLint rule (`no-unwrapped-score`).
 * For now we keep it as a single source of truth: the same wording goes in
 * email templates so growers see consistent framing.
 */
export function AdvisoryBanner(): JSX.Element {
  return (
    <div
      role="note"
      className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900"
    >
      <strong className="font-semibold">Advisory only.</strong>{" "}
      Forecast-derived scores are decision support, not a spray or
      management instruction. Always combine with on-site observations.
    </div>
  );
}
