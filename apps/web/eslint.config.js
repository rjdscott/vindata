// Flat ESLint config for the web app.
//
// Includes the local @vindata/eslint-rules plugin, which enforces the
// AdvisoryBanner contract via the `no-unwrapped-score` rule. See
// /tools/eslint-rules/rules/no-unwrapped-score.js for the contract.

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import vindata from "@vindata/eslint-rules";

export default tseslint.config(
  { ignores: ["dist", "node_modules", "src/api/client.ts"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "@vindata": vindata,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      "@vindata/no-unwrapped-score": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
);
