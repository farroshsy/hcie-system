'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, LabelList,
} from 'recharts'
import { getBackendUrl } from '@/lib/api/backend-url'
import { Panel, Tag, Callout, SectionTitle, Eyebrow, Stat } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'

// ── Types (mirror GET /v3/frontend/dashboard/modality-effectiveness) ──────────
type ByModality = {
  modality: string
  learners: number
  avg_mastery_gain: number
  avg_attempts: number
  engagements: number
}
type ByConceptModality = { concept_id: string; modality: string; avg_mastery_gain: number; n: number }
type ByGradeModality = { grade_band: string; modality: string; avg_mastery_gain: number; n: number }
type Totals = { engagements: number; learners: number; concepts: number }
type Payload = {
  by_modality: ByModality[]
  by_concept_modality: ByConceptModality[]
  by_gradeband_modality: ByGradeModality[]
  totals: Totals
  note?: string
  authority?: string
}

// Stable per-modality colours so a modality is the same hue in every chart.
const MODALITY_COLOR: Record<string, string> = {
  reading: '#2980B9',
  diagram: '#8E44AD',
  audio: '#16A085',
  interactive: '#E67E22',
  video: '#C0392B',
}
const MODALITY_ICON: Record<string, string> = {
  reading: '📖', diagram: '📊', audio: '🎧', interactive: '🎮', video: '🎬',
}
const colorFor = (m: string) => MODALITY_COLOR[m] ?? ui.color.muted

const BACKEND_URL = getBackendUrl()

const pct = (v: number) => `${(v * 100).toFixed(1)}%`

// ── Small building blocks ─────────────────────────────────────────────────────
function EmptyState({ n, label }: { n: number; label: string }) {
  return (
    <div style={{
      padding: '32px 20px', textAlign: 'center', color: ui.color.muted,
      fontSize: ui.font.size.md, lineHeight: 1.6,
    }}>
      <div style={{ fontSize: 26, marginBottom: 8 }}>📭</div>
      <div><strong>{n}</strong> {label}</div>
      <div style={{ fontSize: ui.font.size.sm, marginTop: 4, color: ui.color.faint }}>
        The chart fills in as learners open study materials on /learn.
      </div>
    </div>
  )
}

/** One "research question → which chart answers it" row. */
function QuestionRow({ q, chart, tone }: { q: string; chart: string; tone: 'info' | 'accent' | 'ok' | 'warn' }) {
  return (
    <div style={{
      display: 'flex', gap: 12, alignItems: 'flex-start',
      padding: '10px 0', borderTop: `1px solid ${ui.color.line}`,
    }}>
      <Tag tone={tone} style={{ flexShrink: 0, marginTop: 2 }}>{chart}</Tag>
      <div style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.5 }}>{q}</div>
    </div>
  )
}

export default function ModalityLabPage() {
  const [data, setData] = useState<Payload | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${BACKEND_URL}/v3/frontend/dashboard/modality-effectiveness`)
      .then(r => r.json())
      .then(setData)
      .catch(e => setError(String(e)))
  }, [])

  // Chart 1 data — avg mastery gain by modality.
  const modalityBars = useMemo(
    () => (data?.by_modality ?? []).map(d => ({ ...d, label: d.modality })),
    [data],
  )

  // Chart 2 data — pivot concept × modality into one row per concept, with the
  // best modality flagged. Grouped bars per concept.
  const { conceptRows, conceptModalities } = useMemo(() => {
    const rows = data?.by_concept_modality ?? []
    const mods = Array.from(new Set(rows.map(r => r.modality)))
    const byConcept: Record<string, any> = {}
    for (const r of rows) {
      byConcept[r.concept_id] = byConcept[r.concept_id] || { concept_id: r.concept_id }
      byConcept[r.concept_id][r.modality] = r.avg_mastery_gain
    }
    // flag the winning modality per concept
    const out = Object.values(byConcept).map((row: any) => {
      let best: string | null = null
      let bestVal = -Infinity
      for (const m of mods) {
        if (typeof row[m] === 'number' && row[m] > bestVal) { bestVal = row[m]; best = m }
      }
      return { ...row, _best: best }
    })
    return { conceptRows: out, conceptModalities: mods }
  }, [data])

  // Chart 3 data — grade-band × modality grouped bars.
  const { gradeRows, gradeModalities } = useMemo(() => {
    const rows = data?.by_gradeband_modality ?? []
    const mods = Array.from(new Set(rows.map(r => r.modality)))
    const order = ['K-2', 'K-5', 'K-8', 'K-12']
    const byBand: Record<string, any> = {}
    for (const r of rows) {
      byBand[r.grade_band] = byBand[r.grade_band] || { grade_band: r.grade_band }
      byBand[r.grade_band][r.modality] = r.avg_mastery_gain
    }
    const out = Object.values(byBand).sort((a: any, b: any) => {
      const ia = order.indexOf(a.grade_band); const ib = order.indexOf(b.grade_band)
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
    })
    return { gradeRows: out, gradeModalities: mods }
  }, [data])

  const totals = data?.totals ?? { engagements: 0, learners: 0, concepts: 0 }
  const hasAny = totals.engagements > 0

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1180, margin: '0 auto' }}>
      {/* ── Header + honest intent caption ── */}
      <Eyebrow color="#8E44AD">Research foundation · Observability</Eyebrow>
      <SectionTitle
        sub="Which modality helps which concept — and which grade-band. This is the data layer for future modality-vs-learning-speed studies.">
        Modality Effectiveness Lab
      </SectionTitle>

      <Callout tone="warn" title="Observational, not causal." style={{ marginBottom: 20 }}>
        The modality shown here is <strong>learner-chosen</strong> — it records which study material a
        learner opened, not a modality the bandit assigned. It never feeds the MAB and never touches
        the sealed evaluation (headline AUC 0.6051 is untouched). Read these charts as
        <em> "learners who chose X gained Y"</em>, a foundation for a future controlled study of
        modality → learning speed, not as a causal claim today.
      </Callout>

      {/* ── Totals strip ── */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <Stat label="Engagements recorded" value={totals.engagements} tone="info" />
        <Stat label="Distinct learners" value={totals.learners} tone="accent" />
        <Stat label="Concepts touched" value={totals.concepts} tone="ok" />
        <Stat
          label="Modalities observed"
          value={new Set((data?.by_modality ?? []).map(d => d.modality)).size}
          tone="neutral"
        />
      </div>

      {error && (
        <Callout tone="bad" title="Could not load." style={{ marginBottom: 20 }}>{error}</Callout>
      )}

      {/* ── Chart 1: avg mastery gain by modality ── */}
      <Panel style={{ marginBottom: 20 }}>
        <SectionTitle sub="Mean per-learner mastery gain on the concepts each modality was opened for. Bars are the observed average; the caption below each is the sample size.">
          1 · Average mastery gain by modality
        </SectionTitle>
        {modalityBars.length === 0 ? (
          <EmptyState n={totals.engagements} label="engagements so far — no modality has enough data yet." />
        ) : (
          <>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={modalityBars} margin={{ top: 20, right: 16, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
                <XAxis dataKey="label" tick={{ fontSize: 12, fill: ui.color.body }}
                  tickFormatter={(m: string) => `${MODALITY_ICON[m] ?? '·'} ${m}`} />
                <YAxis tick={{ fontSize: 11, fill: ui.color.muted }}
                  tickFormatter={(v: number) => v.toFixed(2)} />
                <Tooltip
                  formatter={(v: number) => [v.toFixed(4), 'avg mastery gain']}
                  labelFormatter={(m: string) => `${MODALITY_ICON[m] ?? ''} ${m}`} />
                <Bar dataKey="avg_mastery_gain" radius={[4, 4, 0, 0]}>
                  {modalityBars.map((d, i) => <Cell key={i} fill={colorFor(d.modality)} />)}
                  <LabelList dataKey="avg_mastery_gain" position="top"
                    formatter={(v: number) => v.toFixed(3)}
                    style={{ fontSize: 11, fill: ui.color.body }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 10 }}>
              {modalityBars.map(d => (
                <span key={d.modality} style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>
                  <span style={{ color: colorFor(d.modality), fontWeight: 700 }}>
                    {MODALITY_ICON[d.modality] ?? ''} {d.modality}
                  </span>{' '}· {d.learners} learners · {d.engagements} views · ~{d.avg_attempts} attempts
                </span>
              ))}
            </div>
          </>
        )}
      </Panel>

      {/* ── Chart 2: concept × modality ── */}
      <Panel style={{ marginBottom: 20 }}>
        <SectionTitle sub="For each concept, which modality shows the highest observed mastery gain. Winning modality is starred in the table.">
          2 · Best modality per concept
        </SectionTitle>
        {conceptRows.length === 0 ? (
          <EmptyState n={totals.concepts} label="concepts with engagements — need materials opened across concepts." />
        ) : (
          <>
            <ResponsiveContainer width="100%" height={Math.max(220, conceptRows.length * 42)}>
              <BarChart data={conceptRows} layout="vertical"
                margin={{ top: 8, right: 24, left: 8, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
                <XAxis type="number" tick={{ fontSize: 11, fill: ui.color.muted }}
                  tickFormatter={(v: number) => v.toFixed(2)} />
                <YAxis type="category" dataKey="concept_id" width={150}
                  tick={{ fontSize: 11, fill: ui.color.body }} />
                <Tooltip formatter={(v: number, name: string) => [Number(v).toFixed(4), name]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {conceptModalities.map(m => (
                  <Bar key={m} dataKey={m} fill={colorFor(m)} radius={[0, 3, 3, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
            {/* Compact winner table */}
            <div style={{ overflowX: 'auto', marginTop: 12 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: ui.font.size.sm }}>
                <thead>
                  <tr style={{ textAlign: 'left', color: ui.color.muted }}>
                    <th style={{ padding: '6px 8px' }}>Concept</th>
                    <th style={{ padding: '6px 8px' }}>Best modality</th>
                    <th style={{ padding: '6px 8px' }}>Gain</th>
                  </tr>
                </thead>
                <tbody>
                  {conceptRows.map((row: any) => (
                    <tr key={row.concept_id} style={{ borderTop: `1px solid ${ui.color.line}` }}>
                      <td style={{ padding: '6px 8px', color: ui.color.body }}>{row.concept_id}</td>
                      <td style={{ padding: '6px 8px' }}>
                        {row._best ? (
                          <span style={{ color: colorFor(row._best), fontWeight: 700 }}>
                            {MODALITY_ICON[row._best] ?? ''} {row._best} ★
                          </span>
                        ) : <span style={{ color: ui.color.faint }}>—</span>}
                      </td>
                      <td style={{ padding: '6px 8px', color: ui.color.body }}>
                        {row._best && typeof row[row._best] === 'number' ? row[row._best].toFixed(4) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Panel>

      {/* ── Chart 3: grade-band × modality ── */}
      <Panel style={{ marginBottom: 20 }}>
        <SectionTitle sub="Observed mastery gain by grade-band (K-2 / K-5 / K-8 / K-12) and modality — which modality suits which age band.">
          3 · Grade-band × modality
        </SectionTitle>
        {gradeRows.length === 0 ? (
          <EmptyState n={totals.engagements} label="grade-band-tagged engagements — fills as learners across grades use materials." />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={gradeRows} margin={{ top: 16, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
              <XAxis dataKey="grade_band" tick={{ fontSize: 12, fill: ui.color.body }} />
              <YAxis tick={{ fontSize: 11, fill: ui.color.muted }}
                tickFormatter={(v: number) => v.toFixed(2)} />
              <Tooltip formatter={(v: number, name: string) => [Number(v).toFixed(4), name]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {gradeModalities.map(m => (
                <Bar key={m} dataKey={m} fill={colorFor(m)} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </Panel>

      {/* ── Research-questions panel (the intent) ── */}
      <Panel tone="accent">
        <Eyebrow color="#6C3483">The point of this page</Eyebrow>
        <SectionTitle sub="Each question below maps to a chart above. This is the observability foundation the thesis reviewer asked for — it makes modality a first-class research variable.">
          Research questions this answers
        </SectionTitle>
        <QuestionRow chart="Chart 1"
          q="How does mastery gain differ per modality — is reading, interactive, or audio associated with more learning on average?" tone="info" />
        <QuestionRow chart="Chart 2"
          q="Which modality suits which concept — does a given concept learn best via diagram vs reading vs interactive?" tone="accent" />
        <QuestionRow chart="Chart 3"
          q="Which grade-band suits which modality — do younger (K-2) learners benefit more from audio/interactive than older (K-12)?" tone="ok" />
        <QuestionRow chart="Chart 1 + attempts"
          q="How fast per modality — average attempts-to-mastery alongside gain hints at learning speed per modality (foundation for a timed study)." tone="warn" />
        <div style={{ marginTop: 14, fontSize: ui.font.size.sm, color: ui.color.muted, lineHeight: 1.6 }}>
          {data?.authority && <>Authority: <code>{data.authority}</code>. </>}
          Next step for a causal answer: randomise the offered modality (A/B) instead of letting the
          learner choose, then re-run these three cuts.
        </div>
      </Panel>

      {!hasAny && !error && (
        <Callout tone="info" style={{ marginTop: 20 }}>
          No engagements recorded yet. As learners open reading / diagram / audio / interactive / video
          materials on <code>/learn</code>, a beacon records the modality and this lab fills in.
        </Callout>
      )}
    </div>
  )
}
