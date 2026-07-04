'use client'

/**
 * /review/cross-dataset — scrub dataset × window, watch HCIE m_K vs every baseline rebuild.
 *
 * Canonical lagged-Kalman m_K (predict-before-observe, tie-aware), all 6 datasets, per window. Also shows
 * the DEPLOYED 2-learner readout so the reviewer sees the flip (deck/CSEDM 0.673→0.605). Static data
 * (src/data/coldstart_mK_all_datasets.json), computed by tier_coldstart_mK_statics_assist2009.py and
 * validated CSEDM-exact against cross_dataset_mK_unified.json. Honest: HCIE is competitive, rarely leads-all.
 */

import Link from 'next/link'
import { useState } from 'react'
import data from '@/data/coldstart_mK_all_datasets.json'
import { Panel, Callout, Eyebrow, Tag } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'

const DS = data.datasets as Record<string, any>
const DS_KEYS = Object.keys(DS)
const WINS = ['<=5', '<=10', '<=20', 'overall'] as const
// window label i18n keys (resolved at render via t())
const WLABEL_KEY: Record<string, string> = { '<=5': 'winFirst5', '<=10': 'winFirst10', '<=20': 'winFirst20', overall: 'winOverall' }
// baselines to display (floor refs random/static_prior/greedy omitted from the bars).
// label is a t()-key resolved at render; HCIE label has a literal m_K kept verbatim.
const MODELS = [
  { k: 'HCIE_mK', labelKey: 'modelHcie', color: ui.modelColor.hcie, hero: true },
  { k: 'bkt', labelKey: 'modelBkt', color: ui.modelColor.bkt },
  { k: 'dkt', labelKey: 'modelDkt', color: ui.modelColor.dkt },
  { k: 'sakt', labelKey: 'modelSakt', color: ui.modelColor.sakt },
  { k: 'irt_1pl', labelKey: 'modelIrt', color: ui.modelColor.gkt },
]
const bar = (a: number) => Math.max(2, Math.min(100, ((a - 0.5) / 0.35) * 100))

export default function CrossDataset() {
  const t = useT()
  const [ds, setDs] = useState(DS_KEYS[0])
  const [w, setW] = useState<string>('<=5')
  const wlabel = (k: string) => t(`crossDataset.${WLABEL_KEY[k]}`)
  const row = DS[ds].windows[w] as Record<string, number | boolean>
  const rows = MODELS.map(m => ({ ...m, label: t(`crossDataset.${m.labelKey}`), auc: typeof row[m.k] === 'number' ? (row[m.k] as number) : null }))
    .filter(r => r.auc != null).sort((a, b) => (b.auc as number) - (a.auc as number))
  const mk = row.HCIE_mK as number
  const deployed = row.HCIE_deployed_2learner as number
  const baselines = rows.filter(r => !r.hero).map(r => r.auc as number)
  const best = Math.max(...baselines)
  const verdict = mk > best ? { t: t('crossDataset.verdictLeadsAll'), tone: 'ok' as const }
    : mk >= best - 0.015 ? { t: t('crossDataset.verdictCompetitive'), tone: 'info' as const }
    : { t: `${t('crossDataset.verdictTrails')} (${t('crossDataset.verdictBest')} ${best.toFixed(3)})`, tone: 'warn' as const }
  const flip = Math.abs(mk - deployed) >= 0.02

  return (
    <div style={{ padding: '40px 48px', maxWidth: 920 }}>
      <Eyebrow color={ui.tone.info.fg}>{t('crossDataset.eyebrow')}</Eyebrow>
      <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, lineHeight: 1.25, marginBottom: ui.space.md }}>
        {t('crossDataset.heroTitle')}
      </h1>
      <p style={{ fontSize: ui.font.size.lg, color: ui.color.body, lineHeight: 1.6, maxWidth: 780, marginBottom: ui.space.lg }}>
        {t('crossDataset.introA')} <strong>{t('crossDataset.introKalmanAlone')}</strong> {t('crossDataset.introB')} <strong>{t('crossDataset.introCompetitive')}</strong>{t('crossDataset.introC')}
      </p>

      {/* dataset + window pickers */}
      <div style={{ display: 'flex', gap: ui.space.xs, flexWrap: 'wrap', marginBottom: ui.space.sm }}>
        {DS_KEYS.map(k => {
          const on = k === ds
          return <button key={k} onClick={() => setDs(k)} style={{ fontSize: ui.font.size.md, padding: '6px 14px', borderRadius: ui.radius.md, cursor: 'pointer', border: `1px solid ${on ? ui.tone.info.border : ui.color.line}`, background: on ? ui.tone.info.bg : ui.color.surface, color: on ? ui.tone.info.fg : ui.color.muted, fontWeight: on ? ui.font.weight.bold : ui.font.weight.medium }}>{k}</button>
        })}
      </div>
      <div style={{ display: 'flex', gap: ui.space.xs, flexWrap: 'wrap', marginBottom: ui.space.lg }}>
        {WINS.map(k => {
          const on = k === w
          return <button key={k} onClick={() => setW(k)} style={{ fontSize: ui.font.size.sm, padding: '4px 12px', borderRadius: ui.radius.md, cursor: 'pointer', border: `1px solid ${on ? ui.tone.accent.border : ui.color.line}`, background: on ? ui.tone.accent.bg : ui.color.surface, color: on ? ui.tone.accent.fg : ui.color.muted, fontWeight: on ? ui.font.weight.bold : ui.font.weight.medium }}>{wlabel(k)}</button>
        })}
      </div>

      {/* bars */}
      <Panel pad="xl" style={{ marginBottom: ui.space.md }}>
        {rows.map(r => {
          const v = r.auc as number
          return (
            <div key={r.k} style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.sm }}>
              <div style={{ width: 120, fontSize: ui.font.size.md, color: r.hero ? ui.color.ink : ui.color.muted, fontWeight: r.hero ? ui.font.weight.bold : ui.font.weight.medium }}>{r.label}</div>
              <div style={{ flex: 1, background: ui.color.grid, borderRadius: ui.radius.sm, height: r.hero ? 22 : 16 }}>
                <div style={{ width: `${bar(v)}%`, height: '100%', borderRadius: ui.radius.sm, background: r.color, transition: 'width .35s' }} />
              </div>
              <div style={{ width: 48, textAlign: 'right', fontSize: ui.font.size.md, fontWeight: r.hero ? ui.font.weight.heavy : ui.font.weight.medium, color: r.hero ? ui.modelColor.hcie : ui.color.body }}>{v.toFixed(3)}</div>
            </div>
          )
        })}
        <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, marginTop: ui.space.xs }}>{t('crossDataset.coinFlipNote')} {DS[ds].run?.slice(0, 16)} · n={DS[ds].n_traj} · {t('crossDataset.baseRate')} {DS[ds].base_rate}.</div>
      </Panel>

      <Callout tone={verdict.tone} style={{ marginBottom: ui.space.sm }} title={`${ds} · ${wlabel(w)}: HCIE m_K ${mk.toFixed(3)} — ${verdict.t}`}>
        {verdict.tone === 'ok' ? t('crossDataset.calloutOk')
          : verdict.tone === 'info' ? t('crossDataset.calloutInfo')
          : t('crossDataset.calloutWarn')}
      </Callout>

      {flip && (
        <Callout tone="warn" style={{ marginBottom: ui.space.lg }} title={t('crossDataset.flipTitle')}>
          {t('crossDataset.flipA')} <strong>{t('crossDataset.flipDeployed')}</strong> {t('crossDataset.flipB')} <strong>{deployed.toFixed(3)}</strong> {t('crossDataset.flipVs')} <strong>{mk.toFixed(3)}</strong>.
          {' '}{t('crossDataset.flipC')}
        </Callout>
      )}

      <Callout tone="neutral" title={t('crossDataset.reproTitle')}>
        {t('crossDataset.reproBody')}
      </Callout>

      <div style={{ marginTop: ui.space.lg, display: 'flex', gap: ui.space.sm, flexWrap: 'wrap' }}>
        {[['/review/run-it-yourself', t('crossDataset.linkRunLoop')], ['/review/system-journey', t('crossDataset.linkLiveSystem')], ['/dashboard/benchmarks', t('crossDataset.linkFullBenchmark')]].map(([h, label]) => (
          <Link key={h} href={h} style={{ textDecoration: 'none' }}><span style={{ fontSize: ui.font.size.md, color: ui.tone.info.fg, fontWeight: ui.font.weight.medium }}>{label} →</span></Link>
        ))}
      </div>
    </div>
  )
}
