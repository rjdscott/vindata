// Unit tests for the no-unwrapped-score rule using ESLint's RuleTester.
// Run with: pnpm --filter @vindata/eslint-rules test
//
// We exercise the rule against synthetic file contents with synthetic
// filenames so we can validate both the trigger detection and the
// allowlist (src/components/, src/lib/, etc.).

import { RuleTester } from "eslint";
import tsParser from "@typescript-eslint/parser";
import rule from "./no-unwrapped-score.js";

const tester = new RuleTester({
  languageOptions: {
    parser: tsParser,
    ecmaVersion: "latest",
    sourceType: "module",
    parserOptions: {
      ecmaFeatures: { jsx: true },
    },
  },
});

tester.run("no-unwrapped-score", rule, {
  valid: [
    // Page that imports both ScoreRow AND AdvisoryBanner — the happy path.
    {
      filename: "/repo/apps/web/src/pages/VineyardPage.tsx",
      code: `
        import { AdvisoryBanner } from "@/components/AdvisoryBanner";
        import type { ScoreRow } from "../types";
        export function VineyardPage(props: { score: ScoreRow }) { return null; }
      `,
    },
    // Leaf component that reads ScoreRow but lives under /src/components/ —
    // allowlisted because pages compose it with the banner.
    {
      filename: "/repo/apps/web/src/components/FrostChart.tsx",
      code: `
        import type { ScoreRow } from "../types";
        export function FrostChart(props: { scores: ScoreRow[] }) { return null; }
      `,
    },
    // Lib helper — allowlisted regardless of imports.
    {
      filename: "/repo/apps/web/src/lib/format.ts",
      code: `
        import type { FrostLevel } from "../types";
        export const labels: Record<FrostLevel, string> = { low: "L", elevated: "E", high: "H", extreme: "X" };
      `,
    },
    // A page that touches the API but doesn't pull scores — no trigger.
    {
      filename: "/repo/apps/web/src/pages/AdminPage.tsx",
      code: `
        import { api } from "../api/client";
        export function AdminPage() { void api; return null; }
      `,
    },
  ],
  invalid: [
    // Page imports ScoreRow but no banner — must error.
    {
      filename: "/repo/apps/web/src/pages/BadPage.tsx",
      code: `
        import type { ScoreRow } from "../types";
        export function BadPage(props: { score: ScoreRow }) { return null; }
      `,
      errors: [{ messageId: "missingBanner" }],
    },
    // Page calls api.getScores but doesn't import the banner.
    {
      filename: "/repo/apps/web/src/pages/AnotherBad.tsx",
      code: `
        import { api } from "../api/client";
        const x = api.getScores(1, "frost", 72);
        export default x;
      `,
      errors: [{ messageId: "missingBanner" }],
    },
  ],
});

console.log("no-unwrapped-score rule: all tests passed.");
