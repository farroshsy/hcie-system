/**
 * Design tokens for the research dashboards (the /dashboard/* + /review/* surfaces).
 *
 * These pages are dense, inline-styled research instruments. Before this file every page
 * hand-wrote the same hex values (#E2E8F0 ×284, #718096 ×256, …), radii (6/8/10/12), and
 * font sizes — so "the same card" looked subtly different on every page. This is the single
 * source of truth: import `t` and the primitives in ./primitives instead of pasting literals.
 *
 * (shadcn/ui in src/components/ui remains the system for interactive form controls; this is
 * the token layer for the data-display dashboards.)
 */

export const color = {
  // text — darkest (headings) → faintest (captions)
  ink: "#1A2332",
  heading: "#2C3E50",
  body: "#4A5568",
  muted: "#718096",
  faint: "#A0AEC0",
  // surfaces + lines
  surface: "#FFFFFF",
  subtle: "#F8F9FA",
  faintSurface: "#FBFCFD",
  line: "#E2E8F0",
  lineStrong: "#CBD5E0",
  grid: "#F1F5F9",
} as const;

/** Semantic tones: fg (text/icon), bg (tint), border. Used by Tag + Callout. */
export const tone = {
  neutral: { fg: "#4A5568", bg: "#F8F9FA", border: "#E2E8F0" },
  ok: { fg: "#117A65", bg: "#E8F8F5", border: "#A2D9CE" },
  warn: { fg: "#9A7D0A", bg: "#FEF9E7", border: "#F7DC6F" },
  bad: { fg: "#C0392B", bg: "#FDEDEC", border: "#F5B7B1" },
  info: { fg: "#1565C0", bg: "#EBF5FB", border: "#AED6F1" },
  accent: { fg: "#6C3483", bg: "#F4ECF7", border: "#D2B4DE" },
} as const;
export type Tone = keyof typeof tone;

/** Canonical per-model colors (was copy-pasted as MODEL_COLOR on individual pages). */
export const modelColor: Record<string, string> = {
  hcie: "#6C3483", sakt: "#2980B9", dkt: "#16A085", bkt: "#1E8449",
  irt_1pl: "#E67E22", gkt: "#8E44AD", greedy_correct_rate: "#7F8C8D",
  random: "#C0392B", static_prior: "#BDC3C7",
};

/** 4-based spacing scale (px). Use these, not arbitrary paddings. */
export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24 } as const;

/** Corner radii. One card = one radius (was 6/8/10/12 mixed). */
export const radius = { sm: 6, md: 8, lg: 10, xl: 12 } as const;

/** Type scale (px) + weights. */
export const font = {
  size: { xs: 10, sm: 11, base: 12, md: 13, lg: 15, xl: 18, h2: 20, h1: 28 },
  weight: { medium: 600, bold: 700, heavy: 800 },
} as const;

/** Single import surface: `import { t } from "@/lib/ui/theme"`. */
export const t = { color, tone, modelColor, space, radius, font };
export default t;
