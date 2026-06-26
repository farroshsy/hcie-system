'use client'

import { useState } from 'react'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

const C = {
  bg:       '#F8FAFC',
  card:     '#FFFFFF',
  border:   '#E2E8F0',
  text:     '#1E293B',
  sub:      '#64748B',
  blue:     '#3B82F6',
  blueD:    '#1D4ED8',
  green:    '#10B981',
  yellow:   '#F59E0B',
  red:      '#EF4444',
  purple:   '#8B5CF6',
  cyan:     '#06B6D4',
  orange:   '#F97316',
  navyBg:   '#0F172A',
  navyCard: '#1E293B',
}

// ─── tiny building blocks ──────────────────────────────────────────────────

function Badge({ color, label }: { color: string; label: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 10,
      fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
      background: color + '20', color, border: `1px solid ${color}40`,
    }}>{label}</span>
  )
}

function Arrow({ v }: { v?: boolean }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      color: C.blue, fontSize: v ? 20 : 16, lineHeight: 1,
      margin: v ? '4px 0' : '0 4px', flexShrink: 0,
    }}>{v ? '↓' : '→'}</div>
  )
}

function SectionHeader({ n, title, sub }: { n: string; title: string; sub: string }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <span style={{
          width: 32, height: 32, borderRadius: '50%',
          background: C.blue, color: '#fff',
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
      borderLeft: `4px solid ${color}`, borderRadius: 8,
      padding: '14px 18px', marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span style={{ fontWeight: 700, color, fontSize: 14 }}>{title}</span>
      </div>
      <p style={{ margin: 0, color: C.text, fontSize: 14, lineHeight: 1.7 }}>{body}</p>
    </div>
  )
}

// ─── Flow diagram node ─────────────────────────────────────────────────────

interface NodeProps {
  label: string
  sub?: string
  color?: string
  icon?: string
  badge?: string
}
function Node({ label, sub, color = C.blue, icon, badge }: NodeProps) {
  return (
    <div style={{
      background: color + '12', border: `2px solid ${color}40`,
      borderRadius: 10, padding: '10px 14px', textAlign: 'center',
      minWidth: 100, maxWidth: 150,
    }}>
      {icon && <div style={{ fontSize: 20, marginBottom: 4 }}>{icon}</div>}
      <div style={{ fontWeight: 700, fontSize: 13, color, lineHeight: 1.2 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: C.sub, marginTop: 3, lineHeight: 1.3 }}>{sub}</div>}
      {badge && <Badge color={color} label={badge} />}
    </div>
  )
}

// ─── Code snippet ──────────────────────────────────────────────────────────

function Code({ title, lang, code }: { title: string; lang: string; code: string }) {
  return (
    <div style={{ marginBottom: 16, borderRadius: 8, overflow: 'hidden', border: `1px solid ${C.border}` }}>
      <div style={{
        background: C.navyCard, padding: '8px 14px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ color: '#94A3B8', fontSize: 12, fontWeight: 600 }}>{title}</span>
        <Badge color={C.cyan} label={lang} />
      </div>
      <pre style={{
        margin: 0, padding: '14px 16px', background: C.navyBg,
        color: '#E2E8F0', fontSize: 12.5, lineHeight: 1.6,
        overflowX: 'auto', fontFamily: 'monospace',
      }}>{code.trim()}</pre>
    </div>
  )
}

// ─── Component card ────────────────────────────────────────────────────────

function CompCard({
  icon, color, title, file, role, output, outputLabel,
}: { icon: string; color: string; title: string; file: string; role: string; output: string; outputLabel: string }) {
  return (
    <div style={{
      background: C.card, border: `1px solid ${C.border}`,
      borderTop: `3px solid ${color}`, borderRadius: 10,
      padding: 20, flex: '1 1 280px', minWidth: 260,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{title}</div>
          <code style={{ fontSize: 11, color: C.sub }}>{file}</code>
        </div>
      </div>
      <p style={{ margin: '0 0 10px', fontSize: 13, color: C.sub, lineHeight: 1.6 }}>{role}</p>
      <div style={{
        background: color + '08', borderRadius: 6, padding: '8px 10px',
        fontSize: 12, color, fontWeight: 600,
      }}>{outputLabel}: {output}</div>
    </div>
  )
}

// ─── Container card ────────────────────────────────────────────────────────

function ContainerCard({
  name, port, image, role, color = C.blue,
}: { name: string; port?: string; image: string; role: string; color?: string }) {
  return (
    <div style={{
      background: C.navyCard, borderRadius: 10, padding: 16,
      border: `1px solid rgba(255,255,255,0.08)`,
      flex: '1 1 180px', minWidth: 160,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontWeight: 700, color: '#F1F5F9', fontSize: 13 }}>{name}</span>
        {port && <Badge color={color} label={`:${port}`} />}
      </div>
      <div style={{ fontSize: 11, color: '#64748B', marginBottom: 8 }}>{image}</div>
      <p style={{ margin: 0, fontSize: 12, color: '#94A3B8', lineHeight: 1.5 }}>{role}</p>
    </div>
  )
}

// ─── Timeline step ────────────────────────────────────────────────────────

function TimelineStep({
  step, label, detail, color = C.blue, ms,
}: { step: number; label: string; detail: string; color?: string; ms?: string }) {
  return (
    <div style={{ display: 'flex', gap: 14, marginBottom: 18 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: color, color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 800, fontSize: 12,
        }}>{step}</div>
        <div style={{ width: 2, flex: 1, background: C.border, marginTop: 4 }} />
      </div>
      <div style={{ paddingBottom: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{label}</span>
          {ms && <Badge color={color} label={ms} />}
        </div>
        <p style={{ margin: 0, fontSize: 13, color: C.sub, lineHeight: 1.6 }}>{detail}</p>
      </div>
    </div>
  )
}

// ─── Main page ─────────────────────────────────────────────────────────────

export default function ArchitecturePage() {
  const t = useT()
  const [activeSection, setActiveSection] = useState<string | null>(null)

  const toc = [
    { id: 'overview',   label: t('architecture.tocOverview'),    color: C.blue },
    { id: 'ingestion',  label: t('architecture.tocIngestion'),   color: C.cyan },
    { id: 'engine',     label: t('architecture.tocEngine'),      color: C.purple },
    { id: 'bandit',     label: t('architecture.tocBandit'),      color: C.orange },
    { id: 'consumers',  label: t('architecture.tocConsumers'),   color: C.green },
    { id: 'adc',        label: t('architecture.tocAdc'),         color: C.yellow },
    { id: 'routing',    label: t('architecture.tocRouting'),     color: C.red },
    { id: 'lifecycle',  label: t('architecture.tocLifecycle'),   color: C.blue },
    { id: 'datastores', label: t('architecture.tocDatastores'),  color: C.cyan },
    { id: 'invariants', label: t('architecture.tocInvariants'),  color: C.purple },
  ]

  return (
    <div style={{ padding: '36px 40px 80px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <Badge color={C.blue}  label={t('architecture.heroBadgeArchitecture')} />
          <Badge color={C.green} label={t('architecture.heroBadgeEventSourced')} />
          <Badge color={C.purple} label={t('architecture.heroBadgeResearchGrade')} />
        </div>
        <h1 style={{ fontSize: 34, fontWeight: 900, color: C.text, margin: '0 0 12px', lineHeight: 1.2 }}>
          {t('architecture.heroTitle')}
        </h1>
        <p style={{ fontSize: 16, color: C.sub, lineHeight: 1.7, maxWidth: 720, margin: 0 }}>
          {t('architecture.heroLeadA')}{' '}
          <strong>{t('architecture.heroLeadStrong')}</strong>. {t('architecture.heroLeadB')}
        </p>
      </div>

      {/* Table of contents */}
      <div style={{
        background: C.navyCard, borderRadius: 12, padding: 20, marginBottom: 40,
        display: 'flex', flexWrap: 'wrap', gap: 8,
      }}>
        <span style={{ color: '#64748B', fontSize: 12, fontWeight: 600, width: '100%', marginBottom: 4 }}>
          {t('architecture.tocLabel')}
        </span>
        {toc.map(({ id, label, color }) => (
          <a
            key={id}
            href={`#${id}`}
            style={{
              padding: '5px 12px', borderRadius: 6, fontSize: 13, fontWeight: 600,
              background: color + '20', color, textDecoration: 'none',
              border: `1px solid ${color}30`,
            }}
          >{label}</a>
        ))}
      </div>

      {/* ── SECTION 1: OVERVIEW ─────────────────────────────────────── */}
      <div id="overview" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="1"
          title={t('architecture.s1Title')}
          sub={t('architecture.s1Sub')}
        />

        <Callout
          icon="🔑"
          color={C.blue}
          title={t('architecture.s1CalloutTitle')}
          body={t('architecture.s1CalloutBody')}
        />

        {/* High-level flow diagram */}
        <div style={{
          background: C.card, border: `1px solid ${C.border}`,
          borderRadius: 12, padding: 24, marginBottom: 24,
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, letterSpacing: '0.08em', marginBottom: 16 }}>
            {t('architecture.s1FlowLabel')}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
            <Node label={t('architecture.s1NodeBrowser')} sub={t('architecture.s1NodeBrowserSub')} icon="🌐" color={C.blue} />
            <Arrow />
            <Node label={t('architecture.s1NodeGateway')} sub="nginx :80" icon="⚡" color={C.cyan} />
            <Arrow />
            <Node label={t('architecture.s1NodeApi')} sub="FastAPI :8011" icon="🔧" color={C.purple} />
            <Arrow />
            <Node label={t('architecture.s1NodeEngine')} sub="unified_brain" icon="🧠" color={C.orange} />
            <Arrow />
            <Node label={t('architecture.s1NodeOutbox')} sub={t('architecture.s1NodeOutboxSub')} icon="📦" color={C.green} />
            <Arrow />
            <Node label="Kafka" sub={t('architecture.s1NodeKafkaSub')} icon="📡" color={C.yellow} />
            <Arrow />
            <Node label={t('architecture.s1NodeConsumers')} sub={t('architecture.s1NodeConsumersSub')} icon="⚙️" color={C.red} />
            <Arrow />
            <Node label={t('architecture.s1NodeTraj')} sub="experiment_trajectories" icon="📊" color={C.blue} />
          </div>
          <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 6, opacity: 0.7 }}>
            <div style={{ flex: 1, height: 1, background: C.border }} />
            <span style={{ fontSize: 11, color: C.sub }}>{t('architecture.s1FlowFooter')}</span>
            <div style={{ flex: 1, height: 1, background: C.border }} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          {[
            { label: t('architecture.s1StatSealedLabel'), value: '96,727', sub: t('architecture.s1StatSealedSub'), color: C.blue },
            { label: t('architecture.s1StatLiveLabel'), value: '112,465', sub: t('architecture.s1StatLiveSub'), color: C.green },
            { label: t('architecture.s1StatJtLabel'), value: '6', sub: t('architecture.s1StatJtSub'), color: C.purple },
            { label: t('architecture.s1StatConsumersLabel'), value: '4', sub: t('architecture.s1StatConsumersSub'), color: C.orange },
          ].map(({ label, value, sub, color }) => (
            <div key={label} style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderRadius: 10, padding: '16px 20px', textAlign: 'center',
            }}>
              <div style={{ fontSize: 28, fontWeight: 900, color }}>{value}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{label}</div>
              <div style={{ fontSize: 11, color: C.sub }}>{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── SECTION 2: EVENT INGESTION ──────────────────────────────── */}
      <div id="ingestion" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="2"
          title={t('architecture.s2Title')}
          sub={t('architecture.s2Sub')}
        />

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 24 }}>
          <div style={{ flex: 2, minWidth: 280 }}>
            <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8, marginTop: 0 }}>
              {t('architecture.s2ParaA')}{' '}
              <em>{t('architecture.s2ParaEm1')}</em> {t('architecture.s2ParaB')}{' '}
              <strong>{t('architecture.s2ParaStrong')}</strong>{t('architecture.s2ParaC')}{' '}
              <code>interactions</code> {t('architecture.s2ParaD')} <code>outbox_events</code>{' '}
              {t('architecture.s2ParaE')} <em>{t('architecture.s2ParaEm2')}</em>{' '}
              {t('architecture.s2ParaF')} <code>interaction_id</code>{t('architecture.s2ParaG')}
            </p>
            <Callout
              icon="🔒"
              color={C.cyan}
              title={t('architecture.s2CalloutTitle')}
              body={t('architecture.s2CalloutBody')}
            />
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <Code
              title={t('architecture.s2CodeOutboxTitle')}
              lang="SQL"
              code={`
CREATE TABLE outbox_events (
  id           BIGSERIAL PRIMARY KEY,
  event_type   TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,   -- user_id
  payload      JSONB NOT NULL,
  topic        TEXT NOT NULL,
  status       TEXT DEFAULT 'pending',
  created_at   TIMESTAMPTZ DEFAULT now(),
  delivered_at TIMESTAMPTZ
);

-- Atomic write pattern (ITS runtime)
BEGIN;
  INSERT INTO interactions (...) VALUES (...);
  INSERT INTO outbox_events (
    event_type, aggregate_id,
    payload, topic
  ) VALUES (
    'learner.attempt',
    :user_id,
    :full_interaction_json,
    'hcie.interactions'
  );
COMMIT;
`}
            />
          </div>
        </div>

        <Code
          title={t('architecture.s2CodeRoutingTitle')}
          lang="Python"
          code={`
# Two primary topics
TOPIC_INTERACTIONS   = "hcie.interactions"    # every attempt
TOPIC_LEARNER_UPDATE = "hcie.learner-updates" # mastery state change

# Partition key = user_id → guarantees ordering per learner
producer.produce(
    topic   = TOPIC_INTERACTIONS,
    key     = str(user_id),
    value   = json.dumps(event_payload),
)
# Consumers read from topic + partition → no out-of-order mastery updates
`}
        />
      </div>

      {/* ── SECTION 3: HCIE ENGINE ──────────────────────────────────── */}
      <div id="engine" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="3"
          title={t('architecture.s3Title')}
          sub={t('architecture.s3Sub')}
        />

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 24 }}>
          <CompCard
            icon="📐"
            color={C.blue}
            title={t('architecture.s3KfTitle')}
            file="core/03_ensemble/unified_brain.py"
            role={t('architecture.s3KfRole')}
            output="μ_k, σ²_k — posterior mastery ∈ [0,1]"
            outputLabel={t('architecture.s3OutputLabel')}
          />
          <CompCard
            icon="🎲"
            color={C.purple}
            title={t('architecture.s3BayesTitle')}
            file="core/03_ensemble/unified_brain.py"
            role={t('architecture.s3BayesRole')}
            output="E[mastery] = α/(α+β), Var = αβ/(α+β)²(α+β+1)"
            outputLabel={t('architecture.s3OutputLabel')}
          />
          <CompCard
            icon="⚖️"
            color={C.orange}
            title={t('architecture.s3EnsembleTitle')}
            file="core/03_ensemble/unified_brain.py"
            role={t('architecture.s3EnsembleRole')}
            output="ŷ_ensemble = w_KF·μ_KF + w_Bayes·E[Beta]"
            outputLabel={t('architecture.s3OutputLabel')}
          />
          <CompCard
            icon="🗺️"
            color={C.green}
            title={t('architecture.s3JtTitle')}
            file="core/03_ensemble/unified_brain.py"
            role={t('architecture.s3JtRole')}
            output="jt_score_total ∈ ℝ, 6 jt_*_contribution columns"
            outputLabel={t('architecture.s3OutputLabel')}
          />
        </div>

        {/* JT dimensions breakdown */}
        <div style={{
          background: C.card, border: `1px solid ${C.border}`,
          borderRadius: 12, padding: 24, marginBottom: 24,
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, letterSpacing: '0.08em', marginBottom: 16 }}>
            {t('architecture.s3TableLabel')}
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: C.navyCard }}>
                  {[
                    t('architecture.s3ColDimension'),
                    t('architecture.s3ColColumn'),
                    t('architecture.s3ColFormula'),
                    t('architecture.s3ColComplexity'),
                    t('architecture.s3ColStatus'),
                  ].map(h => (
                    <th key={h} style={{ padding: '10px 12px', color: '#94A3B8', fontWeight: 600, textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { dim: t('architecture.s3RowDeltaMDim'), col: 'jt_delta_m_contribution', formula: 'μ_after − μ_before', cplx: 'O(1)', status: C.green, statusL: t('architecture.s3StatusPass') },
                  { dim: t('architecture.s3RowTransferDim'), col: 'jt_transfer_contribution', formula: 'Σ w_ij · μ_j for j ∈ prereqs(k)', cplx: 'O(indeg(k))', status: C.yellow, statusL: t('architecture.s3StatusDisclose') },
                  { dim: t('architecture.s3RowProspectiveDim'), col: 'jt_transfer_prospective_contribution', formula: t('architecture.s3RowProspectiveFormula'), cplx: 'O(1)', status: C.red, statusL: t('architecture.s3StatusDormant') },
                  { dim: t('architecture.s3RowChallengeDim'), col: 'jt_challenge_contribution', formula: 'avg_difficulty × recent_err_rate', cplx: 'O(1)', status: C.yellow, statusL: t('architecture.s3StatusWarnLatency') },
                  { dim: t('architecture.s3RowUncertaintyDim'), col: 'jt_uncertainty_contribution', formula: t('architecture.s3RowUncertaintyFormula'), cplx: 'O(1)', status: C.green, statusL: t('architecture.s3StatusPass') },
                  { dim: 'ZPD', col: 'jt_zpd_contribution', formula: 'sigmoid((μ − 0.4)/0.2)', cplx: 'O(1)', status: C.yellow, statusL: t('architecture.s3StatusSaturated') },
                ].map((r, i) => (
                  <tr key={r.col} style={{ background: i % 2 === 0 ? 'transparent' : '#F8FAFC' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: C.text }}>{r.dim}</td>
                    <td style={{ padding: '10px 12px' }}><code style={{ fontSize: 11, color: C.sub }}>{r.col}</code></td>
                    <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: 12, color: C.text }}>{r.formula}</td>
                    <td style={{ padding: '10px 12px' }}><Badge color={C.blue} label={r.cplx} /></td>
                    <td style={{ padding: '10px 12px' }}><Badge color={r.status} label={r.statusL} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ margin: '12px 0 0', fontSize: 12, color: C.sub }}>
            {t('architecture.s3TableFootnote')}
          </p>
        </div>

        <Code
          title={t('architecture.s3CodeJtTitle')}
          lang="Python"
          code={`
def compute_jt(
    concept_id: str,
    mastery_before: float,
    mastery_after:  float,
    prereq_mastery: dict[str, float],  # {concept_id: μ} for all prereqs
    uncertainty:    float,
    difficulty:     float,
    zpd_score:      float,
) -> JTResult:
    delta_m      = mastery_after - mastery_before
    t_realized   = sum(prereq_mastery.values()) / max(len(prereq_mastery), 1)
    t_prospective = 0.0                         # dormant — 5 formulations failed
    challenge    = difficulty * (1 - mastery_before)
    uncertainty_ = 1 - abs(2 * mastery_after - 1)
    zpd          = sigmoid((mastery_after - 0.4) / 0.2)

    total = (0.30 * delta_m + 0.25 * t_realized + 0.10 * t_prospective
           + 0.15 * challenge + 0.10 * uncertainty_ + 0.10 * zpd)
    return JTResult(total=total, delta_m=delta_m, t_realized=t_realized,
                    challenge=challenge, uncertainty=uncertainty_, zpd=zpd,
                    t_prospective=t_prospective)
`}
        />
      </div>

      {/* ── SECTION 4: MODALITY BANDIT ─────────────────────────────── */}
      <div id="bandit" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="4"
          title={t('architecture.s4Title')}
          sub={t('architecture.s4Sub')}
        />

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 24 }}>
          <div style={{ flex: 2, minWidth: 280 }}>
            <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8, marginTop: 0 }}>
              {t('architecture.s4ParaA')}{' '}
              <em>{t('architecture.s4ParaEm')}</em>{' '}
              {t('architecture.s4ParaB')}
            </p>
            <div style={{
              fontFamily: 'monospace', fontSize: 13, background: C.navyBg,
              color: '#E2E8F0', borderRadius: 8, padding: '14px 18px', marginBottom: 16,
            }}>
              {'θ_arm ~ Beta(α_arm + 1, β_arm + 1)'}
              <br />
              {'arm* = argmax(θ_arm over all arms)'}
              <br />
              {'On reward=1: α_arm += 1'}
              <br />
              {'On reward=0: β_arm += 1'}
            </div>
            <Callout
              icon="🛡️"
              color={C.orange}
              title={t('architecture.s4CalloutTitle')}
              body={t('architecture.s4CalloutBody')}
            />
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderRadius: 10, padding: 18,
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, marginBottom: 12 }}>
                {t('architecture.s4ArmsLabel')}
              </div>
              {[
                { arm: 'text',  icon: '📖', desc: t('architecture.s4ArmTextDesc') },
                { arm: 'mcq',   icon: '✅', desc: t('architecture.s4ArmMcqDesc') },
                { arm: 'video', icon: '🎬', desc: t('architecture.s4ArmVideoDesc') },
                { arm: 'audio', icon: '🔊', desc: t('architecture.s4ArmAudioDesc') },
              ].map(({ arm, icon, desc }) => (
                <div key={arm} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 0', borderBottom: `1px solid ${C.border}`,
                }}>
                  <span style={{ fontSize: 18 }}>{icon}</span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 13, color: C.text }}>{arm}</div>
                    <div style={{ fontSize: 11, color: C.sub }}>{desc}</div>
                  </div>
                </div>
              ))}
              <div style={{ marginTop: 12, fontSize: 11, color: C.sub }}>
                {t('architecture.s4PosteriorStored')} <code>selection_metrics</code> {t('architecture.s4PosteriorTable')}<br />
                α, β {t('architecture.s4PosteriorPer')} (user_id, concept_id, arm)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── SECTION 5: KAFKA CONSUMERS ─────────────────────────────── */}
      <div id="consumers" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="5"
          title={t('architecture.s5Title')}
          sub={t('architecture.s5Sub')}
        />

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
          {[
            {
              icon: '📊', color: C.blue,
              name: 'trajectory-recorder',
              reads: 'hcie.interactions',
              writes: 'experiment_trajectories',
              role: t('architecture.s5TrajRole'),
            },
            {
              icon: '🧮', color: C.purple,
              name: 'projection-consumer',
              reads: 'hcie.interactions',
              writes: 'learner_projections',
              role: t('architecture.s5ProjRole'),
            },
            {
              icon: '🔄', color: C.green,
              name: 'learning-consumer',
              reads: 'hcie.learner-updates',
              writes: 'learner_state, concept_mastery',
              role: t('architecture.s5LearnRole'),
            },
            {
              icon: '🔍', color: C.orange,
              name: 'audit-consumer',
              reads: 'hcie.interactions',
              writes: 'audit_log (append-only)',
              role: t('architecture.s5AuditRole'),
            },
          ].map(c => (
            <div key={c.name} style={{
              flex: '1 1 240px', minWidth: 220,
              background: C.card, border: `1px solid ${C.border}`,
              borderLeft: `4px solid ${c.color}`, borderRadius: 10, padding: 18,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <span style={{ fontSize: 22 }}>{c.icon}</span>
                <span style={{ fontWeight: 700, fontSize: 14, color: C.text }}>{c.name}</span>
              </div>
              <div style={{ marginBottom: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <Badge color={C.cyan} label={`← ${c.reads}`} />
                <Badge color={c.color} label={`→ ${c.writes}`} />
              </div>
              <p style={{ margin: 0, fontSize: 12.5, color: C.sub, lineHeight: 1.6 }}>{c.role}</p>
            </div>
          ))}
        </div>

        <Code
          title={t('architecture.s5CodeTitle')}
          lang="Python"
          code={`
# trajectory-recorder consumer — handles duplicate events safely
def record_trajectory(event: InteractionEvent) -> None:
    with db.transaction():
        existing = db.fetchone(
            "SELECT id FROM experiment_trajectories "
            "WHERE interaction_id = %s AND experiment_run_id = %s",
            (event.interaction_id, event.run_id)
        )
        if existing:
            return   # already recorded — Kafka at-least-once safe

        db.execute("""
            INSERT INTO experiment_trajectories (
                interaction_id, experiment_run_id, user_id, concept_id,
                jt_delta_m_contribution, jt_transfer_contribution,
                jt_challenge_contribution, jt_uncertainty_contribution,
                jt_zpd_contribution, jt_transfer_prospective_contribution,
                mastery_after, ensemble_weight_kf, ensemble_weight_bayes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (...event fields...))
`}
        />
      </div>

      {/* ── SECTION 6: ADC AUDIT PATH ───────────────────────────────── */}
      <div id="adc" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="6"
          title={t('architecture.s6Title')}
          sub={t('architecture.s6Sub')}
        />

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 24 }}>
          <div style={{ flex: 2, minWidth: 280 }}>
            <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8, marginTop: 0 }}>
              {t('architecture.s6ParaA')} <em>{t('architecture.s6ParaEm')}</em>{' '}
              {t('architecture.s6ParaB')}
            </p>
            <div style={{
              background: C.navyBg, borderRadius: 8, padding: '14px 18px', marginBottom: 16,
              fontFamily: 'monospace', color: '#E2E8F0', fontSize: 13, lineHeight: 1.7,
            }}>
              {'for dim in JT_DIMENSIONS:'}
              <br />
              {'    μ = mean(traj[dim])'}
              <br />
              {'    σ = std(traj[dim])'}
              <br />
              {'    # Gate 1: above sigmoid floor'}
              <br />
              {'    if μ <= α_floor (0.01): verdict = FLOOR_NOISE'}
              <br />
              {'    # Gate 2: meaningful variance'}
              <br />
              {'    elif σ/μ < 0.08: verdict = NEAR_CONSTANT'}
              <br />
              {'    else: verdict = INFORMATIVE'}
            </div>
            <Callout
              icon="⚠️"
              color={C.yellow}
              title={t('architecture.s6CalloutTitle')}
              body={t('architecture.s6CalloutBody')}
            />
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div style={{
              background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 18,
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, marginBottom: 12 }}>
                {t('architecture.s6VerdictsLabel')}
              </div>
              {[
                { dim: 'ΔM',             verdict: 'INFORMATIVE', color: C.green },
                { dim: 'T_realized',     verdict: 'INFORMATIVE', color: C.green },
                { dim: 'T_prospective',  verdict: 'FLOOR_NOISE', color: C.red },
                { dim: 'Challenge',      verdict: 'NEAR_CONSTANT', color: C.yellow },
                { dim: 'Uncertainty',    verdict: 'INFORMATIVE', color: C.green },
                { dim: 'ZPD',           verdict: 'NEAR_CONSTANT', color: C.yellow },
              ].map(({ dim, verdict, color }) => (
                <div key={dim} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '7px 0', borderBottom: `1px solid ${C.border}`,
                }}>
                  <span style={{ fontSize: 13, color: C.text }}>{dim}</span>
                  <Badge color={color} label={verdict} />
                </div>
              ))}
              <div style={{ marginTop: 12, fontSize: 11, color: C.sub }}>
                {t('architecture.s6VerdictsSource')} <code>run-94a3b8ba</code>, N=96,727 {t('architecture.s6VerdictsLearners')}
              </div>
            </div>
          </div>
        </div>

        {/* ADC cascade path */}
        <div style={{
          background: C.card, border: `1px solid ${C.border}`,
          borderRadius: 12, padding: 20, marginBottom: 16,
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.sub, letterSpacing: '0.08em', marginBottom: 14 }}>
            {t('architecture.s6CascadeLabel')}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
            {[
              { label: 'experiment_trajectories', color: C.blue },
              { label: t('architecture.s6CascadeClassifier'), color: C.purple },
              { label: t('architecture.s6CascadeTier2'), color: C.orange },
              { label: t('architecture.s6CascadeTier2_5'), color: C.yellow },
              { label: t('architecture.s6CascadeTier5'), color: C.green },
              { label: 'cascade_status', color: C.cyan },
              { label: t('architecture.s6CascadeThesis'), color: C.red },
            ].map((n, i) => (
              <>
                <Node key={n.label} label={n.label} color={n.color} />
                {i < 6 && <Arrow key={`a${i}`} />}
              </>
            ))}
          </div>
          <p style={{ margin: '12px 0 0', fontSize: 12, color: C.sub }}>
            {t('architecture.s6CascadeFootnoteA')} <code>jt_design_decisions.json</code> {t('architecture.s6CascadeFootnoteB')}
          </p>
        </div>
      </div>

      {/* ── SECTION 7: ROUTING & CONTAINERS ────────────────────────── */}
      <div id="routing" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="7"
          title={t('architecture.s7Title')}
          sub={t('architecture.s7Sub')}
        />

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
          <div style={{ flex: 2, minWidth: 280 }}>
            <div style={{
              background: C.navyBg, borderRadius: 12, padding: 24,
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#64748B', marginBottom: 16 }}>
                {t('architecture.s7TopologyLabel')}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                <ContainerCard name="gateway" port="80" image="nginx:alpine" role={t('architecture.s7CtrGateway')} color={C.cyan} />
                <ContainerCard name="api" port="8011" image="hcie-api (FastAPI)" role={t('architecture.s7CtrApi')} color={C.blue} />
                <ContainerCard name="frontend" port="3001" image="hcie-frontend (Next.js)" role={t('architecture.s7CtrFrontend')} color={C.purple} />
                <ContainerCard name="kafka" image="confluentinc/kafka" role={t('architecture.s7CtrKafka')} color={C.orange} />
                <ContainerCard name="zookeeper" image="confluentinc/zookeeper" role={t('architecture.s7CtrZookeeper')} color={C.yellow} />
                <ContainerCard name="postgres" port="5432" image="postgres:14" role={t('architecture.s7CtrPostgres')} color={C.green} />
                <ContainerCard name="consumer-*" image="4 typed workers" role={t('architecture.s7CtrConsumer')} color={C.red} />
              </div>
            </div>
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <Code
              title={t('architecture.s7CodeNginxTitle')}
              lang="nginx"
              code={`
# gateway/nginx.conf
server {
  listen 80;
  listen [::]:80;   # ← critical fix: was IPv4-only

  # API — all /api/* and /v3/*
  location ~ ^/(api|v3)/ {
    proxy_pass http://api:8011;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # Frontend — everything else
  location / {
    proxy_pass http://frontend:3000;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
  }
}
`}
            />
            <Code
              title={t('architecture.s7CodeNetworkTitle')}
              lang="bash"
              code={`
# Accessible on research network:
# http://RESEARCH_NET_IP → gateway :80
# http://RESEARCH_NET_IP/api/v3/... → API
# http://RESEARCH_NET_IP/review/... → frontend

# Local port (direct to API for debugging):
# http://localhost:8011/v3/...
`}
            />
          </div>
        </div>
      </div>

      {/* ── SECTION 8: FULL REQUEST LIFECYCLE ──────────────────────── */}
      <div id="lifecycle" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="8"
          title={t('architecture.s8Title')}
          sub={t('architecture.s8Sub')}
        />

        <div style={{ position: 'relative' }}>
          <TimelineStep
            step={1} color={C.blue} ms="~0ms"
            label={t('architecture.s8Step1Label')}
            detail={t('architecture.s8Step1Detail')}
          />
          <TimelineStep
            step={2} color={C.cyan} ms="~1ms"
            label={t('architecture.s8Step2Label')}
            detail={t('architecture.s8Step2Detail')}
          />
          <TimelineStep
            step={3} color={C.purple} ms="~2ms"
            label={t('architecture.s8Step3Label')}
            detail={t('architecture.s8Step3Detail')}
          />
          <TimelineStep
            step={4} color={C.orange} ms="~5ms"
            label={t('architecture.s8Step4Label')}
            detail={t('architecture.s8Step4Detail')}
          />
          <TimelineStep
            step={5} color={C.green} ms="~8ms"
            label={t('architecture.s8Step5Label')}
            detail={t('architecture.s8Step5Detail')}
          />
          <TimelineStep
            step={6} color={C.yellow} ms="~10ms"
            label={t('architecture.s8Step6Label')}
            detail={t('architecture.s8Step6Detail')}
          />
          <TimelineStep
            step={7} color={C.red} ms="async"
            label={t('architecture.s8Step7Label')}
            detail={t('architecture.s8Step7Detail')}
          />
          <TimelineStep
            step={8} color={C.purple} ms="~50–200ms"
            label={t('architecture.s8Step8Label')}
            detail={t('architecture.s8Step8Detail')}
          />
          <TimelineStep
            step={9} color={C.blue} ms={t('architecture.s8Step9Ms')}
            label={t('architecture.s8Step9Label')}
            detail={t('architecture.s8Step9Detail')}
          />
        </div>
      </div>

      {/* ── SECTION 9: DATA STORES ──────────────────────────────────── */}
      <div id="datastores" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="9"
          title={t('architecture.s9Title')}
          sub={t('architecture.s9Sub')}
        />

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginBottom: 24 }}>
            <thead>
              <tr style={{ background: C.navyCard }}>
                {[
                  t('architecture.s9ColTable'),
                  t('architecture.s9ColPartitioned'),
                  t('architecture.s9ColWritten'),
                  t('architecture.s9ColRead'),
                  t('architecture.s9ColRole'),
                ].map(h => (
                  <th key={h} style={{ padding: '10px 12px', color: '#94A3B8', fontWeight: 600, textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                {
                  table: 'interactions', part: 'user_id, concept_id', by: t('architecture.s9ByApiSync'), reads: t('architecture.s9ReadsAllConsumers'), role: t('architecture.s9RoleInteractions'),
                },
                {
                  table: 'outbox_events', part: 'status, created_at', by: t('architecture.s9ByApiTx'), reads: t('architecture.s9ReadsKafkaProducer'), role: t('architecture.s9RoleOutbox'),
                },
                {
                  table: 'experiment_trajectories', part: 'experiment_run_id, user_id', by: 'trajectory-recorder', reads: t('architecture.s9ReadsAdcGrounding'), role: t('architecture.s9RoleTrajectories'),
                },
                {
                  table: 'learner_projections', part: 'user_id, concept_id', by: 'projection-consumer', reads: t('architecture.s9ReadsApiNextRec'), role: t('architecture.s9RoleProjections'),
                },
                {
                  table: 'selection_metrics', part: 'user_id, concept_id, arm', by: t('architecture.s9ByBandit'), reads: t('architecture.s9ReadsBandit'), role: t('architecture.s9RoleSelectionMetrics'),
                },
                {
                  table: 'outbox_events (audit)', part: 'aggregate_id, event_type', by: t('architecture.s9ByApiTx'), reads: t('architecture.s9ReadsAuditConsumer'), role: t('architecture.s9RoleAudit'),
                },
              ].map((r, i) => (
                <tr key={r.table} style={{ background: i % 2 === 0 ? 'transparent' : '#F8FAFC' }}>
                  <td style={{ padding: '10px 12px' }}><code style={{ fontWeight: 700, color: C.blue }}>{r.table}</code></td>
                  <td style={{ padding: '10px 12px', fontSize: 11, color: C.sub }}>{r.part}</td>
                  <td style={{ padding: '10px 12px' }}><Badge color={C.green} label={r.by} /></td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: C.sub }}>{r.reads}</td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: C.text }}>{r.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <Code
          title={t('architecture.s9CodeTitle')}
          lang="SQL"
          code={`
-- Sealed runs (reproducible, used in paper)
SELECT * FROM experiment_trajectories
WHERE experiment_run_id = 'run-94a3b8ba'  -- Junyi N=96,727
   OR experiment_run_id = 'run-e49d92e6'; -- ASSISTments-2009 N=4,729

-- Live runs (real learners, ongoing)
SELECT COUNT(*), COUNT(DISTINCT user_id)
FROM experiment_trajectories
WHERE experiment_run_id LIKE 'live::%%';
-- Pattern: live::run-<uuid>::ex_<dataset>_<user_id>
-- ⚠ psycopg2: use %% not % — single % is eaten as parameter placeholder

-- ADC reads sealed only — never live
SELECT dim, mean_val, std_val, verdict
FROM adc_dimension_verdicts
WHERE run_id = 'run-94a3b8ba';
`}
        />
      </div>

      {/* ── SECTION 10: DESIGN INVARIANTS ──────────────────────────── */}
      <div id="invariants" style={{ marginBottom: 60 }}>
        <SectionHeader
          n="10"
          title={t('architecture.s10Title')}
          sub={t('architecture.s10Sub')}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[
            {
              n: 'I-1', color: C.red,
              title: t('architecture.s10I1Title'),
              body: t('architecture.s10I1Body'),
            },
            {
              n: 'I-2', color: C.orange,
              title: t('architecture.s10I2Title'),
              body: t('architecture.s10I2Body'),
            },
            {
              n: 'I-3', color: C.purple,
              title: t('architecture.s10I3Title'),
              body: t('architecture.s10I3Body'),
            },
            {
              n: 'I-4', color: C.blue,
              title: t('architecture.s10I4Title'),
              body: t('architecture.s10I4Body'),
            },
            {
              n: 'I-5', color: C.green,
              title: t('architecture.s10I5Title'),
              body: t('architecture.s10I5Body'),
            },
          ].map(({ n, color, title, body }) => (
            <div key={n} style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderLeft: `4px solid ${color}`, borderRadius: 10, padding: '16px 20px',
              display: 'flex', gap: 16,
            }}>
              <div style={{
                flexShrink: 0, width: 44, height: 44, borderRadius: 8,
                background: color + '15', display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontWeight: 800, fontSize: 12, color,
              }}>{n}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, color: C.text, marginBottom: 6 }}>{title}</div>
                <p style={{ margin: 0, fontSize: 13, color: C.sub, lineHeight: 1.7 }}>{body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        borderTop: `1px solid ${C.border}`, paddingTop: 24,
        display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
        fontSize: 12, color: C.sub,
      }}>
        <div>
          <strong style={{ color: C.text }}>{t('architecture.footerTitle')}</strong>
          {' · '}sealed run-94a3b8ba · N=96,727 · α_floor=0.01
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Badge color={C.blue} label="FastAPI + Next.js" />
          <Badge color={C.orange} label="Kafka + Postgres" />
          <Badge color={C.green} label={t('architecture.heroBadgeEventSourced')} />
          <Badge color={C.purple} label={t('architecture.heroBadgeResearchGrade')} />
        </div>
      </div>

      <NextSteps />
    </div>
  )
}
