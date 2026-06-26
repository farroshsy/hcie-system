/**
 * Presentational primitives for the research dashboards, built on ./theme tokens.
 *
 * Replaces the ~50 hand-rolled "white card", ~30 "badge", and ~10 "banner" inline-style
 * blobs that had drifted apart across pages. One component = one consistent look. All accept
 * a `style` escape hatch for the rare one-off, but reach for the prop first.
 */
import React from "react";
import { t, type Tone } from "./theme";

type Div = React.HTMLAttributes<HTMLDivElement>;

/** The standard white surface card. `pad` picks a padding from the spacing scale. */
export function Panel({
  children, style, pad = "lg", tone: toneName, ...rest
}: Div & { pad?: "md" | "lg" | "xl"; tone?: Tone }) {
  const tn = toneName ? t.tone[toneName] : null;
  const padY = pad === "xl" ? t.space.xl : pad === "md" ? t.space.md : t.space.lg;
  return (
    <div
      style={{
        background: tn ? tn.bg : t.color.surface,
        border: `1px solid ${tn ? tn.border : t.color.line}`,
        borderRadius: t.radius.lg,
        padding: `${padY}px ${padY + 4}px`,
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  );
}

/** Small status pill. */
export function Tag({
  tone: toneName = "neutral", children, style, ...rest
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  const tn = t.tone[toneName];
  return (
    <span
      style={{
        display: "inline-block", fontSize: t.font.size.xs, fontWeight: t.font.weight.heavy,
        color: tn.fg, background: tn.bg, border: `1px solid ${tn.border}`,
        borderRadius: t.radius.sm, padding: "2px 8px",
        textTransform: "uppercase", letterSpacing: "0.06em", ...style,
      }}
      {...rest}
    >
      {children}
    </span>
  );
}

/** Tinted callout / banner with an optional bold lead-in. */
export function Callout({
  tone: toneName = "info", title, children, style, ...rest
}: Div & { tone?: Tone; title?: React.ReactNode }) {
  const tn = t.tone[toneName];
  return (
    <div
      style={{
        background: tn.bg, border: `1px solid ${tn.border}`, borderRadius: t.radius.md,
        padding: `${t.space.md}px ${t.space.lg}px`, fontSize: t.font.size.sm,
        color: t.color.body, lineHeight: 1.6, ...style,
      }}
      {...rest}
    >
      {title ? <strong style={{ color: tn.fg }}>{title} </strong> : null}
      {children}
    </div>
  );
}

/** Section heading + optional sub-line, on the type scale. */
export function SectionTitle({ children, sub }: { children: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div style={{ marginBottom: sub ? t.space.md : t.space.sm }}>
      <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.bold, color: t.color.heading }}>
        {children}
      </div>
      {sub ? (
        <div style={{ fontSize: t.font.size.sm, color: t.color.muted, marginTop: 2, lineHeight: 1.5 }}>
          {sub}
        </div>
      ) : null}
    </div>
  );
}

/** The uppercase, letter-spaced kicker above a title. */
export function Eyebrow({ children, color = t.color.muted }: { children: React.ReactNode; color?: string }) {
  return (
    <div style={{
      fontSize: t.font.size.sm, fontWeight: t.font.weight.bold, letterSpacing: "0.1em",
      textTransform: "uppercase", color, marginBottom: t.space.sm,
    }}>
      {children}
    </div>
  );
}

/** A labelled metric tile (big number + caption). */
export function Stat({ label, value, tone: toneName = "neutral" }: { label: React.ReactNode; value: React.ReactNode; tone?: Tone }) {
  const tn = t.tone[toneName];
  return (
    <Panel pad="md" style={{ borderColor: tn.border }}>
      <div style={{ fontSize: t.font.size.h2, fontWeight: t.font.weight.heavy, color: tn.fg }}>{value}</div>
      <div style={{ fontSize: t.font.size.xs, color: t.color.muted, marginTop: 2 }}>{label}</div>
    </Panel>
  );
}
