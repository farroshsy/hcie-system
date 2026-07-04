'use client'

import { useState } from 'react'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

const C = {
  bg:     '#F8FAFC',
  card:   '#FFFFFF',
  border: '#E2E8F0',
  text:   '#1E293B',
  sub:    '#64748B',
  blue:   '#3B82F6',
  blueD:  '#1D4ED8',
  green:  '#10B981',
  yellow: '#F59E0B',
  red:    '#EF4444',
  purple: '#8B5CF6',
  cyan:   '#06B6D4',
  orange: '#F97316',
  navy:   '#0F172A',
  navyC:  '#1E293B',
}

// ─── Primitives ────────────────────────────────────────────────────────────

function Badge({ color, label }: { color: string; label: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 10,
      fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
      background: color + '20', color, border: `1px solid ${color}40`,
    }}>{label}</span>
  )
}

function SectionHeader({ n, title, sub }: { n: string; title: string; sub: string }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <span style={{
          width: 32, height: 32, borderRadius: '50%', background: C.blue, color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 800, fontSize: 13, flexShrink: 0,
        }}>{n}</span>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: C.text, margin: 0 }}>{title}</h2>
      </div>
      <p style={{ margin: '0 0 0 44px', color: C.sub, fontSize: 15, lineHeight: 1.6 }}>{sub}</p>
    </div>
  )
}

function Callout({ icon, color, title, body }: { icon: string; color: string; title: string; body: string }) {
  return (
    <div style={{
      background: color + '08', border: `1px solid ${color}30`,
      borderLeft: `4px solid ${color}`, borderRadius: 8, padding: '14px 18px', marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span style={{ fontWeight: 700, color, fontSize: 14 }}>{title}</span>
      </div>
      <p style={{ margin: 0, color: C.text, fontSize: 14, lineHeight: 1.7 }}>{body}</p>
    </div>
  )
}

function Code({ title, lang, code }: { title: string; lang: string; code: string }) {
  return (
    <div style={{ marginBottom: 16, borderRadius: 8, overflow: 'hidden', border: `1px solid ${C.border}` }}>
      <div style={{
        background: C.navyC, padding: '8px 14px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ color: '#94A3B8', fontSize: 12, fontWeight: 600 }}>{title}</span>
        <Badge color={C.cyan} label={lang} />
      </div>
      <pre style={{
        margin: 0, padding: '14px 16px', background: C.navy,
        color: '#E2E8F0', fontSize: 12.5, lineHeight: 1.65,
        overflowX: 'auto', fontFamily: 'monospace',
      }}>{code.trim()}</pre>
    </div>
  )
}

// ─── Verdict chip ──────────────────────────────────────────────────────────

const VERDICT_COLORS: Record<string, string> = {
  INFORMATIVE:    C.green,
  FLOOR_NOISE:    C.red,
  NEAR_CONSTANT:  C.yellow,
  CONDITIONAL:    C.purple,
  REDUNDANT:      C.orange,
  UNMEASURED:     C.sub,
}
function Verdict({ v }: { v: string }) {
  return <Badge color={VERDICT_COLORS[v] ?? C.sub} label={v} />
}

// ─── BKT parameter card ────────────────────────────────────────────────────
// Display-text fields hold t()-keys (resolved at render); structural fields
// (sym, color, verdict enum) stay literal.

interface BktParam {
  sym: string
  nameKey: string
  meaningKey: string
  floorKey: string
  adcVerdict: string
  adcReasonKey: string
  topologyKey: string
  alerts: { conditionKey: string; signalKey: string; whyKey: string; color: string }[]
}

function BktParamCard({ p, open, onToggle, t }: { p: BktParam; open: boolean; onToggle: () => void; t: (k: string) => string }) {
  const color = VERDICT_COLORS[p.adcVerdict] ?? C.blue
  return (
    <div style={{
      background: C.card, border: `1px solid ${C.border}`,
      borderLeft: `4px solid ${color}`, borderRadius: 10, marginBottom: 16,
      overflow: 'hidden',
    }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%', background: 'none', border: 'none', cursor: 'pointer',
          padding: '16px 20px', display: 'flex', alignItems: 'flex-start', gap: 16,
          textAlign: 'left',
        }}
      >
        <div style={{
          flexShrink: 0, width: 48, height: 48, borderRadius: 10,
          background: color + '15', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontFamily: 'monospace', fontWeight: 900,
          fontSize: 14, color,
        }}>{p.sym}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 4 }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>{t(p.nameKey)}</span>
            <Verdict v={p.adcVerdict} />
          </div>
          <p style={{ margin: 0, fontSize: 13, color: C.sub, lineHeight: 1.5 }}>{t(p.meaningKey)}</p>
        </div>
        <span style={{ color: C.sub, fontSize: 18, flexShrink: 0 }}>{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div style={{ padding: '0 20px 20px', borderTop: `1px solid ${C.border}` }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginTop: 16, marginBottom: 20 }}>
            <div style={{ background: C.red + '08', borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.red, marginBottom: 4 }}>{t('adcGeneral.labelStructuralFloor')}</div>
              <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(p.floorKey)}</p>
            </div>
            <div style={{ background: color + '08', borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color, marginBottom: 4 }}>{t('adcGeneral.labelWhyVerdict')}</div>
              <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(p.adcReasonKey)}</p>
            </div>
            <div style={{ background: C.purple + '08', borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.purple, marginBottom: 4 }}>{t('adcGeneral.labelTopologyDependency')}</div>
              <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(p.topologyKey)}</p>
            </div>
          </div>

          <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, letterSpacing: '0.08em', marginBottom: 10 }}>
            {t('adcGeneral.labelAdcAlertConditions')}
          </div>
          {p.alerts.map((a, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: 12,
              padding: '10px 14px', borderRadius: 8, marginBottom: 8,
              background: a.color + '08', border: `1px solid ${a.color}20`,
            }}>
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: a.color, marginBottom: 2 }}>{t('adcGeneral.labelCondition')}</div>
                <div style={{ fontSize: 12, color: C.text, fontWeight: 600 }}>{t(a.conditionKey)}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: a.color, marginBottom: 2 }}>{t('adcGeneral.labelAlertSignal')}</div>
                <div style={{ fontSize: 12, color: C.text, fontFamily: 'monospace' }}>{t(a.signalKey)}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: C.sub, marginBottom: 2 }}>{t('adcGeneral.labelWhyItMatters')}</div>
                <div style={{ fontSize: 12, color: C.sub, lineHeight: 1.5 }}>{t(a.whyKey)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── BKT parameter data (text via t()-keys) ─────────────────────────────────

const BKT_PARAMS: BktParam[] = [
  {
    sym: 'P(L₀)',
    nameKey: 'adcGeneral.bktL0Name',
    meaningKey: 'adcGeneral.bktL0Meaning',
    floorKey: 'adcGeneral.bktL0Floor',
    adcVerdict: 'CONDITIONAL',
    adcReasonKey: 'adcGeneral.bktL0Reason',
    topologyKey: 'adcGeneral.bktL0Topology',
    alerts: [
      { conditionKey: 'adcGeneral.bktL0A1Cond', signalKey: 'adcGeneral.bktL0A1Sig', whyKey: 'adcGeneral.bktL0A1Why', color: C.yellow },
      { conditionKey: 'adcGeneral.bktL0A2Cond', signalKey: 'adcGeneral.bktL0A2Sig', whyKey: 'adcGeneral.bktL0A2Why', color: C.purple },
      { conditionKey: 'adcGeneral.bktL0A3Cond', signalKey: 'adcGeneral.bktL0A3Sig', whyKey: 'adcGeneral.bktL0A3Why', color: C.red },
    ],
  },
  {
    sym: 'P(T)',
    nameKey: 'adcGeneral.bktTName',
    meaningKey: 'adcGeneral.bktTMeaning',
    floorKey: 'adcGeneral.bktTFloor',
    adcVerdict: 'CONDITIONAL',
    adcReasonKey: 'adcGeneral.bktTReason',
    topologyKey: 'adcGeneral.bktTTopology',
    alerts: [
      { conditionKey: 'adcGeneral.bktTA1Cond', signalKey: 'adcGeneral.bktTA1Sig', whyKey: 'adcGeneral.bktTA1Why', color: C.yellow },
      { conditionKey: 'adcGeneral.bktTA2Cond', signalKey: 'adcGeneral.bktTA2Sig', whyKey: 'adcGeneral.bktTA2Why', color: C.purple },
      { conditionKey: 'adcGeneral.bktTA3Cond', signalKey: 'adcGeneral.bktTA3Sig', whyKey: 'adcGeneral.bktTA3Why', color: C.red },
      { conditionKey: 'adcGeneral.bktTA4Cond', signalKey: 'adcGeneral.bktTA4Sig', whyKey: 'adcGeneral.bktTA4Why', color: C.orange },
    ],
  },
  {
    sym: 'P(G)',
    nameKey: 'adcGeneral.bktGName',
    meaningKey: 'adcGeneral.bktGMeaning',
    floorKey: 'adcGeneral.bktGFloor',
    adcVerdict: 'FLOOR_NOISE',
    adcReasonKey: 'adcGeneral.bktGReason',
    topologyKey: 'adcGeneral.bktGTopology',
    alerts: [
      { conditionKey: 'adcGeneral.bktGA1Cond', signalKey: 'adcGeneral.bktGA1Sig', whyKey: 'adcGeneral.bktGA1Why', color: C.red },
      { conditionKey: 'adcGeneral.bktGA2Cond', signalKey: 'adcGeneral.bktGA2Sig', whyKey: 'adcGeneral.bktGA2Why', color: C.red },
      { conditionKey: 'adcGeneral.bktGA3Cond', signalKey: 'adcGeneral.bktGA3Sig', whyKey: 'adcGeneral.bktGA3Why', color: C.red },
    ],
  },
  {
    sym: 'P(S)',
    nameKey: 'adcGeneral.bktSName',
    meaningKey: 'adcGeneral.bktSMeaning',
    floorKey: 'adcGeneral.bktSFloor',
    adcVerdict: 'NEAR_CONSTANT',
    adcReasonKey: 'adcGeneral.bktSReason',
    topologyKey: 'adcGeneral.bktSTopology',
    alerts: [
      { conditionKey: 'adcGeneral.bktSA1Cond', signalKey: 'adcGeneral.bktSA1Sig', whyKey: 'adcGeneral.bktSA1Why', color: C.yellow },
      { conditionKey: 'adcGeneral.bktSA2Cond', signalKey: 'adcGeneral.bktSA2Sig', whyKey: 'adcGeneral.bktSA2Why', color: C.orange },
      { conditionKey: 'adcGeneral.bktSA3Cond', signalKey: 'adcGeneral.bktSA3Sig', whyKey: 'adcGeneral.bktSA3Why', color: C.purple },
    ],
  },
]

// ─── Topology conditional matrix (text via t()-keys) ────────────────────────

const TOPO_MATRIX = [
  {
    topo: 'Chain', icon: '→→→', color: C.blue,
    topoKey: 'adcGeneral.topoChainName',
    descKey: 'adcGeneral.topoChainDesc',
    bkt: { L0: 'adcGeneral.topoChainL0', T: 'adcGeneral.topoChainT', G: 'adcGeneral.topoChainG', S: 'adcGeneral.topoChainS' },
    alertKey: 'adcGeneral.topoChainAlert',
    adcSignal: 'TOPOLOGY_BLIND',
    adcColor: C.purple,
  },
  {
    topo: 'Diamond', icon: '◇', color: C.purple,
    topoKey: 'adcGeneral.topoDiamondName',
    descKey: 'adcGeneral.topoDiamondDesc',
    bkt: { L0: 'adcGeneral.topoDiamondL0', T: 'adcGeneral.topoDiamondT', G: 'adcGeneral.topoDiamondG', S: 'adcGeneral.topoDiamondS' },
    alertKey: 'adcGeneral.topoDiamondAlert',
    adcSignal: 'TRANSFER_MISSING',
    adcColor: C.cyan,
  },
  {
    topo: 'Fan-out', icon: '⊸', color: C.orange,
    topoKey: 'adcGeneral.topoFanoutName',
    descKey: 'adcGeneral.topoFanoutDesc',
    bkt: { L0: 'adcGeneral.topoFanoutL0', T: 'adcGeneral.topoFanoutT', G: 'adcGeneral.topoFanoutG', S: 'adcGeneral.topoFanoutS' },
    alertKey: 'adcGeneral.topoFanoutAlert',
    adcSignal: 'FOUNDATION_ANOMALY',
    adcColor: C.orange,
  },
  {
    topo: 'Island', icon: '○', color: C.green,
    topoKey: 'adcGeneral.topoIslandName',
    descKey: 'adcGeneral.topoIslandDesc',
    bkt: { L0: 'adcGeneral.topoIslandL0', T: 'adcGeneral.topoIslandT', G: 'adcGeneral.topoIslandG', S: 'adcGeneral.topoIslandS' },
    alertKey: 'adcGeneral.topoIslandAlert',
    adcSignal: 'ISOLATION_ANOMALY',
    adcColor: C.green,
  },
  {
    topo: 'Mesh', icon: '⊞', color: C.red,
    topoKey: 'adcGeneral.topoMeshName',
    descKey: 'adcGeneral.topoMeshDesc',
    bkt: { L0: 'adcGeneral.topoMeshL0', T: 'adcGeneral.topoMeshT', G: 'adcGeneral.topoMeshG', S: 'adcGeneral.topoMeshS' },
    alertKey: 'adcGeneral.topoMeshAlert',
    adcSignal: 'MESH_INTERFERENCE',
    adcColor: C.red,
  },
]

// ─── Generalization to other models (text via t()-keys) ─────────────────────

const MODEL_SIGNALS = [
  {
    model: 'BKT (HMM)',
    color: C.blue,
    dims: ['P(L₀)', 'P(T)', 'P(G)', 'P(S)'],
    floorKey: 'adcGeneral.modelBktFloor',
    nearConstKey: 'adcGeneral.modelBktNearConst',
    topoKey: 'adcGeneral.modelBktTopo',
    redundancyKey: 'adcGeneral.modelBktRedundancy',
    adcValueKey: 'adcGeneral.modelBktValue',
  },
  {
    model: 'DKT (LSTM)',
    color: C.purple,
    dims: ['hidden state h_t', 'output σ(Wh_t)', 'gradient norms', 'attention (if any)'],
    floorKey: 'adcGeneral.modelDktFloor',
    nearConstKey: 'adcGeneral.modelDktNearConst',
    topoKey: 'adcGeneral.modelDktTopo',
    redundancyKey: 'adcGeneral.modelDktRedundancy',
    adcValueKey: 'adcGeneral.modelDktValue',
  },
  {
    model: 'SAKT (Attention)',
    color: C.green,
    dims: ['attention weights α_ij', 'key similarity scores', 'position embeddings'],
    floorKey: 'adcGeneral.modelSaktFloor',
    nearConstKey: 'adcGeneral.modelSaktNearConst',
    topoKey: 'adcGeneral.modelSaktTopo',
    redundancyKey: 'adcGeneral.modelSaktRedundancy',
    adcValueKey: 'adcGeneral.modelSaktValue',
  },
  {
    model: 'GKT (Graph)',
    color: C.orange,
    dims: ['node embeddings h_k^(l)', 'edge weights w_ij', 'aggregation scalars', 'readout logits'],
    floorKey: 'adcGeneral.modelGktFloor',
    nearConstKey: 'adcGeneral.modelGktNearConst',
    topoKey: 'adcGeneral.modelGktTopo',
    redundancyKey: 'adcGeneral.modelGktRedundancy',
    adcValueKey: 'adcGeneral.modelGktValue',
  },
  {
    model: 'HCIE (JT Engine)',
    color: C.red,
    dims: ['ΔM', 'T_realized', 'T_prospective', 'Challenge', 'Uncertainty', 'ZPD'],
    floorKey: 'adcGeneral.modelHcieFloor',
    nearConstKey: 'adcGeneral.modelHcieNearConst',
    topoKey: 'adcGeneral.modelHcieTopo',
    redundancyKey: 'adcGeneral.modelHcieRedundancy',
    adcValueKey: 'adcGeneral.modelHcieValue',
  },
]

// ─── Main page ─────────────────────────────────────────────────────────────

export default function AdcGeneralPage() {
  const t = useT()
  const [openParam, setOpenParam] = useState<string | null>('P(L₀)')
  const [activeModel, setActiveModel] = useState('BKT (HMM)')
  const [activeTopoRow, setActiveTopoRow] = useState<string | null>(null)

  const sel = MODEL_SIGNALS.find(m => m.model === activeModel)!

  return (
    <div style={{ padding: '36px 40px 80px', maxWidth: 1100, margin: '0 auto' }}>

      {/* Hero */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
          <Badge color={C.purple} label={t('adcGeneral.heroBadgeGeneralized')} />
          <Badge color={C.blue}   label={t('adcGeneral.heroBadgeBktDeepDive')} />
          <Badge color={C.green}  label={t('adcGeneral.heroBadgeTopologyConditional')} />
          <Badge color={C.orange} label={t('adcGeneral.heroBadgeCrossModel')} />
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 900, color: C.text, margin: '0 0 12px', lineHeight: 1.2 }}>
          {t('adcGeneral.heroTitle')}
        </h1>
        <p style={{ fontSize: 16, color: C.sub, lineHeight: 1.7, maxWidth: 740, margin: 0 }}>
          {t('adcGeneral.heroIntroA')}{' '}
          <strong>{t('adcGeneral.heroIntroAnyKt')}</strong>: <em>{t('adcGeneral.heroIntroQuestion')}</em> {t('adcGeneral.heroIntroB')}
        </p>
      </div>

      {/* ── SECTION 1: ADC CORE PRINCIPLE ──────────────────────────── */}
      <div id="principle" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="1"
          title={t('adcGeneral.sec1Title')}
          sub={t('adcGeneral.sec1Sub')}
        />

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 24 }}>
          <div style={{ flex: 2, minWidth: 280 }}>
            <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8, marginTop: 0 }}>
              {t('adcGeneral.sec1P1a')} <strong>{t('adcGeneral.sec1P1Strong')}</strong> {t('adcGeneral.sec1P1b')}
            </p>
            <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8 }}>
              {t('adcGeneral.sec1P2')}
            </p>
            <div style={{
              fontFamily: 'monospace', fontSize: 13, background: C.navy,
              color: '#E2E8F0', borderRadius: 8, padding: '16px 20px', marginBottom: 16,
            }}>
              <span style={{ color: '#94A3B8' }}>{'// ADC classification (applies to ANY model)'}</span>
              <br /><br />
              {'μ = mean(signal_dimension)'}
              <br />
              {'σ = std(signal_dimension)'}
              <br /><br />
              {'if μ ≤ α_floor:          → FLOOR_NOISE'}
              <br />
              {'elif σ/μ < signal_ratio: → NEAR_CONSTANT'}
              <br />
              {'else:                    → INFORMATIVE'}
            </div>
            <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8 }}>
              {t('adcGeneral.sec1P3a')} <strong>{t('adcGeneral.sec1P3Strong')}</strong> {t('adcGeneral.sec1P3b')}
            </p>
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 18, marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, marginBottom: 12 }}>{t('adcGeneral.verdict3Types')}</div>
              {[
                { v: 'INFORMATIVE',   d: t('adcGeneral.verdictInformativeDesc'), c: C.green },
                { v: 'NEAR_CONSTANT', d: t('adcGeneral.verdictNearConstantDesc'), c: C.yellow },
                { v: 'FLOOR_NOISE',   d: t('adcGeneral.verdictFloorNoiseDesc'), c: C.red },
              ].map(({ v, d, c }) => (
                <div key={v} style={{ marginBottom: 12 }}>
                  <Badge color={c} label={v} />
                  <p style={{ margin: '6px 0 0', fontSize: 12, color: C.sub, lineHeight: 1.5 }}>{d}</p>
                </div>
              ))}
            </div>

            <Callout
              icon="🔑"
              color={C.purple}
              title={t('adcGeneral.calloutGeneralizableTitle')}
              body={t('adcGeneral.calloutGeneralizableBody')}
            />
          </div>
        </div>

        <Callout
          icon="⚠️"
          color={C.orange}
          title={t('adcGeneral.calloutHardToSeeTitle')}
          body={t('adcGeneral.calloutHardToSeeBody')}
        />
      </div>

      {/* ── SECTION 2: BKT PARAMETER-BY-PARAMETER ──────────────────── */}
      <div id="bkt" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="2"
          title={t('adcGeneral.sec2Title')}
          sub={t('adcGeneral.sec2Sub')}
        />

        <Callout
          icon="📐"
          color={C.blue}
          title={t('adcGeneral.calloutBktRecapTitle')}
          body={t('adcGeneral.calloutBktRecapBody')}
        />

        <div style={{ marginBottom: 8 }}>
          {BKT_PARAMS.map(p => (
            <BktParamCard
              key={p.sym}
              p={p}
              t={t}
              open={openParam === p.sym}
              onToggle={() => setOpenParam(openParam === p.sym ? null : p.sym)}
            />
          ))}
        </div>

        <Code
          title={t('adcGeneral.codeBktWrapperTitle')}
          lang="Python"
          code={`
class ADCForBKT:
    """Wraps any BKT implementation. Classifies 4 parameters per KC."""

    α_floor_prior = 0.01   # P(L₀), P(T): positive probability space
    α_floor_noise = 0.001  # P(G), P(S): bounded by HMM identifiability
    signal_ratio   = 0.08  # std/mean threshold

    def classify(self, bkt_params: dict[str, dict]) -> dict:
        # bkt_params: {kc_id: {L0, T, G, S}} for all KCs
        verdicts = {}
        for dim in ['L0', 'T', 'G', 'S']:
            vals = [bkt_params[kc][dim] for kc in bkt_params]
            μ, σ = np.mean(vals), np.std(vals)
            floor = self.α_floor_prior if dim in ['L0','T'] else self.α_floor_noise

            if μ <= floor:
                verdicts[dim] = 'FLOOR_NOISE'
            elif σ / max(μ, 1e-9) < self.signal_ratio:
                verdicts[dim] = 'NEAR_CONSTANT'
            else:
                verdicts[dim] = 'INFORMATIVE'

        # Extra gate: BKT degeneracy check
        G_vals = [bkt_params[kc]['G'] for kc in bkt_params]
        S_vals = [bkt_params[kc]['S'] for kc in bkt_params]
        if np.corrcoef(G_vals, S_vals)[0,1] > 0.7:
            verdicts['_alert'] = 'REDUNDANT: P(G) corr(P(S))>0.7 — consider 1-param noise model'

        return verdicts
`}
        />
      </div>

      {/* ── SECTION 3: TOPOLOGY-CONDITIONAL ALERTS ─────────────────── */}
      <div id="topology" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="3"
          title={t('adcGeneral.sec3Title')}
          sub={t('adcGeneral.sec3Sub')}
        />

        <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8, marginBottom: 20 }}>
          {t('adcGeneral.sec3P1a')} <em>{t('adcGeneral.sec3P1Em1')}</em> {t('adcGeneral.sec3P1b')} <em>{t('adcGeneral.sec3P1Em2')}</em>{t('adcGeneral.sec3P1c')}
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {TOPO_MATRIX.map(row => (
            <div key={row.topo} style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderLeft: `4px solid ${row.color}`, borderRadius: 10,
              overflow: 'hidden',
            }}>
              <button
                onClick={() => setActiveTopoRow(activeTopoRow === row.topo ? null : row.topo)}
                style={{
                  width: '100%', background: 'none', border: 'none', cursor: 'pointer',
                  padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 14, textAlign: 'left',
                }}
              >
                <span style={{
                  fontSize: 22, width: 40, height: 40, borderRadius: 8,
                  background: row.color + '15', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                }}>{row.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>{t(row.topoKey)}</span>
                    <Badge color={row.adcColor} label={row.adcSignal} />
                  </div>
                  <span style={{ fontSize: 13, color: C.sub }}>{t(row.descKey)}</span>
                </div>
                <span style={{ color: C.sub, fontSize: 18 }}>{activeTopoRow === row.topo ? '▲' : '▼'}</span>
              </button>

              {activeTopoRow === row.topo && (
                <div style={{ padding: '0 20px 20px', borderTop: `1px solid ${C.border}` }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, margin: '16px 0' }}>
                    {(['L0','T','G','S'] as const).map(dim => {
                      const val = t(row.bkt[dim as 'L0'|'T'|'G'|'S'])
                      const sym = { L0: 'P(L₀)', T: 'P(T)', G: 'P(G)', S: 'P(S)' }[dim]
                      return (
                        <div key={dim} style={{
                          background: row.color + '06', borderRadius: 8, padding: '10px 14px',
                          border: `1px solid ${row.color}20`,
                        }}>
                          <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 13, color: row.color, marginBottom: 4 }}>{sym}</div>
                          <p style={{ margin: 0, fontSize: 12, color: C.sub, lineHeight: 1.5 }}>{val}</p>
                        </div>
                      )
                    })}
                  </div>
                  <div style={{
                    background: row.adcColor + '10', border: `1px solid ${row.adcColor}30`,
                    borderRadius: 8, padding: '12px 16px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <Badge color={row.adcColor} label={`${t('adcGeneral.labelAdcAlertPrefix')}: ${row.adcSignal}`} />
                    </div>
                    <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(row.alertKey)}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <Code
          title={t('adcGeneral.codeTopoCheckTitle')}
          lang="Python"
          code={`
def topology_conditional_check(
    bkt_params: dict,      # {kc_id: {L0, T, G, S}}
    kg: KnowledgeGraph,    # adjacency list
) -> list[Alert]:
    alerts = []
    for kc_id, params in bkt_params.items():
        topo_class = kg.classify_node(kc_id)
        # Chain: expect P(T) to increase with chain depth
        if topo_class == 'chain':
            depth = kg.chain_depth(kc_id)
            expected_T = baseline_T + depth * 0.02  # empirical gradient
            if abs(params['T'] - expected_T) > 0.05:
                alerts.append(Alert(
                    kc=kc_id, param='T',
                    type='TOPOLOGY_BLIND',
                    msg=f'P(T)={params["T"]:.3f} does not reflect chain depth={depth}',
                ))

        # Diamond: expect P(L0) elevated at convergence node
        elif topo_class == 'diamond_sink':
            prereq_mastery = np.mean([
                bkt_params[p]['L0'] for p in kg.predecessors(kc_id)
            ])
            if params['L0'] < prereq_mastery * 0.9:
                alerts.append(Alert(
                    kc=kc_id, param='L0',
                    type='TRANSFER_MISSING',
                    msg=f'P(L0)={params["L0"]:.3f} not elevated despite convergent prereqs',
                ))

        # Island: P(L0) should match global prior
        elif topo_class == 'island':
            global_prior = np.mean([p['L0'] for p in bkt_params.values()])
            if abs(params['L0'] - global_prior) > 0.15:
                alerts.append(Alert(
                    kc=kc_id, param='L0',
                    type='ISOLATION_ANOMALY',
                    msg=f'Island node P(L0)={params["L0"]:.3f} deviates from global prior={global_prior:.3f}',
                ))
    return alerts
`}
        />
      </div>

      {/* ── SECTION 4: EDGE CASES ───────────────────────────────────── */}
      <div id="edgecases" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="4"
          title={t('adcGeneral.sec4Title')}
          sub={t('adcGeneral.sec4Sub')}
        />

        {[
          {
            id: 'EC-1', color: C.red,
            titleKey: 'adcGeneral.ec1Title',
            scenarioKey: 'adcGeneral.ec1Scenario',
            problemKey: 'adcGeneral.ec1Problem',
            adcAlertKey: 'adcGeneral.ec1Alert',
          },
          {
            id: 'EC-2', color: C.orange,
            titleKey: 'adcGeneral.ec2Title',
            scenarioKey: 'adcGeneral.ec2Scenario',
            problemKey: 'adcGeneral.ec2Problem',
            adcAlertKey: 'adcGeneral.ec2Alert',
          },
          {
            id: 'EC-3', color: C.purple,
            titleKey: 'adcGeneral.ec3Title',
            scenarioKey: 'adcGeneral.ec3Scenario',
            problemKey: 'adcGeneral.ec3Problem',
            adcAlertKey: 'adcGeneral.ec3Alert',
          },
          {
            id: 'EC-4', color: C.yellow,
            titleKey: 'adcGeneral.ec4Title',
            scenarioKey: 'adcGeneral.ec4Scenario',
            problemKey: 'adcGeneral.ec4Problem',
            adcAlertKey: 'adcGeneral.ec4Alert',
          },
          {
            id: 'EC-5', color: C.cyan,
            titleKey: 'adcGeneral.ec5Title',
            scenarioKey: 'adcGeneral.ec5Scenario',
            problemKey: 'adcGeneral.ec5Problem',
            adcAlertKey: 'adcGeneral.ec5Alert',
          },
        ].map(ec => (
          <div key={ec.id} style={{
            background: C.card, border: `1px solid ${C.border}`,
            borderLeft: `4px solid ${ec.color}`, borderRadius: 10,
            padding: '20px 24px', marginBottom: 16,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <Badge color={ec.color} label={ec.id} />
              <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>{t(ec.titleKey)}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.sub, marginBottom: 6 }}>{t('adcGeneral.labelScenario')}</div>
                <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(ec.scenarioKey)}</p>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.red, marginBottom: 6 }}>{t('adcGeneral.labelSilentProblem')}</div>
                <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(ec.problemKey)}</p>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: ec.color, marginBottom: 6 }}>{t('adcGeneral.labelAdcAlertAction')}</div>
                <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(ec.adcAlertKey)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── SECTION 5: CROSS-MODEL COMPARISON ──────────────────────── */}
      <div id="crossmodel" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="5"
          title={t('adcGeneral.sec5Title')}
          sub={t('adcGeneral.sec5Sub')}
        />

        {/* Model tabs */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
          {MODEL_SIGNALS.map(m => (
            <button
              key={m.model}
              onClick={() => setActiveModel(m.model)}
              style={{
                padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
                fontWeight: 700, fontSize: 13,
                background: activeModel === m.model ? m.color : C.border,
                color: activeModel === m.model ? '#fff' : C.sub,
                transition: 'all 0.15s',
              }}
            >{m.model}</button>
          ))}
        </div>

        <div style={{
          background: C.card, border: `2px solid ${sel.color}`,
          borderRadius: 12, padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: C.text }}>{sel.model}</h3>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {sel.dims.map(d => (
                <code key={d} style={{
                  background: sel.color + '15', color: sel.color,
                  padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                }}>{d}</code>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
            {[
              { label: t('adcGeneral.labelFloorArtifact'), icon: '⬇', color: C.red, body: t(sel.floorKey) },
              { label: t('adcGeneral.labelNearConstantPattern'), icon: '≈', color: C.yellow, body: t(sel.nearConstKey) },
              { label: t('adcGeneral.labelTopologyInteraction'), icon: '◈', color: C.purple, body: t(sel.topoKey) },
              { label: t('adcGeneral.labelRedundancyRisk'), icon: '∥', color: C.orange, body: t(sel.redundancyKey) },
            ].map(({ label, icon, color, body }) => (
              <div key={label} style={{
                background: color + '08', border: `1px solid ${color}25`, borderRadius: 8, padding: '12px 14px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <span style={{ fontSize: 15 }}>{icon}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color, letterSpacing: '0.06em' }}>{label}</span>
                </div>
                <p style={{ margin: 0, fontSize: 12.5, color: C.text, lineHeight: 1.6 }}>{body}</p>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 16, background: sel.color + '10', border: `1px solid ${sel.color}30`,
            borderRadius: 8, padding: '12px 16px',
          }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: sel.color, marginBottom: 4 }}>{t('adcGeneral.labelAdcValueProp')}</div>
            <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.6 }}>{t(sel.adcValueKey)}</p>
          </div>
        </div>
      </div>

      {/* ── SECTION 6: IS ADC HCIE-ONLY? ────────────────────────────── */}
      <div id="generalize" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="6"
          title={t('adcGeneral.sec6Title')}
          sub={t('adcGeneral.sec6Sub')}
        />

        <Code
          title={t('adcGeneral.codeProtocolTitle')}
          lang="Python"
          code={`
from abc import ABC, abstractmethod

class ADCCompatible(ABC):
    """
    Any KT model implementing these 4 hooks can be governed by ADC.
    The governance logic (floor/near-constant/topology checks) is
    model-agnostic — only the hooks differ.
    """

    @abstractmethod
    def signal_dimensions(self) -> list[str]:
        """Return names of all output signal dimensions.
        BKT: ['L0','T','G','S']
        DKT: ['h_0','h_1',...,'h_127']   (hidden units)
        SAKT: ['attn_0','attn_1',...]     (attention heads)
        HCIE: ['delta_m','t_realized','challenge','uncertainty','zpd','t_prospective']
        """

    @abstractmethod
    def theoretical_floor(self, dim: str) -> float:
        """Return the structural minimum for this dimension.
        BKT P(G): 1/n_choices (item format floor)
        BKT P(T): 0.01 (HMM identifiability)
        DKT h_i:  0.007 (sigmoid(-5))
        HCIE:     sigmoid(-2.5)=0.076 for sigmoid-output dims
        """

    @abstractmethod
    def emit_signals(self, trajectories: list) -> dict[str, list[float]]:
        """Run the model and return per-dimension signal distributions.
        Output: {dim: [val_1, val_2, ..., val_N]} for N learner-concept pairs
        """

    @abstractmethod
    def topology_expected(self, dim: str, topo_class: str) -> tuple[float,float]:
        """Return (expected_mean, expected_std) for this dim × topology class.
        Used by topology-conditional alert check.
        Return (None, None) if this model has no topology structure.
        """

# ─── ADC governance engine (unchanged for all models) ───────────────

class ADC:
    signal_ratio = 0.08   # std/mean threshold

    def govern(self, model: ADCCompatible, trajectories: list, kg=None) -> Report:
        signals = model.emit_signals(trajectories)
        verdicts = {}
        for dim in model.signal_dimensions():
            vals = signals[dim]
            μ, σ = np.mean(vals), np.std(vals)
            floor = model.theoretical_floor(dim)
            if μ <= floor:
                verdicts[dim] = Verdict.FLOOR_NOISE
            elif σ / max(μ, 1e-9) < self.signal_ratio:
                verdicts[dim] = Verdict.NEAR_CONSTANT
            else:
                verdicts[dim] = Verdict.INFORMATIVE
        return Report(verdicts=verdicts)
`}
        />

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
          {[
            { titleKey: 'adcGeneral.implBktTitle', sub: '~2 hours', color: C.blue, bodyKey: 'adcGeneral.implBktBody' },
            { titleKey: 'adcGeneral.implDktTitle', sub: '~4 hours', color: C.purple, bodyKey: 'adcGeneral.implDktBody' },
            { titleKey: 'adcGeneral.implHcieTitle', sub: t('adcGeneral.implHcieSub'), color: C.red, bodyKey: 'adcGeneral.implHcieBody' },
          ].map(({ titleKey, sub, color, bodyKey }) => (
            <div key={titleKey} style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderTop: `3px solid ${color}`, borderRadius: 10, padding: '16px 18px',
            }}>
              <div style={{ fontWeight: 700, fontSize: 14, color: C.text, marginBottom: 2 }}>{t(titleKey)}</div>
              <Badge color={color} label={sub} />
              <p style={{ margin: '10px 0 0', fontSize: 13, color: C.sub, lineHeight: 1.6 }}>{t(bodyKey)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── SECTION 7: THE KEY INSIGHT ──────────────────────────────── */}
      <div id="insight" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="7"
          title={t('adcGeneral.sec7Title')}
          sub={t('adcGeneral.sec7Sub')}
        />

        <div style={{
          background: C.navy, borderRadius: 14, padding: 32, marginBottom: 24,
        }}>
          <p style={{ margin: '0 0 20px', color: '#E2E8F0', fontSize: 16, lineHeight: 1.8, fontStyle: 'italic' }}>
            {t('adcGeneral.insightQuote')}
          </p>
          <p style={{ margin: '0 0 16px', color: '#94A3B8', fontSize: 14, lineHeight: 1.7 }}>
            {t('adcGeneral.insightP1a')} <strong style={{ color: '#F1F5F9' }}>{t('adcGeneral.insightP1Strong')}</strong>{t('adcGeneral.insightP1b')}
          </p>
          <p style={{ margin: '0 0 16px', color: '#94A3B8', fontSize: 14, lineHeight: 1.7 }}>
            {t('adcGeneral.insightP2a')} <strong style={{ color: '#F1F5F9' }}>{t('adcGeneral.insightP2Strong')}</strong>{t('adcGeneral.insightP2b')}
          </p>
          <p style={{ margin: 0, color: '#94A3B8', fontSize: 14, lineHeight: 1.7 }}>
            {t('adcGeneral.insightP3')}
          </p>
        </div>

        <Callout
          icon="🔭"
          color={C.purple}
          title={t('adcGeneral.calloutContributionTitle')}
          body={t('adcGeneral.calloutContributionBody')}
        />
      </div>

      {/* Footer */}
      <div style={{
        borderTop: `1px solid ${C.border}`, paddingTop: 24,
        display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
        fontSize: 12, color: C.sub,
      }}>
        <div>
          <strong style={{ color: C.text }}>{t('adcGeneral.footerTitle')}</strong>
          {' · '}{t('adcGeneral.footerSub')}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Badge color={C.blue} label="BKT/HMM" />
          <Badge color={C.purple} label="DKT/LSTM" />
          <Badge color={C.green} label="SAKT" />
          <Badge color={C.orange} label="GKT" />
        </div>
      </div>

      <NextSteps />
    </div>
  )
}
