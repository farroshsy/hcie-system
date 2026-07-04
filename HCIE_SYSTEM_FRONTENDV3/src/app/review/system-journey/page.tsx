'use client'

/**
 * /review/system-journey — "be the learner, then the researcher" end-to-end.
 *
 * Three acts: (1) be a brand-new learner (go do real interactions on /learn); (2) watch the REAL
 * distributed system process them — live pipeline (outbox→Kafka→consumers→trajectory/projection),
 * system scale, governance (ADC) — auto-refreshed from the live /v3 endpoints; (3) be the researcher:
 * read the data your interaction produced + the aggregate science. The live panel IS the observability
 * (rendered from real metrics) so no monitoring container needs public exposure. Snapshot fallback so
 * the page is never empty for a logged-out reviewer.
 */

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getBackendUrl } from '@/lib/api/backend-url'
import { authHeaders } from '@/lib/api/auth-headers'
import { Panel, Callout, Eyebrow, Tag } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'

const BACKEND = getBackendUrl()
const fmt = (n: number) => n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'k' : String(n)

// Real snapshot (2026-06-25) — shown until/if the live fetch lands, so the page is never empty.
// `labelKey` is a stable i18n key so the ADC dimension name renders translated whether the data
// comes from this snapshot or the live API (resolved by `d.name` at render time).
const SNAP = {
  system: { interactions: { total: 1044014, unique_users: 5786, unique_concepts: 1307, avg_correct: 0.737 }, task_catalog: { total: 849225 }, trajectories: { total: 1104173 }, active_sessions: 0 },
  pipe: { stages: { outbox: { total: 2410620, published: 2410615, failed: 5 }, projection: { read_models: 61088 }, trajectory: { rows_estimated: 1044014 } },
    event_types: [{ type: 'ProjectionUpdated', count: 1204558 }, { type: 'AdaptationGenerated', count: 602305 }, { type: 'CognitionUpdated', count: 602302 }, { type: 'RecommendationGenerated', count: 1351 }, { type: 'user_registered', count: 104 }] },
  adc: { dimensions: [{ name: 'challenge', label: 'Challenge', signal_ratio: 0.222, status: 'ACTIVE' }, { name: 'uncertainty', label: 'Uncertainty', signal_ratio: 0.579, status: 'ACTIVE' }, { name: 'delta_m', label: 'Delta-M', signal_ratio: 0.427, status: 'ACTIVE' }, { name: 'zpd', label: 'ZPD', signal_ratio: 1.286, status: 'ACTIVE' }] },
}

// i18n key per ADC dimension name — keeps live + snapshot rendering consistent.
const ADC_LABEL_KEY: Record<string, string> = {
  challenge: 'systemJourney.adcDimChallenge',
  uncertainty: 'systemJourney.adcDimUncertainty',
  delta_m: 'systemJourney.adcDimDeltaM',
  zpd: 'systemJourney.adcDimZpd',
}

export default function SystemJourney() {
  const t = useT()
  const [live, setLive] = useState<{ system?: any; pipe?: any; adc?: any } | null>(null)
  const [ago, setAgo] = useState<number | null>(null)

  // The real services that process every interaction (the "all the containers" showcase).
  // Group names are translated; the item entries are concrete service/container names kept verbatim.
  const SERVICES = [
    { g: t('systemJourney.svcGroupServing'), items: ['api (FastAPI)', 'gateway (nginx)', 'frontend (Next.js)'] },
    { g: t('systemJourney.svcGroupState'), items: ['postgres', 'redis'] },
    { g: t('systemJourney.svcGroupEventBus'), items: ['redpanda / Kafka', 'outbox → CDC'] },
    { g: t('systemJourney.svcGroupConsumers'), items: ['learning', 'trajectory-recorder', 'projection', 'adaptation', 'exploration', 'transfer-measurement', 'dlq-replay'] },
    { g: t('systemJourney.svcGroupObservability'), items: ['prometheus', 'grafana', 'kafka-ui', 'cadvisor', 'dozzle', 'alertmanager'] },
  ]

  useEffect(() => {
    let alive = true
    const tick = async () => {
      const j = async (ep: string) => { try { const r = await fetch(`${BACKEND}/v3/frontend/dashboard/${ep}`, { headers: authHeaders() as HeadersInit }); return r.ok ? await r.json() : null } catch { return null } }
      const [system, pipe, adc] = await Promise.all([j('system-stats'), j('pipeline-stats'), j('adc-live-status')])
      if (alive && (system || pipe || adc)) { setLive({ system, pipe, adc }); setAgo(0) }
    }
    tick(); const iv = setInterval(tick, 5000); const ac = setInterval(() => setAgo(a => (a == null ? a : a + 1)), 1000)
    return () => { alive = false; clearInterval(iv); clearInterval(ac) }
  }, [])

  const isLive = !!live
  const sys = live?.system ?? SNAP.system
  const pipe = live?.pipe ?? SNAP.pipe
  const adc = live?.adc ?? SNAP.adc
  const evMax = Math.max(...pipe.event_types.map((e: any) => e.count))

  // Resolve an ADC dimension's display label: prefer a translated label keyed by `name`,
  // fall back to whatever label the data carried (live API or snapshot).
  const adcLabel = (d: any) => (d?.name && ADC_LABEL_KEY[d.name]) ? t(ADC_LABEL_KEY[d.name]) : (d?.label ?? d?.name ?? '')

  return (
    <div style={{ padding: '40px 48px', maxWidth: 980 }}>
      <Eyebrow color={ui.tone.info.fg}>{t('systemJourney.eyebrow')}</Eyebrow>
      <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, lineHeight: 1.25, marginBottom: ui.space.md }}>
        {t('systemJourney.title')}
      </h1>
      <p style={{ fontSize: ui.font.size.lg, color: ui.color.body, lineHeight: 1.6, maxWidth: 800, marginBottom: ui.space.xl }}>
        {t('systemJourney.introA')} <strong>{t('systemJourney.introRealSystem')}</strong> {t('systemJourney.introB')} <strong>{t('systemJourney.introLive')}</strong> {t('systemJourney.introC')}
      </p>

      {/* ACT 1 — be the learner */}
      <Eyebrow color={ui.tone.accent.fg}>{t('systemJourney.act1Eyebrow')}</Eyebrow>
      <Panel pad="lg" style={{ marginBottom: ui.space.xl }}>
        <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, marginBottom: ui.space.md }}>
          {t('systemJourney.act1HoldsA')} <strong>{fmt(sys.interactions.total)}</strong> {t('systemJourney.act1HoldsB')} <strong>{fmt(sys.interactions.unique_users)}</strong> {t('systemJourney.act1HoldsC')}
          {' '}<strong>{fmt(sys.interactions.unique_concepts)}</strong> {t('systemJourney.act1HoldsD')} <strong>{t('systemJourney.act1None')}</strong> {t('systemJourney.act1HoldsE')}
        </p>
        <Link href="/learn" style={{ textDecoration: 'none' }}>
          <div style={{ background: ui.tone.ok.bg, border: `1px solid ${ui.tone.ok.border}`, borderRadius: ui.radius.lg, padding: ui.space.lg, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.tone.ok.fg }}>{t('systemJourney.act1CtaTitle')}</div>
              <div style={{ fontSize: ui.font.size.md, color: ui.color.body, marginTop: 2 }}>{t('systemJourney.act1CtaBodyA')} <strong>{t('systemJourney.act1CtaBodyReal')}</strong> {t('systemJourney.act1CtaBodyB')}</div>
            </div>
            <span style={{ fontSize: 26, color: ui.tone.ok.fg }} aria-hidden>→</span>
          </div>
        </Link>
      </Panel>

      {/* ACT 2 — watch the real system */}
      <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.xs }}>
        <Eyebrow color={ui.tone.accent.fg}>{t('systemJourney.act2Eyebrow')}</Eyebrow>
        <Tag tone={isLive ? 'ok' : 'neutral'}>{isLive ? `${t('systemJourney.liveBadge')} · ${ago ?? 0}${t('systemJourney.secondsAgo')}` : t('systemJourney.snapshotBadge')}</Tag>
      </div>

      {/* pipeline flow */}
      <Panel pad="lg" style={{ marginBottom: ui.space.md }}>
        <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, marginBottom: ui.space.md }}>{t('systemJourney.pipelineCaption')}</div>
        <div style={{ display: 'flex', alignItems: 'stretch', gap: 4, flexWrap: 'wrap' }}>
          {[
            { k: t('systemJourney.pipeYourAnswer'), v: 'API', sub: '/v3/learner/attempt' },
            { k: t('systemJourney.pipeOutbox'), v: fmt(pipe.stages.outbox.published), sub: `${pipe.stages.outbox.failed} ${t('systemJourney.pipeFailed')}` },
            { k: 'Kafka / Redpanda', v: 'CDC', sub: t('systemJourney.pipeDurableLog') },
            { k: t('systemJourney.pipeConsumers'), v: t('systemJourney.pipeFanOut'), sub: 'learning · trajectory · projection · adaptation' },
            { k: t('systemJourney.pipeTrajectory'), v: fmt(pipe.stages.trajectory.rows_estimated), sub: t('systemJourney.pipeTrajectorySub') },
            { k: t('systemJourney.pipeProjections'), v: fmt(pipe.stages.projection.read_models), sub: t('systemJourney.pipeProjectionsSub') },
          ].map((n, i, arr) => (
            <div key={n.k} style={{ flex: '1 1 130px', position: 'relative', background: ui.color.subtle, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md, padding: ui.space.sm, minWidth: 120 }}>
              <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{n.k}</div>
              <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.heavy, color: ui.modelColor.hcie }}>{n.v}</div>
              <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, lineHeight: 1.3 }}>{n.sub}</div>
              {i < arr.length - 1 && <span style={{ position: 'absolute', right: -8, top: '40%', color: ui.color.muted, zIndex: 1 }} aria-hidden>→</span>}
            </div>
          ))}
        </div>
        <div style={{ marginTop: ui.space.md }}>
          <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: 4 }}>{t('systemJourney.eventsEmitted')}</div>
          {pipe.event_types.map((e: any) => (
            <div key={e.type} style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: 3 }}>
              <div style={{ width: 170, fontSize: ui.font.size.sm, color: ui.color.body }}>{e.type}</div>
              <div style={{ flex: 1, background: ui.color.grid, borderRadius: 3, height: 12 }}>
                <div style={{ width: `${Math.max(2, (e.count / evMax) * 100)}%`, height: '100%', borderRadius: 3, background: ui.tone.info.fg, transition: 'width .4s' }} />
              </div>
              <div style={{ width: 64, textAlign: 'right', fontSize: ui.font.size.sm, color: ui.color.ink, fontWeight: ui.font.weight.medium }}>{fmt(e.count)}</div>
            </div>
          ))}
        </div>
      </Panel>

      {/* system scale + governance */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: ui.space.md, marginBottom: ui.space.md }}>
        <Panel pad="lg">
          <Eyebrow>{t('systemJourney.scaleTitle')}</Eyebrow>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: ui.space.sm, marginTop: ui.space.xs }}>
            {[[t('systemJourney.scaleInteractions'), fmt(sys.interactions.total)], [t('systemJourney.scaleLearners'), fmt(sys.interactions.unique_users)], [t('systemJourney.scaleConcepts'), fmt(sys.interactions.unique_concepts)], [t('systemJourney.scaleAvgCorrect'), (sys.interactions.avg_correct ?? 0).toFixed(3)], [t('systemJourney.scaleTrajectoryRows'), fmt(sys.trajectories.total)], [t('systemJourney.scaleTaskCatalog'), fmt(sys.task_catalog.total)]].map(([k, v]) => (
              <div key={k as string}><div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.ink }}>{v}</div><div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{k}</div></div>
            ))}
          </div>
        </Panel>
        <Panel pad="lg">
          <Eyebrow>{t('systemJourney.governanceTitle')}</Eyebrow>
          <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: ui.space.xs }}>{t('systemJourney.governanceCaption')}</div>
          {adc.dimensions.slice(0, 5).map((d: any) => (
            <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: 4 }}>
              <div style={{ width: 90, fontSize: ui.font.size.sm, color: ui.color.body }}>{adcLabel(d)}</div>
              <div style={{ flex: 1, background: ui.color.grid, borderRadius: 3, height: 10 }}>
                <div style={{ width: `${Math.max(3, Math.min(100, (d.signal_ratio / 1.3) * 100))}%`, height: '100%', borderRadius: 3, background: d.status === 'ACTIVE' ? ui.tone.ok.fg : ui.color.muted }} />
              </div>
              <Tag tone={d.status === 'ACTIVE' ? 'ok' : 'neutral'}>{d.status}</Tag>
            </div>
          ))}
        </Panel>
      </div>

      {/* the containers */}
      <Panel pad="lg" style={{ marginBottom: ui.space.xl }}>
        <Eyebrow>{t('systemJourney.containersTitle')}</Eyebrow>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: ui.space.md, marginTop: ui.space.xs }}>
          {SERVICES.map(s => (
            <div key={s.g}>
              <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.tone.info.fg, marginBottom: 2 }}>{s.g}</div>
              {s.items.map(it => <div key={it} style={{ fontSize: ui.font.size.sm, color: ui.color.body }}>{it}</div>)}
            </div>
          ))}
        </div>
        <Callout tone="warn" style={{ marginTop: ui.space.md }} title={t('systemJourney.monitoringTitle')}>
          {t('systemJourney.monitoringBodyA')} <code>/v3</code> {t('systemJourney.monitoringBodyB')}{' '}
          <a href="/grafana/" target="_blank" rel="noreferrer" style={{ color: ui.tone.info.fg, fontWeight: ui.font.weight.bold }}>Grafana ↗</a>{' · '}
          <a href="/prometheus/" target="_blank" rel="noreferrer" style={{ color: ui.tone.info.fg, fontWeight: ui.font.weight.bold }}>Prometheus ↗</a>{' · '}
          <a href="/kafka-ui/" target="_blank" rel="noreferrer" style={{ color: ui.tone.info.fg, fontWeight: ui.font.weight.bold }}>Kafka-UI ↗</a>.{' '}
          {t('systemJourney.monitoringBodyC')}
        </Callout>
      </Panel>

      {/* ACT 3 — be the researcher */}
      <Eyebrow color={ui.tone.accent.fg}>{t('systemJourney.act3Eyebrow')}</Eyebrow>
      <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, marginBottom: ui.space.sm, maxWidth: 800 }}>
        {t('systemJourney.act3Intro')}
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: ui.space.sm, marginBottom: ui.space.xl }}>
        {[
          { href: '/review/run-it-yourself', t: t('systemJourney.cardLoopTitle'), b: t('systemJourney.cardLoopBody') },
          { href: '/dashboard/benchmarks', t: t('systemJourney.cardResultTitle'), b: t('systemJourney.cardResultBody') },
          { href: '/dashboard/governance', t: t('systemJourney.cardGovernanceTitle'), b: t('systemJourney.cardGovernanceBody') },
          { href: '/dashboard/reproducibility', t: t('systemJourney.cardReproTitle'), b: t('systemJourney.cardReproBody') },
          { href: '/learn', t: t('systemJourney.cardTrajectoryTitle'), b: t('systemJourney.cardTrajectoryBody') },
        ].map(c => (
          <Link key={c.href} href={c.href} style={{ textDecoration: 'none' }}>
            <div style={{ background: ui.color.surface, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md, padding: ui.space.md, height: '100%', cursor: 'pointer' }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ui.tone.info.border }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ui.color.line }}>
              <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{c.t}</div>
              <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, marginTop: 2, lineHeight: 1.4 }}>{c.b}</div>
            </div>
          </Link>
        ))}
      </div>

      <Callout tone="info" title={t('systemJourney.summaryTitle')}>
        {t('systemJourney.summaryBody')}
      </Callout>
    </div>
  )
}
