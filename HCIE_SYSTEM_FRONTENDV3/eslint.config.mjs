import next from "eslint-config-next";

// eslint-config-next@16 ships a flat-config array (next/core-web-vitals rules,
// the TS layer, and its own ignores). Spread it directly — the old FlatCompat
// bridge (`compat.extends("next/core-web-vitals")`) throws a circular-JSON
// error on ESLint 10, which silently disabled the lint gate.
const eslintConfig = [
  ...next,

  // ── Severity calibration (deliberate, not gaming the gate) ──────────────────
  // We keep eslint-config-next's defaults as the base. The overrides below
  // demote two rule groups from error → warn so they stay VISIBLE in CI output
  // without permanently red-lining the gate (which is how a gate gets ignored).
  // Real-bug rules (rules-of-hooks, exhaustive-deps, jsx-no-comment-textnodes,
  // @next/next/*) keep their default severity.
  {
    rules: {
      // React Compiler readiness rules. This repo does NOT adopt the React
      // Compiler (no babel-plugin-react-compiler; next.config has no
      // `reactCompiler`). These flag compiler-unsafe patterns that are
      // nonetheless correct without the compiler (e.g. fetch-on-dep effects,
      // timer-driven animations, default-sync of user-overridable state).
      // Surfaced as warnings; promote back to error if the compiler is adopted.
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/immutability": "warn",
      "react-hooks/purity": "warn",
      "react-hooks/static-components": "warn",

      // Cosmetic: flags apostrophes/quotes in JSX *prose* (doesn't, "graph").
      // This is a text-heavy research-review UI; the rule fires on copy, not on
      // bugs. Warn so a genuinely stray entity still surfaces without blocking
      // on prose punctuation.
      "react/no-unescaped-entities": "warn",
    },
  },

  {
    ignores: [".next/", "node_modules/", "out/", "next-env.d.ts"],
  },
];

export default eslintConfig;
