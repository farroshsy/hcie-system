'use client'

/**
 * /learners/launch — create + launch a synthetic cohort. Spawns
 * archetypes × policies × seeds × learners_per_cell synthetic learners that run
 * through the REAL recommend → attempt loop (server-orchestrated), recorded to
 * experiment_trajectories. POST /v3/experiments/cohorts → POST …/{id}/launch.
 * Both are researcher/admin-gated; the form surfaces that honestly.
 */
import { useState } from 'react'
import Link from 'next/link'
import { useT } from '@/contexts/language_context'

const ARCHETYPES = ['novice', 'intermediate', 'advanced', 'struggling', 'average']
const POLICIES = ['hcie', 'bandit', 'thompson', 'ucb', 'epsilon_greedy',
  'mastery_greedy', 'zpd_aligned', 'uncertainty_reduction', 'random', 'static']

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined'
    ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

export default function LaunchCohortPage() {
  const t = useT()
  const [name, setName] = useState('demo cohort')
  const [archetypes, setArchetypes] = useState<string[]>(['novice', 'intermediate'])
  const [policies, setPolicies] = useState<string[]>(['hcie', 'bandit'])
  const [concepts, setConcepts] = useState('k2_algorithms, k5_algorithms')
  const [perCell, setPerCell] = useState(3)
  const [interactions, setInteractions] = useState(30)
  const [freeSelect, setFreeSelect] = useState(true)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; msg: string; runId?: string } | null>(null)

  const toggle = (arr: string[], set: (v: string[]) => void, v: string) =>
    set(arr.includes(v) ? arr.filter(x => x !== v) : [...arr, v])

  const cells = archetypes.length * policies.length
  const totalLearners = cells * perCell
  const totalInteractions = totalLearners * interactions

  const launch = async () => {
    setBusy(true); setResult(null)
    try {
      const spec = {
        name,
        archetypes,
        policies,
        seeds: [42],
        concepts: concepts.split(',').map(s => s.trim()).filter(Boolean),
        learners_per_cell: perCell,
        interactions_per_learner: interactions,
        free_concept_selection: freeSelect,
        metadata: { source: 'frontend /learners/launch' },
      }
      if (!spec.concepts.length) { setResult({ ok: false, msg: t('launchPage.errNoConcept') }); setBusy(false); return }
      if (!archetypes.length || !policies.length) { setResult({ ok: false, msg: t('launchPage.errNoArchetypePolicy') }); setBusy(false); return }

      const cRes = await fetch('/v3/experiments/cohorts',
        { method: 'POST', headers: authHeaders(), body: JSON.stringify(spec) })
      if (cRes.status === 401 || cRes.status === 403) {
        setResult({ ok: false, msg: t('launchPage.errAuth') }); setBusy(false); return
      }
      if (!cRes.ok) { setResult({ ok: false, msg: `${t('launchPage.errCreateFailed')} (${cRes.status}): ${(await cRes.text()).slice(0, 200)}` }); setBusy(false); return }
      const cohort = await cRes.json()
      const cohortId = cohort.cohort_id
      if (!cohortId) { setResult({ ok: false, msg: t('launchPage.errNoCohortId') }); setBusy(false); return }

      const lRes = await fetch(`/v3/experiments/cohorts/${encodeURIComponent(cohortId)}/launch`,
        { method: 'POST', headers: authHeaders(), body: JSON.stringify({ reason: 'frontend demo launch' }) })
      if (!lRes.ok) { setResult({ ok: false, msg: `${t('launchPage.errLaunchFailed')} (${lRes.status}): ${(await lRes.text()).slice(0, 200)}` }); setBusy(false); return }
      const run = await lRes.json()
      setResult({ ok: true, runId: run.run_id, msg: `${t('launchPage.launchedPrefix')} ${totalLearners} ${t('launchPage.launchedSuffix')}` })
    } catch (e: any) {
      setResult({ ok: false, msg: `${t('launchPage.errNetwork')}: ${String(e).slice(0, 160)}` })
    } finally { setBusy(false) }
  }

  const card: React.CSSProperties = { background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 18, marginBottom: 16 }
  const chip = (on: boolean, color: string): React.CSSProperties => ({
    padding: '5px 11px', fontSize: 12, fontWeight: 600, borderRadius: 8, cursor: 'pointer',
    border: `1px solid ${on ? color : '#CBD5E0'}`, background: on ? color : '#fff', color: on ? '#fff' : '#4A5568',
  })

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '28px 24px 80px', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Link href="/learners" style={{ fontSize: 13, color: '#1A5276', textDecoration: 'none' }}>← {t('launchPage.backLink')}</Link>
      <h1 style={{ fontSize: 24, fontWeight: 800, color: '#1A2332', margin: '8px 0 6px' }}>{t('launchPage.title')}</h1>
      <p style={{ fontSize: 13.5, color: '#5A6776', lineHeight: 1.6, marginBottom: 18, maxWidth: 720 }}>
        {t('launchPage.introLead')} <b>archetypes × policies × {perCell}</b> {t('launchPage.introMid1')} <b>{interactions}</b> {t('launchPage.introMid2')}
        <b> {t('launchPage.introReal')}</b> {t('launchPage.introMid3')}
        <code> experiment_trajectories</code>. {t('launchPage.introTail')} <b>{t('launchPage.introSynthetic')}</b>.
      </p>

      <div style={card}>
        <label style={{ fontSize: 12, fontWeight: 700, color: '#4A5568' }}>{t('launchPage.cohortNameLabel')}</label>
        <input value={name} onChange={e => setName(e.target.value)} style={{ width: '100%', marginTop: 6, padding: '8px 10px', fontSize: 13, border: '1px solid #CBD5E0', borderRadius: 8 }} />
      </div>

      <div style={card}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#4A5568', marginBottom: 8 }}>{t('launchPage.archetypesLabel')}</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {ARCHETYPES.map(a => <button key={a} onClick={() => toggle(archetypes, setArchetypes, a)} style={chip(archetypes.includes(a), '#2980B9')}>{a}</button>)}
        </div>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#4A5568', margin: '14px 0 8px' }}>{t('launchPage.policiesLabel')}</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {POLICIES.map(p => <button key={p} onClick={() => toggle(policies, setPolicies, p)} style={chip(policies.includes(p), '#8E44AD')}>{p}</button>)}
        </div>
      </div>

      <div style={card}>
        <label style={{ fontSize: 12, fontWeight: 700, color: '#4A5568' }}>{t('launchPage.conceptsLabel')}</label>
        <input value={concepts} onChange={e => setConcepts(e.target.value)} style={{ width: '100%', marginTop: 6, padding: '8px 10px', fontSize: 13, border: '1px solid #CBD5E0', borderRadius: 8, fontFamily: 'ui-monospace, monospace' }} />
        <div style={{ display: 'flex', gap: 18, marginTop: 14, flexWrap: 'wrap' }}>
          <label style={{ fontSize: 12, color: '#4A5568' }}>{t('launchPage.learnersPerCellLabel')}
            <input type="number" min={1} max={100} value={perCell} onChange={e => setPerCell(Math.max(1, Math.min(100, +e.target.value || 1)))} style={{ width: 70, marginLeft: 8, padding: '5px 8px', border: '1px solid #CBD5E0', borderRadius: 6 }} />
          </label>
          <label style={{ fontSize: 12, color: '#4A5568' }}>{t('launchPage.interactionsPerLearnerLabel')}
            <input type="number" min={1} max={1000} value={interactions} onChange={e => setInteractions(Math.max(1, Math.min(1000, +e.target.value || 1)))} style={{ width: 80, marginLeft: 8, padding: '5px 8px', border: '1px solid #CBD5E0', borderRadius: 6 }} />
          </label>
          <label style={{ fontSize: 12, color: '#4A5568', display: 'flex', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" checked={freeSelect} onChange={e => setFreeSelect(e.target.checked)} /> {t('launchPage.freeSelectLabel')}
          </label>
        </div>
      </div>

      <div style={{ background: '#FEF9F0', border: '1px solid #F5D5A0', borderRadius: 10, padding: '10px 14px', marginBottom: 16, fontSize: 12.5, color: '#7E5109' }}>
        {t('launchPage.estimateLead')} <b>{cells} {t('launchPage.estimateCells')}</b> → <b>{totalLearners} {t('launchPage.estimateLearners')}</b> → ~<b>{totalInteractions.toLocaleString()}</b> {t('launchPage.estimateInteractions')} {t('launchPage.estimateNote')}
      </div>

      <button onClick={launch} disabled={busy} style={{
        padding: '11px 22px', fontSize: 14, fontWeight: 700, color: '#fff', border: 'none', borderRadius: 10,
        background: busy ? '#B39CC9' : '#8E44AD', cursor: busy ? 'default' : 'pointer',
      }}>{busy ? `⟳ ${t('launchPage.launchingButton')}` : `+ ${t('launchPage.createButton')}`}</button>

      {result && (
        <div style={{ marginTop: 16, padding: '14px 16px', borderRadius: 10, fontSize: 13.5, lineHeight: 1.6,
          background: result.ok ? '#F0FAF4' : '#FDEDEC', border: `1px solid ${result.ok ? '#B7E0D7' : '#F5B7B1'}`,
          color: result.ok ? '#1B5E55' : '#922B21' }}>
          {result.ok ? '✓ ' : '⚠ '}{result.msg}
          {result.runId && <div style={{ marginTop: 8, fontFamily: 'ui-monospace, monospace', fontSize: 12 }}>
            run_id: {result.runId} · <Link href="/learners" style={{ color: '#1A5276' }}>{t('launchPage.seeInSelector')} →</Link>
          </div>}
        </div>
      )}
    </div>
  )
}
