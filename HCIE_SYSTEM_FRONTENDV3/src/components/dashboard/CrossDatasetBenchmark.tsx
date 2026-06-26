'use client'

/**
 * Cross-dataset KT benchmark — the two figures the manuscripts need that no
 * single page showed before:
 *   (A) fig08b — unified 8-models × 5-datasets AUC matrix (heatmap), LIVE from
 *       /v3/frontend/dashboard/kt-benchmark-matrix (canonical sealed runs).
 *   (B) F10 — KT scale sweep (AUC vs N), from the sealed frozen artifact
 *       /data/kt/scale_sweep_summary.json (15-cell sweep, 30/100/500 users).
 *
 * HCIE is zero-shot; trained baselines train on the same held-out users.
 */

import { useEffect, useState } from 'react'
import { getBackendUrl } from '@/lib/api/backend-url'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'

const BACKEND = getBackendUrl()

// Fixed model order so the matrix reads the same every time (HCIE = the subject, first).
const MODEL_ORDER = ['hcie', 'sakt', 'dkt', 'bkt', 'irt_1pl', 'greedy_correct_rate', 'random', 'static_prior']
const MODEL_LABEL: Record<string, string> = {
  hcie: 'HCIE', sakt: 'SAKT', dkt: 'DKT', bkt: 'BKT', irt_1pl: 'IRT-1PL',
  greedy_correct_rate: 'Greedy', random: 'Random', static_prior: 'Static',
}
const MODEL_COLOR: Record<string, string> = {
  hcie: '#6C3483', sakt: '#2980B9', dkt: '#16A085', bkt: '#1E8449',
  irt_1pl: '#E67E22', greedy_correct_rate: '#7F8C8D', random: '#C0392B', static_prior: '#BDC3C7',
}
// Datasets in a fixed left→right order for the matrix.
const DATASET_ORDER = ['junyi_2015', 'assistments_2015_skill', 'csedm_f19', 'ednet_kt1', 'statics_2011']
const SWEEP_LABEL: Record<string, string> = {
  junyi_2015: 'Junyi 2015', assistments_2015_skill: 'ASSISTments 2015',
  assistments_2009_skill: 'ASSISTments 2009', csedm_f19: 'CSEDM F19',
  ednet_kt1: 'EdNet KT1', statics_2011: 'STATICS 2011',
}

function authHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// AUC → heat color. 0.5 (chance) = pale red, 0.75+ = green.
function aucColor(v: number | null | undefined): string {
  if (v == null) return '#F1F5F9'
  const t = Math.max(0, Math.min(1, (v - 0.5) / 0.25))
  return `hsl(${Math.round(t * 120)}, 58%, ${Math.round(86 - t * 26)}%)`
}

export function CrossDatasetBenchmark() {
  const [matrix, setMatrix] = useState<any>(null)
  const [matrixErr, setMatrixErr] = useState<string | null>(null)
  const [sweep, setSweep] = useState<any[]>([])
  const [sweepDataset, setSweepDataset] = useState('junyi_2015')
  const [sweepWindow, setSweepWindow] = useState<number>(20)

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/kt-benchmark-matrix`,
          { headers: authHeaders(), signal: AbortSignal.timeout(12000) })
        if (r.ok) { setMatrix(await r.json()); setMatrixErr(null) }
        else setMatrixErr(`benchmark matrix unavailable (HTTP ${r.status})`)
      } catch {
        // Surface the failure instead of rendering an empty table silently.
        setMatrixErr('benchmark matrix unavailable — could not reach the backend')
      }
    })()
  }, [])

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/data/kt/scale_sweep_summary.json', { signal: AbortSignal.timeout(12000) })
        if (r.ok) setSweep(await r.json())
      } catch { /* leave empty */ }
    })()
  }, [])

  // ── Matrix: model_id → { dataset → {auc, rank} } ─────────────────────────────
  const datasets: any[] = matrix?.datasets ?? []
  const presentModels = MODEL_ORDER.filter(mid =>
    datasets.some(d => (d.models ?? []).some((m: any) => m.model_id === mid)))
  const cell = (mid: string, dskey: string) => {
    const ds = datasets.find(d => d.dataset === dskey)
    return (ds?.models ?? []).find((m: any) => m.model_id === mid)
  }

  // ── Scale sweep: rows for the selected dataset+window, pivoted by N ───────────
  const sweepDatasets = Array.from(new Set(sweep.map(r => r.dataset)))
  const sweepRows = (() => {
    const ns = [30, 100, 500]
    return ns.map(n => {
      const row: any = { N: n }
      for (const mid of MODEL_ORDER) {
        const hit = sweep.find(r => r.dataset === sweepDataset && r.max_users === n
          && r.window === sweepWindow && r.model_id === mid)
        if (hit) row[mid] = hit.auc
      }
      return row
    })
  })()
  const sweepModels = MODEL_ORDER.filter(mid =>
    sweep.some(r => r.dataset === sweepDataset && r.model_id === mid))

  return (
    <div>
      {/* Intent */}
      <div style={{ background: 'linear-gradient(135deg, #EBF5FB, #F4ECF7)', border: '1px solid #C3CFE2',
                    borderRadius: 10, padding: '16px 20px', marginBottom: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#1A5276', marginBottom: 6,
                      textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          🔵 Cross-dataset — the whole generalization picture in one view
        </div>
        {!!matrixErr && !matrix && (
          <div style={{ marginTop: 10, padding: '8px 12px', borderRadius: 8,
                        background: '#FDEDEC', border: '1px solid #F5B7B1',
                        color: '#922B21', fontSize: 12, fontWeight: 600 }}>
            ⚠ {matrixErr}. The matrix below may be empty until the backend responds.
          </div>
        )}
        <div style={{ fontSize: 13, color: '#2C3E50', lineHeight: 1.65 }}>
          Every model on every dataset (overall AUC), plus how AUC moves with cohort size. HCIE is{' '}
          <strong>zero-shot</strong>; the trained baselines (incl. deep DKT/SAKT) see the same held-out users.
          The honest story: HCIE is a <strong>governance instrument</strong>, mid-pack on raw prediction —
          competitive on CSEDM, strong cold-start on STATICS, behind deep models elsewhere.
        </div>
      </div>

      {/* ════ (A) UNIFIED MATRIX — fig08b ════ */}
      <div style={{ background: '#fff', border: '2px solid #C3CFE2', borderRadius: 12,
                    padding: '18px 20px', marginBottom: 18 }}>
        <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332', marginBottom: 2 }}>
          Cross-dataset AUC matrix — 8 models × 5 datasets (overall window)
        </div>
        <div style={{ fontSize: 11, color: '#718096', marginBottom: 14 }}>
          Each cell = overall AUC; greener = stronger. HCIE row highlighted. Live from the canonical sealed runs.
        </div>

        {!matrix && <div style={{ textAlign: 'center', padding: 30, color: '#A0AEC0' }}>⟳ Loading matrix…</div>}

        {matrix && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'separate', borderSpacing: 0, width: '100%', minWidth: 620 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', fontSize: 11, color: '#718096', padding: '6px 10px', position: 'sticky', left: 0, background: '#fff' }}>Model</th>
                  {DATASET_ORDER.map(dskey => {
                    const ds = datasets.find(d => d.dataset === dskey)
                    return (
                      <th key={dskey} style={{ fontSize: 10.5, color: '#4A5568', fontWeight: 700, padding: '6px 8px', textAlign: 'center', minWidth: 96 }}>
                        {ds?.label ?? SWEEP_LABEL[dskey] ?? dskey}
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {presentModels.map(mid => (
                  <tr key={mid} style={{ background: mid === 'hcie' ? '#F4ECF7' : 'transparent' }}>
                    <td style={{ fontSize: 12, fontWeight: mid === 'hcie' ? 800 : 600,
                                 color: mid === 'hcie' ? '#6C3483' : '#4A5568', padding: '5px 10px',
                                 position: 'sticky', left: 0, background: mid === 'hcie' ? '#F4ECF7' : '#fff',
                                 borderLeft: `3px solid ${MODEL_COLOR[mid] ?? '#CBD5E0'}` }}>
                      {MODEL_LABEL[mid] ?? mid}
                    </td>
                    {DATASET_ORDER.map(dskey => {
                      const m = cell(mid, dskey)
                      const auc = m?.auc
                      const isBest = m?.rank === 1
                      return (
                        <td key={dskey} style={{
                          textAlign: 'center', fontSize: 12, padding: '5px 8px',
                          fontVariantNumeric: 'tabular-nums',
                          background: aucColor(auc),
                          fontWeight: (mid === 'hcie' || isBest) ? 800 : 500,
                          color: '#1A2332',
                          border: '1px solid #fff',
                          outline: isBest ? '2px solid #1E8449' : 'none', outlineOffset: -2,
                        }}>
                          {auc != null ? auc.toFixed(3) : '—'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
                {/* HCIE rank strip */}
                <tr>
                  <td style={{ fontSize: 10, color: '#6C3483', fontWeight: 700, padding: '6px 10px', position: 'sticky', left: 0, background: '#fff' }}>HCIE rank</td>
                  {DATASET_ORDER.map(dskey => {
                    const ds = datasets.find(d => d.dataset === dskey)
                    return (
                      <td key={dskey} style={{ textAlign: 'center', fontSize: 11, fontWeight: 700, color: '#6C3483', padding: '6px 8px' }}>
                        {ds?.hcie_rank ? `#${ds.hcie_rank}/${ds.n_models}` : '—'}
                      </td>
                    )
                  })}
                </tr>
              </tbody>
            </table>
            <div style={{ marginTop: 10, fontSize: 10.5, color: '#A0AEC0' }}>
              Green outline = best model in that dataset. HCIE n is lower (drops each user's first prediction). {matrix?.note}
            </div>
          </div>
        )}
      </div>

      {/* ════ (B) SCALE SWEEP — F10 ════ */}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12,
                    padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332', marginBottom: 2 }}>
          Scale sweep — AUC vs cohort size (N)
        </div>
        <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
          Does the ranking hold as N grows? Sealed 15-cell sweep (30 / 100 / 500 users). HCIE in bold purple.
        </div>

        {/* dataset + window pickers */}
        <div style={{ display: 'flex', gap: 14, marginBottom: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {sweepDatasets.map(ds => (
              <button key={ds} onClick={() => setSweepDataset(ds)} style={{
                padding: '4px 12px', fontSize: 11, fontWeight: 600, borderRadius: 6, cursor: 'pointer',
                border: `1px solid ${sweepDataset === ds ? '#1A5276' : '#CBD5E0'}`,
                background: sweepDataset === ds ? '#1A5276' : '#fff', color: sweepDataset === ds ? '#fff' : '#4A5568',
              }}>{SWEEP_LABEL[ds] ?? ds}</button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: '#718096', fontWeight: 700 }}>Window:</span>
            {[5, 10, 20].map(w => (
              <button key={w} onClick={() => setSweepWindow(w)} style={{
                padding: '4px 10px', fontSize: 11, fontWeight: 600, borderRadius: 6, cursor: 'pointer',
                border: `1px solid ${sweepWindow === w ? '#6C3483' : '#CBD5E0'}`,
                background: sweepWindow === w ? '#6C3483' : '#fff', color: sweepWindow === w ? '#fff' : '#4A5568',
              }}>≤{w}</button>
            ))}
          </div>
        </div>

        {sweep.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#A0AEC0' }}>⟳ Loading sweep…</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sweepRows} margin={{ left: 0, right: 24, top: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="N" type="number" scale="log" domain={[25, 600]} ticks={[30, 100, 500]}
                tick={{ fontSize: 11, fill: '#4A5568' }} axisLine={false} tickLine={false}
                label={{ value: 'cohort size N (log)', fontSize: 10, fill: '#A0AEC0', position: 'insideBottom', offset: -2 }} />
              <YAxis domain={[0.45, 0.85]} tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: any, n: any) => [v != null ? `${(Number(v) * 100).toFixed(1)}%` : '—', MODEL_LABEL[n] ?? n]} />
              <ReferenceLine y={0.5} stroke="#C0392B" strokeDasharray="4 4"
                label={{ value: 'chance', fontSize: 9, fill: '#C0392B', position: 'right' }} />
              {sweepModels.map(mid => (
                <Line key={mid} dataKey={mid} name={mid} stroke={MODEL_COLOR[mid] ?? '#4A5568'}
                  strokeWidth={mid === 'hcie' ? 3.5 : 1.5} dot={{ r: mid === 'hcie' ? 4 : 2 }}
                  type="monotone" opacity={mid === 'hcie' ? 1 : 0.7} connectNulls />
              ))}
              <Legend formatter={(v) => MODEL_LABEL[v] ?? v} wrapperStyle={{ fontSize: 10 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
        <div style={{ marginTop: 12, background: '#F8F9FF', border: '1px solid #C3CFE2', borderRadius: 8,
                      padding: '10px 14px', fontSize: 11, color: '#4A5568', lineHeight: 1.6 }}>
          <strong>Read:</strong> the model ranking is largely stable across N — deep models (SAKT/DKT) lead
          where embeddings pay off, HCIE stays mid-pack and zero-shot. The sweep is the reproducibility check
          behind the headline matrix above (sealed artifact, frozen).
        </div>
      </div>
    </div>
  )
}
