// Local ESLint plugin for VinData. Stage 00 ships one rule:
// `no-unwrapped-score` — see ./rules/no-unwrapped-score.js for the contract.

import noUnwrappedScore from "./rules/no-unwrapped-score.js";

export default {
  meta: {
    name: "@vindata/eslint-rules",
    version: "0.0.1",
  },
  rules: {
    "no-unwrapped-score": noUnwrappedScore,
  },
};
