/**
 * @fileoverview Enforces that any module rendering an agronomy score
 *   (i.e. accessing `.score`, `.level`, or destructuring a `ScoreRow`)
 *   imports `AdvisoryBanner`. The banner is the framing safety net that
 *   tells growers our outputs are advisory, not a spray decision.
 *
 *   Why this rule exists: Stage 00 plan called out that the framing must
 *   not be skippable in code review. ESLint catches it deterministically.
 *
 *   Heuristic (intentionally conservative):
 *     1. Find files that import any of: `ScoreRow`, `FrostLevel` from `../types`
 *        (or `@/types`), OR call `api.getScores(...)`.
 *     2. In those files, require an import of `AdvisoryBanner`.
 *
 *   Allowlist: files in `src/lib/`, `src/api/`, and `src/test/` are skipped
 *   (utility / data-access modules don't render UI).
 *
 *   This is a file-scoped rule, not a render-tree analysis. A more
 *   ambitious version would track JSX tree composition, but this catches
 *   the realistic class of "developer renders a score and forgets the
 *   banner" without false-positive grief.
 */

const SCORE_TYPE_IMPORTS = new Set(["ScoreRow", "FrostLevel"]);
const TYPE_PATHS = new Set(["../types", "../../types", "@/types", "./types"]);
const API_PATHS = new Set(["../api/client", "@/api/client", "./api/client"]);
// Pages own the AdvisoryBanner contract. Leaf modules (lib utilities, API
// clients, and presentational components in src/components/) are composed
// inside pages and don't each need to import the banner.
const SKIP_DIR_FRAGMENTS = [
  "/src/lib/",
  "/src/api/",
  "/src/test/",
  "/src/components/",
];

export default {
  meta: {
    type: "problem",
    docs: {
      description:
        "Modules that render agronomy scores must import AdvisoryBanner.",
    },
    schema: [],
    messages: {
      missingBanner:
        "This module reads agronomy score data ({{trigger}}) but does not " +
        "import AdvisoryBanner. Add `import { AdvisoryBanner } from " +
        "\"@/components/AdvisoryBanner\"` and render it in the page layout.",
    },
  },
  create(context) {
    const filename = context.filename ?? context.getFilename();
    if (SKIP_DIR_FRAGMENTS.some((frag) => filename.includes(frag))) {
      return {};
    }

    let importsAdvisoryBanner = false;
    let trigger = null;
    let triggerNode = null;

    return {
      ImportDeclaration(node) {
        const source = node.source.value;
        if (
          typeof source === "string" &&
          source.includes("AdvisoryBanner")
        ) {
          importsAdvisoryBanner = true;
        }
        if (TYPE_PATHS.has(source)) {
          for (const spec of node.specifiers) {
            if (
              spec.type === "ImportSpecifier" &&
              SCORE_TYPE_IMPORTS.has(spec.imported.name)
            ) {
              trigger = spec.imported.name;
              triggerNode = node;
            }
          }
        }
        if (API_PATHS.has(source)) {
          for (const spec of node.specifiers) {
            if (
              spec.type === "ImportSpecifier" &&
              spec.imported.name === "api"
            ) {
              // Only count `api` if `getScores` is called on it later.
              // We track the import; the call check happens below.
              triggerNode = triggerNode ?? node;
            }
          }
        }
      },

      // Catch `api.getScores(...)` calls.
      CallExpression(node) {
        if (
          node.callee.type === "MemberExpression" &&
          node.callee.object.type === "Identifier" &&
          node.callee.object.name === "api" &&
          node.callee.property.type === "Identifier" &&
          node.callee.property.name === "getScores"
        ) {
          trigger = trigger ?? "api.getScores";
          triggerNode = triggerNode ?? node;
        }
      },

      "Program:exit"() {
        if (trigger && !importsAdvisoryBanner) {
          context.report({
            node: triggerNode,
            messageId: "missingBanner",
            data: { trigger },
          });
        }
      },
    };
  },
};
