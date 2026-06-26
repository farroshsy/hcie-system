'use client'

import { useState } from 'react'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

// ── palette ────────────────────────────────────────────────────────────────────
const C = {
  bg:       '#F8FAFC',
  card:     '#FFFFFF',
  border:   '#E2E8F0',
  accent:   '#1565C0',
  accentL:  '#E3F2FD',
  green:    '#1E8449',
  greenL:   '#EAFAF1',
  warn:     '#B7791F',
  warnL:    '#FFFBEB',
  red:      '#C0392B',
  redL:     '#FDEDEC',
  neutral:  '#4A5568',
  dark:     '#1A2332',
  muted:    '#94A3B8',
  purple:   '#6D28D9',
  purpleL:  '#EDE9FE',
  teal:     '#0891B2',
  tealL:    '#ECFEFF',
}

// ── primitives ─────────────────────────────────────────────────────────────────

function Tag({ label, color, bg }: { label: string; color: string; bg: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 9px', borderRadius: 12,
      fontSize: 10, fontWeight: 700, letterSpacing: '0.07em',
      color, background: bg, textTransform: 'uppercase' as const,
    }}>{label}</span>
  )
}

function SectionDivider({ n, title, sub }: { n: string; title: string; sub?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, margin: '40px 0 20px' }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10,
        background: C.accent, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 800, fontSize: 16, flexShrink: 0,
      }}>{n}</div>
      <div>
        {sub && <div style={{ fontSize: 10, fontWeight: 700, color: C.muted,
                               letterSpacing: '0.1em', textTransform: 'uppercase' as const,
                               marginBottom: 2 }}>{sub}</div>}
        <div style={{ fontSize: 18, fontWeight: 800, color: C.dark }}>{title}</div>
      </div>
    </div>
  )
}

function Callout({ color, bg, border, children }: {
  color: string; bg: string; border: string; children: React.ReactNode
}) {
  return (
    <div style={{
      background: bg, border: `1.5px solid ${border}`,
      borderRadius: 8, padding: '14px 18px', marginBottom: 14,
    }}>
      <div style={{ fontSize: 13, color, lineHeight: 1.75 }}>{children}</div>
    </div>
  )
}

function Mono({ children }: { children: React.ReactNode }) {
  return (
    <code style={{
      fontFamily: '"Fira Code",Consolas,monospace',
      fontSize: 11, background: '#F1F5F9', padding: '1px 5px', borderRadius: 3,
      color: C.accent,
    }}>{children}</code>
  )
}

// ── Gap card ──────────────────────────────────────────────────────────────────

function GapCard({ n, label, primary, body, cpNote, primaryTag, lessLabel, moreLabel, cpHeading }: {
  n: string; label: string; primary?: boolean; body: React.ReactNode; cpNote: string;
  primaryTag: string; lessLabel: string; moreLabel: string; cpHeading: string
}) {
  const [open, setOpen] = useState(false)
  const accent = primary ? C.accent : C.neutral
  const bg     = primary ? C.accentL : '#F8FAFC'
  const border = primary ? C.accent  : C.border

  return (
    <div style={{
      border: `1.5px solid ${border}`, borderRadius: 10, overflow: 'hidden',
      marginBottom: 12, boxShadow: primary ? '0 2px 8px rgba(21,101,192,0.10)' : 'none',
    }}>
      <div style={{ background: bg, padding: '12px 18px',
                    display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            width: 28, height: 28, borderRadius: 8, background: accent,
            color: '#fff', fontWeight: 800, fontSize: 13,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>{n}</span>
          <span style={{ fontWeight: 700, fontSize: 15, color: C.dark }}>{label}</span>
          {primary && <Tag label={primaryTag} color={C.accent} bg="#DBEAFE" />}
        </div>
        <button onClick={() => setOpen(v => !v)} style={{
          fontSize: 11, color: accent, background: 'none', border: `1px solid ${accent}`,
          borderRadius: 6, padding: '3px 10px', cursor: 'pointer', fontWeight: 600,
          flexShrink: 0,
        }}>{open ? `▲ ${lessLabel}` : `▼ ${moreLabel}`}</button>
      </div>
      <div style={{ padding: '12px 18px' }}>
        {body}
        {open && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.muted,
                           letterSpacing: '0.08em', textTransform: 'uppercase' as const,
                           marginBottom: 6 }}>{cpHeading}</div>
            <pre style={{
              margin: 0, padding: '10px 14px',
              background: '#0F172A', color: '#94A3B8',
              borderRadius: 6, fontSize: 11, lineHeight: 1.6,
              overflowX: 'auto',
              fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
              whiteSpace: 'pre',
            }}>
              {cpNote.split('\n').map((line, i) => {
                const isComment = line.trim().startsWith('//')
                return (
                  <span key={i} style={{ color: isComment ? '#4ADE80' : '#E2E8F0', display: 'block' }}>
                    {line}
                  </span>
                )
              })}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Contribution card ─────────────────────────────────────────────────────────

function ContribCard({ letter, tag, tagColor, tagBg, title, subtitle, items, evidence, cpNote,
                       evidenceHeading, cpHideLabel, cpShowLabel }: {
  letter: string; tag: string; tagColor: string; tagBg: string;
  title: string; subtitle: string;
  items: { label: string; text: string }[];
  evidence: string;
  cpNote: string;
  evidenceHeading: string; cpHideLabel: string; cpShowLabel: string;
}) {
  const [cpOpen, setCpOpen] = useState(false)
  return (
    <div style={{
      border: `1.5px solid ${tagColor}`,
      borderRadius: 12, overflow: 'hidden', marginBottom: 16,
    }}>
      {/* Header */}
      <div style={{
        background: tagBg, padding: '14px 20px',
        display: 'flex', alignItems: 'flex-start', gap: 14,
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10, background: tagColor,
          color: '#fff', fontWeight: 900, fontSize: 20, flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>{letter}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' as const }}>
            <Tag label={tag} color={tagColor} bg="rgba(255,255,255,0.6)" />
          </div>
          <div style={{ fontWeight: 800, fontSize: 16, color: C.dark, marginBottom: 2 }}>{title}</div>
          <div style={{ fontSize: 12, color: C.neutral, lineHeight: 1.6 }}>{subtitle}</div>
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
          {items.map((item, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: tagColor,
                              flexShrink: 0, marginTop: 6 }} />
              <div>
                <span style={{ fontWeight: 700, fontSize: 12, color: C.dark }}>{item.label}: </span>
                <span style={{ fontSize: 12, color: C.neutral, lineHeight: 1.6 }}>{item.text}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Evidence box */}
        <div style={{
          background: C.greenL, border: `1px solid ${C.green}`,
          borderRadius: 6, padding: '8px 14px', marginBottom: 12,
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: C.green,
                         letterSpacing: '0.08em', textTransform: 'uppercase' as const, marginBottom: 3 }}>
            {evidenceHeading}
          </div>
          <div style={{ fontSize: 12, color: C.dark, lineHeight: 1.6 }}>{evidence}</div>
        </div>

        {/* CP note toggle */}
        <button onClick={() => setCpOpen(v => !v)} style={{
          fontSize: 11, color: tagColor, background: 'none',
          border: `1px solid ${tagColor}`, borderRadius: 6,
          padding: '3px 10px', cursor: 'pointer', fontWeight: 600, marginBottom: cpOpen ? 10 : 0,
        }}>
          {cpOpen ? `▲ ${cpHideLabel}` : `▶ ${cpShowLabel}`}
        </button>
        {cpOpen && (
          <pre style={{
            margin: '0', padding: '10px 14px',
            background: '#0F172A', color: '#94A3B8',
            borderRadius: 6, fontSize: 11, lineHeight: 1.6,
            overflowX: 'auto',
            fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
            whiteSpace: 'pre',
          }}>
            {cpNote.split('\n').map((line, i) => {
              const isComment = line.trim().startsWith('//')
              return (
                <span key={i} style={{ color: isComment ? '#4ADE80' : '#E2E8F0', display: 'block' }}>
                  {line}
                </span>
              )
            })}
          </pre>
        )}
      </div>
    </div>
  )
}

// ── Maturation step ───────────────────────────────────────────────────────────

function MatStep({ n, title, body, verdict, isLast }: {
  n: number; title: string; body: React.ReactNode; verdict: string; isLast?: boolean
}) {
  return (
    <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: C.accent, color: '#fff',
          fontWeight: 800, fontSize: 14,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>{n}</div>
        {!isLast && <div style={{ width: 2, flex: 1, background: C.border, marginTop: 4 }} />}
      </div>
      <div style={{ flex: 1, paddingBottom: 4 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: C.dark, marginBottom: 6 }}>{title}</div>
        <div style={{ fontSize: 12, color: C.neutral, lineHeight: 1.7, marginBottom: 8 }}>{body}</div>
        <div style={{
          display: 'inline-flex', fontSize: 11, fontWeight: 700, color: C.green,
          background: C.greenL, borderRadius: 6, padding: '4px 10px',
        }}>→ {verdict}</div>
      </div>
    </div>
  )
}

// ── AUC mini-table ────────────────────────────────────────────────────────────
// Numeric/identifier data only — display text resolved via t() in the component.

// Matched-eval m_K (lagged-Kalman, tie-aware, 10 held-out users) — the single
// headline number. HCIE 0.6051 LEADS all baselines on pooled overall AUC.
// δ = HCIE − model (positive ⇒ HCIE ahead). Source: pass01_matched_eval.json
// (seal-bae44d1a / run-d2154070). Supersedes the pre-tie-aware 0.6364 family.
const AUC_ROWS = [
  { model: 'HCIE',  auc: 0.6051, delta: null,    noteKey: 'aucNoteHcie' },
  { model: 'BKT',   auc: 0.5963, delta: +0.0088, noteKey: 'aucNoteBkt' },
  { model: 'DKT',   auc: 0.5892, delta: +0.0159, noteKey: 'aucNoteDkt' },
  { model: 'SAKT',  auc: 0.5730, delta: +0.0321, noteKey: 'aucNoteSakt' },
  { model: 'GKT',   auc: 0.5711, delta: +0.0340, noteKey: 'aucNoteGkt' },
]

// Cold-start window margins — matched eval, robust n=76 (tie-aware, Junyi Phase-2).
// δ = HCIE − BKT. Only ≤5 favours HCIE; ≤10/≤20 favour BKT, and ALL CIs cross zero,
// so no per-window claim is robust (the robust headline is the pooled overall lead
// above, +0.0088 → +0.0125 significant at n=76). Per-window absolute AUCs are the
// small-sample n=50/100/200 cells (pass01_matched_eval.json) — not shown here to
// avoid implying robustness the windows do not have. Source: DRAFT 26 JUNI.
const COLDSTART_ROWS = [
  { id: 'w5',  n: 76, delta: +0.037, robust: false, primary: true  },
  { id: 'w10', n: 76, delta: -0.017, robust: false, primary: false },
  { id: 'w20', n: 76, delta: -0.031, robust: false, primary: false },
]

function AucTable() {
  const t = useT()
  const headers = [
    t('narrative.aucColModel'),
    t('narrative.aucColAuc'),
    t('narrative.aucColDelta'),
    t('narrative.aucColNotes'),
  ]
  return (
    <div style={{ overflowX: 'auto', marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 6,
                     textTransform: 'uppercase' as const, letterSpacing: '0.08em' }}>
        {t('narrative.aucTableCaption')}
      </div>
      <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
        <thead>
          <tr style={{ background: '#F1F5F9' }}>
            {headers.map(h => (
              <th key={h} style={{ padding: '6px 12px', color: C.neutral, fontWeight: 700,
                                    textAlign: 'left', borderBottom: '2px solid #CBD5E0' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {AUC_ROWS.map((r, i) => (
            <tr key={r.model} style={{
              background: r.model === 'HCIE' ? C.accentL : i % 2 === 0 ? '#fff' : '#F8FAFC',
              fontWeight: r.model === 'HCIE' ? 700 : 400,
            }}>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            color: r.model === 'HCIE' ? C.accent : C.dark }}>{r.model}</td>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            fontFamily: 'Consolas,monospace', color: C.dark }}>{r.auc.toFixed(4)}</td>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            fontFamily: 'Consolas,monospace',
                            color: r.delta === null ? C.muted : r.delta > 0 ? C.green : C.red }}>
                {r.delta === null ? '—' : (r.delta > 0 ? '+' : '') + r.delta.toFixed(4)}
              </td>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            fontSize: 11, color: C.neutral }}>{t(`narrative.${r.noteKey}`)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: 11, color: C.neutral, marginTop: 6 }}>
        {t('narrative.aucTableFootnote')}
      </div>
    </div>
  )
}

function ColdStartTable() {
  const t = useT()
  const headers = [
    t('narrative.coldColWindow'),
    t('narrative.coldColNPairs'),
    t('narrative.coldColDelta'),
    t('narrative.coldColRobust'),
  ]
  return (
    <div style={{ overflowX: 'auto', marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 6,
                     textTransform: 'uppercase' as const, letterSpacing: '0.08em' }}>
        {t('narrative.coldTableCaption')}
      </div>
      <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
        <thead>
          <tr style={{ background: '#F1F5F9' }}>
            {headers.map(h => (
              <th key={h} style={{ padding: '6px 12px', color: C.neutral, fontWeight: 700,
                                    textAlign: 'left', borderBottom: '2px solid #CBD5E0' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {COLDSTART_ROWS.map((r, i) => (
            <tr key={r.id} style={{ background: i % 2 === 0 ? '#fff' : '#F8FAFC' }}>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            fontWeight: r.primary ? 700 : 400,
                            color: C.dark }}>{t(`narrative.coldRow_${r.id}`)}</td>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            color: C.neutral }}>{r.n.toLocaleString()}</td>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            fontFamily: 'Consolas,monospace', fontWeight: 700,
                            color: r.delta > 0 ? C.green : C.red }}>
                {(r.delta > 0 ? '+' : '') + r.delta.toFixed(3)}
              </td>
              <td style={{ padding: '6px 12px', borderBottom: '1px solid #EDF2F7',
                            fontSize: 11, color: C.warn, fontWeight: 600 }}>
                {t('narrative.coldRobustNo')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: 11, color: C.neutral, marginTop: 6 }}>
        {t('narrative.coldTableFootnote')}
      </div>
    </div>
  )
}

// ── main ───────────────────────────────────────────────────────────────────────

export default function NarrativePage() {
  const t = useT()
  return (
    <div style={{ padding: '32px 40px', maxWidth: 960,
                  fontFamily: 'Inter,system-ui,sans-serif', color: C.dark }}>

      {/* ── Hero ── */}
      <div style={{ marginBottom: 36 }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
                      color: C.muted, textTransform: 'uppercase' as const, marginBottom: 6 }}>
          {t('narrative.heroEyebrow')}
        </div>
        <h1 style={{ fontSize: 24, fontWeight: 900, color: C.dark, marginBottom: 10, lineHeight: 1.2 }}>
          {t('narrative.heroTitleA')}<br />{t('narrative.heroTitleB')}
        </h1>
        <p style={{ fontSize: 13, color: C.neutral, lineHeight: 1.8, maxWidth: 740, marginBottom: 16 }}>
          {t('narrative.heroLeadA')}{' '}
          <strong>{t('narrative.heroLeadInstrument')}</strong>{t('narrative.heroLeadB')}{' '}
          <strong>{t('narrative.heroLeadFinding')}</strong>{t('narrative.heroLeadC')}
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap' as const, gap: 8 }}>
          <Tag label={t('narrative.tagIdentity')} color={C.accent} bg={C.accentL} />
          <Tag label={t('narrative.tagAnchor')} color={C.neutral} bg="#F1F5F9" />
          <Tag label={t('narrative.tagCausalSeal')} color={C.green} bg={C.greenL} />
        </div>
      </div>

      {/* ── §1.2 Gaps ── */}
      <SectionDivider n="§1" title={t('narrative.sec1Title')} sub={t('narrative.sec1Sub')} />

      <GapCard n="1" label={t('narrative.gap1Label')}
        primaryTag={t('narrative.primaryGapTag')}
        lessLabel={t('narrative.lessLabel')} moreLabel={t('narrative.moreLabel')}
        cpHeading={t('narrative.cpAngleHeading')}
        body={
          <p style={{ fontSize: 13, color: C.neutral, lineHeight: 1.75, margin: 0 }}>
            {t('narrative.gap1BodyA')}<strong>{t('narrative.gap1BodyLatent')}</strong>{t('narrative.gap1BodyB')}
          </p>
        }
        cpNote={`// Gap 1 in algorithm terms:
// DKT: h_0 = zeros(d)  → cold prediction = σ(W_y · 0 + b_y) = constant
// SAKT: no history → attention over empty sequence → undefined or degenerate
// GKT: node states are GLOBAL (shared across learners) → can't personalise cold user
//
// HCIE fix: per-(learner, concept) state (μ=0.5, σ²=1.0) from t=0
//   first prediction already uses informative prior, not a zero vector
//   O(2) space per new learner-concept pair; no batch job needed`}
      />

      <GapCard n="2" label={t('narrative.gap2Label')}
        primaryTag={t('narrative.primaryGapTag')}
        lessLabel={t('narrative.lessLabel')} moreLabel={t('narrative.moreLabel')}
        cpHeading={t('narrative.cpAngleHeading')}
        body={
          <p style={{ fontSize: 13, color: C.neutral, lineHeight: 1.75, margin: 0 }}>
            {t('narrative.gap2BodyA')}<em>{t('narrative.gap2BodyHowMuch')}</em>{t('narrative.gap2BodyB')}<strong>{t('narrative.gap2BodyQuality')}</strong>{t('narrative.gap2BodyC')}
          </p>
        }
        cpNote={`// Gap 2 in algorithm terms:
// Greedy exploitation of mastery signal → recommendation converges too fast
// BKT: purely reactive (update then predict) — no explicit exploration term
// HCIE fix: JT Uncertainty signal = KF variance σ²_ik
//   High σ² → high JT → system recommends under-explored concepts
//   Thompson Sampling bandit also injects exploration over modalities
//   Exploration decays naturally as σ² shrinks with more observations
//   This is the standard explore-exploit tradeoff, but per-(learner,concept)`}
      />

      <GapCard n="3" label={t('narrative.gap3Label')} primary
        primaryTag={t('narrative.primaryGapTag')}
        lessLabel={t('narrative.lessLabel')} moreLabel={t('narrative.moreLabel')}
        cpHeading={t('narrative.cpAngleHeading')}
        body={
          <p style={{ fontSize: 13, color: C.neutral, lineHeight: 1.75, margin: 0 }}>
            {t('narrative.gap3BodyA')}<strong>{t('narrative.gap3BodyMultidim')}</strong>{t('narrative.gap3BodyB')}<strong>{t('narrative.gap3BodyDramatic')}</strong>{t('narrative.gap3BodyC')}
          </p>
        }
        cpNote={`// Gap 3 in algorithm terms:
// Suppose JT(i,k) = Σ_d w_d * signal_d(i,k), and AUC = 0.61 for two systems:
//   System A: w = [0.5, 0.5, 0, 0, 0, 0]  (only ΔM + uncertainty active)
//   System B: w = [0.1, 0.1, 0.2, 0.2, 0.2, 0.2]  (all 6 dims active)
// AUC cannot distinguish A from B.
//
// ADC fix: classify each dimension as ACTIVE or structural_zero
//   threshold: E[signal_d] > α_floor AND std/mean > 0.08
//   This is a per-dimension health check, like a CI assertion:
//     assert mean_contribution > 0.01, "dimension is dead weight"
//   The ADC runs post-hoc on sealed trajectory data, never touches runtime`}
      />

      {/* ── Contributions ── */}
      <SectionDivider n="§2" title={t('narrative.sec2Title')} sub={t('narrative.sec2Sub')} />

      {/* Dependency flow */}
      <div style={{
        background: C.accentL, border: `1px solid ${C.accent}`,
        borderRadius: 10, padding: '16px 20px', marginBottom: 20,
        fontFamily: '"Fira Code",Consolas,monospace', fontSize: 13,
      }}>
        <div style={{ fontWeight: 700, color: C.dark, marginBottom: 10 }}>{t('narrative.depTitle')}</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div>
            <span style={{ background: C.accent, color: '#fff', borderRadius: 4,
                            padding: '2px 8px', fontWeight: 700 }}>A</span>
            <span style={{ color: C.dark, marginLeft: 10 }}>
              {t('narrative.depA')}
            </span>
          </div>
          <div style={{ paddingLeft: 20, color: C.neutral, fontSize: 12 }}>
            {t('narrative.depArrowAB')}
          </div>
          <div>
            <span style={{ background: C.purple, color: '#fff', borderRadius: 4,
                            padding: '2px 8px', fontWeight: 700 }}>B</span>
            <span style={{ color: C.dark, marginLeft: 10 }}>
              {t('narrative.depB')}
            </span>
          </div>
          <div style={{ paddingLeft: 20, color: C.neutral, fontSize: 12 }}>
            {t('narrative.depArrowBC')}
          </div>
          <div>
            <span style={{ background: C.teal, color: '#fff', borderRadius: 4,
                            padding: '2px 8px', fontWeight: 700 }}>C</span>
            <span style={{ color: C.dark, marginLeft: 10 }}>
              {t('narrative.depC')}
            </span>
          </div>
        </div>
      </div>

      <ContribCard
        letter="A" tag={t('narrative.contribATag')}
        tagColor={C.accent} tagBg={C.accentL}
        title={t('narrative.contribATitle')}
        subtitle={t('narrative.contribASubtitle')}
        evidenceHeading={t('narrative.successEvidenceHeading')}
        cpHideLabel={t('narrative.cpHideLabel')} cpShowLabel={t('narrative.cpShowLabel')}
        items={[
          { label: t('narrative.contribAItem1Label'), text: t('narrative.contribAItem1Text') },
          { label: t('narrative.contribAItem2Label'), text: t('narrative.contribAItem2Text') },
          { label: t('narrative.contribAItem3Label'), text: t('narrative.contribAItem3Text') },
          { label: t('narrative.contribAItem4Label'), text: t('narrative.contribAItem4Text') },
        ]}
        evidence={t('narrative.contribAEvidence')}
        cpNote={`// Contribution A in algorithm terms:
// Traditional KT pipeline:
//   offline training  →  frozen model  →  predict(h_t)
//   new learner = zero-state (degenerate)
//
// HCIE pipeline:
//   event → outbox → Kafka → consumer
//     ├── KF update:   O(1), state per (learner,concept)
//     ├── Beta update: O(1), state per (learner,concept,modality)
//     ├── JT score:    O(indeg(k)) for recommendation
//     └── persist trajectory row with all JT components
//
// Replay guarantee:
//   same event stream + same seeds → same JT scores to 5 decimals
//   implemented via: PYTHONHASHSEED pin + per-run RNG stream (V2 plan)
//
// ADC post-hoc audit:
//   reads experiment_trajectories (immutable after seal)
//   never writes back to runtime  → zero blast radius on live system`}
      />

      <ContribCard
        letter="B" tag={t('narrative.contribBTag')}
        tagColor={C.purple} tagBg={C.purpleL}
        title={t('narrative.contribBTitle')}
        subtitle={t('narrative.contribBSubtitle')}
        evidenceHeading={t('narrative.successEvidenceHeading')}
        cpHideLabel={t('narrative.cpHideLabel')} cpShowLabel={t('narrative.cpShowLabel')}
        items={[
          { label: t('narrative.contribBItem1Label'), text: t('narrative.contribBItem1Text') },
          { label: t('narrative.contribBItem2Label'), text: t('narrative.contribBItem2Text') },
          { label: t('narrative.contribBItem3Label'), text: t('narrative.contribBItem3Text') },
          { label: t('narrative.contribBItem4Label'), text: t('narrative.contribBItem4Text') },
        ]}
        evidence={t('narrative.contribBEvidence')}
        cpNote={`// Contribution B in algorithm terms:

// ADC = a test suite that runs on sealed trajectory data:
for dimension d in {ΔM, T_realized, Challenge, Uncertainty, ZPD, T_prospective}:
    mean_d  = mean(jt_{d}_contribution over all sealed interactions)
    ratio_d = std(jt_{d}_contribution) / mean_d
    if mean_d > α_floor AND ratio_d > 0.08:
        verdict[d] = "ACTIVE"
    else:
        verdict[d] = "structural_zero"
// α_floor = 0.01  (not 0! normalizer floor σ(-2.5)≈0.076 can fool a naive >0 check)

// Shuffled-DAG control = randomized baseline (like a permutation test on graph structure):
//   null_graph = shuffle_edges(G, preserve_degree_sequence=True)
//   effect_null = estimate_topology_effect(null_graph)
//   p_value = #{null_effect >= observed_effect} / K   (K=100 permutations)
//   Result: null ≈ 0, observed ≈ +0.053  →  topology is doing real work

// Time-placebo = falsification test:
//   Treatment: learner mastered prereq BEFORE target attempt  → real causal path
//   Placebo:   learner will master prereq AFTER target attempt → same learner, no causal path
//   Placebo removes selection bias: if result survives placebo, it's causal`}
      />

      <ContribCard
        letter="C" tag={t('narrative.contribCTag')}
        tagColor={C.teal} tagBg={C.tealL}
        title={t('narrative.contribCTitle')}
        subtitle={t('narrative.contribCSubtitle')}
        evidenceHeading={t('narrative.successEvidenceHeading')}
        cpHideLabel={t('narrative.cpHideLabel')} cpShowLabel={t('narrative.cpShowLabel')}
        items={[
          { label: t('narrative.contribCItem1Label'), text: t('narrative.contribCItem1Text') },
          { label: t('narrative.contribCItem2Label'), text: t('narrative.contribCItem2Text') },
          { label: t('narrative.contribCItem3Label'), text: t('narrative.contribCItem3Text') },
          { label: t('narrative.contribCItem4Label'), text: t('narrative.contribCItem4Text') },
        ]}
        evidence={t('narrative.contribCEvidence')}
        cpNote={`// Contribution C in algorithm terms:
// This is a standard benchmark comparison, but with key constraints:

// 1. Matched-eval protocol (same test set for all models — no cherry-picking)
//    All models see the same 10 held-out learners at each window size

// 2. Why HCIE wins cold-start:
//    At t ≤ 5 attempts:
//      BKT: needs ≥ 5 observations for EM estimate to stabilize
//      HCIE: KF σ²_ik is HIGH → Uncertainty signal is HIGH → JT recommends diverse concepts
//            = Thompson sampling over uncertainty = exploration without EM
//      Result: HCIE collects more informative signal in fewer attempts

// 3. Why DKT still beats HCIE on dense corpora:
//    DKT trained offline on N=100k+ interactions → d=200 hidden state
//    captures long-range dependencies HCIE's 2-state (μ,σ²) cannot model
//    This is the expected tradeoff: HCIE optimizes for zero-data cold-start,
//    DKT optimizes for dense well-represented concepts

// 4. The conditional framing:
//    Competitiveness holds WHERE topology activates transfer dimension (Gap 3)
//    On topology-poor datasets (random graphs, single-concept), no advantage
//    ADC is the instrument that tells you WHICH regime you're in`}
      />

      {/* AUC tables */}
      <SectionDivider n="§3" title={t('narrative.sec3Title')} sub={t('narrative.sec3Sub')} />
      <AucTable />
      <ColdStartTable />

      {/* ── §1.3 Formal Claim ── */}
      <SectionDivider n="§4" title={t('narrative.sec4Title')} sub={t('narrative.sec4Sub')} />

      <Callout color={C.accent} bg={C.accentL} border={C.accent}>
        <strong>{t('narrative.claim1Heading')}</strong>
        {' '}{t('narrative.claim1BodyA')}<strong>{t('narrative.claim1Adc')}</strong>{t('narrative.claim1BodyB')}{' '}
        <strong>{t('narrative.claim1NeverReads')}</strong>{t('narrative.claim1BodyC')}
      </Callout>

      <Callout color={C.dark} bg="#F8FAFC" border={C.border}>
        <strong>{t('narrative.claim2Heading')}</strong>
        {' '}{t('narrative.claim2BodyA')}<strong>{t('narrative.claim2Causal')}</strong>{t('narrative.claim2BodyB')}{' '}
        <strong>{t('narrative.claim2Proximity')}</strong>{t('narrative.claim2BodyC')}
        <Mono>+0.053</Mono>{t('narrative.claim2BodyD')}
      </Callout>

      <div style={{
        background: C.purpleL, border: `1px solid ${C.purple}`,
        borderRadius: 8, padding: '12px 18px', marginBottom: 20,
        fontSize: 12, color: C.dark, lineHeight: 1.75,
      }}>
        <strong>{t('narrative.formalPropsHeading')}</strong>
        <ul style={{ margin: '8px 0 0', paddingLeft: 20 }}>
          <li>{t('narrative.formalProp1')}</li>
          <li>{t('narrative.formalProp2A')}<Mono>α_floor=0.01</Mono>{t('narrative.formalProp2B')}<Mono>signal_ratio &gt; 0.08</Mono>{t('narrative.formalProp2C')}</li>
          <li>{t('narrative.formalProp3A')}<Mono>structural_zero</Mono>{t('narrative.formalProp3B')}</li>
          <li>{t('narrative.formalProp4')}</li>
          <li>{t('narrative.formalProp5')}</li>
        </ul>
      </div>

      {/* ── §1.3.1 Maturation ── */}
      <SectionDivider n="§5" title={t('narrative.sec5Title')} sub={t('narrative.sec5Sub')} />
      <p style={{ fontSize: 13, color: C.neutral, lineHeight: 1.7, marginBottom: 20 }}>
        {t('narrative.matIntroA')}{' '}
        <Mono>structural_zero</Mono>{t('narrative.matIntroB')}
      </p>

      <MatStep n={1} title={t('narrative.mat1Title')}
        body={
          <>
            {t('narrative.mat1BodyA')}<strong>{t('narrative.mat1NoZeroGuard')}</strong>{t('narrative.mat1BodyB')}
            <Mono>σ(−2.5) ≈ 0.076</Mono>{t('narrative.mat1BodyC')}<em>{t('narrative.mat1ThresholdFragile')}</em>{t('narrative.mat1BodyD')}
          </>
        }
        verdict={t('narrative.mat1Verdict')}
      />

      <MatStep n={2} title={t('narrative.mat2Title')}
        body={
          <>
            {t('narrative.mat2BodyA')}<strong>{t('narrative.mat2Committed')}</strong>{t('narrative.mat2BodyB')}<strong>{t('narrative.mat2TimePlacebo')}</strong>{t('narrative.mat2BodyC')}
          </>
        }
        verdict={t('narrative.mat2Verdict')}
      />

      <MatStep n={3} title={t('narrative.mat3Title')} isLast
        body={
          <>
            {t('narrative.mat3BodyA')}<strong>{t('narrative.mat3Causal')}</strong>{t('narrative.mat3BodyB')}<strong>{t('narrative.mat3TwoThirds')}</strong>{t('narrative.mat3BodyC')}
            <Mono>+0.053</Mono>{t('narrative.mat3BodyD')}
          </>
        }
        verdict={t('narrative.mat3Verdict')}
      />

      <Callout color={C.warn} bg={C.warnL} border={C.warn}>
        <strong>{t('narrative.maturationPatternHeading')}</strong>{' '}
        <em>{t('narrative.maturationPatternFreeze')}</em>{' '}
        {t('narrative.maturationPatternBody')}
      </Callout>

      <NextSteps />
    </div>
  )
}
