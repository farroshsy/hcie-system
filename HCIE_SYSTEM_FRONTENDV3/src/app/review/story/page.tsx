'use client'

import { useState } from 'react'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

const C = {
  accent:  '#1565C0',
  accentL: '#E3F2FD',
  green:   '#1E8449',
  greenL:  '#EAFAF1',
  warn:    '#B7791F',
  warnL:   '#FFFBEB',
  neutral: '#4A5568',
  dark:    '#1A2332',
  muted:   '#94A3B8',
  purple:  '#6D28D9',
  purpleL: '#EDE9FE',
  teal:    '#0891B2',
}

type T = (key: string, fallback?: string) => string

// ── primitives ─────────────────────────────────────────────────────────────────

function PullQuote({ children, color = C.accent }: { children: React.ReactNode; color?: string }) {
  return (
    <blockquote style={{
      borderLeft: `4px solid ${color}`,
      margin: '24px 0', padding: '12px 24px',
      background: `${color}0D`,
      borderRadius: '0 8px 8px 0',
      fontSize: 16, fontStyle: 'italic', color: C.dark,
      lineHeight: 1.75,
    }}>{children}</blockquote>
  )
}

function ActHeader({ act, title, sub, color }: { act: string; title: string; sub: string; color: string }) {
  return (
    <div style={{
      display: 'flex', gap: 16, alignItems: 'flex-start',
      margin: '44px 0 24px', paddingTop: 32,
      borderTop: `2px solid ${color}`,
    }}>
      <div style={{
        flexShrink: 0,
        background: color, color: '#fff',
        borderRadius: 10, padding: '6px 14px',
        fontWeight: 900, fontSize: 13, letterSpacing: '0.08em',
        textTransform: 'uppercase' as const,
      }}>{act}</div>
      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: C.muted,
                       letterSpacing: '0.1em', textTransform: 'uppercase' as const,
                       marginBottom: 4 }}>{sub}</div>
        <div style={{ fontSize: 22, fontWeight: 900, color: C.dark, lineHeight: 1.2 }}>{title}</div>
      </div>
    </div>
  )
}

function Analogy({ icon, title, label, children }: { icon: string; title: string; label: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: C.purpleL, border: `1px solid ${C.purple}`,
      borderRadius: 10, padding: '14px 18px', margin: '20px 0',
    }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontSize: 24 }}>{icon}</span>
        <span style={{ fontWeight: 800, fontSize: 13, color: C.purple,
                        textTransform: 'uppercase' as const, letterSpacing: '0.06em' }}>
          {label} — {title}
        </span>
      </div>
      <div style={{ fontSize: 13, color: C.dark, lineHeight: 1.8 }}>{children}</div>
    </div>
  )
}

function ABTBar({ t }: { t: T }) {
  return (
    <div style={{
      display: 'flex', gap: 0, borderRadius: 10, overflow: 'hidden',
      border: `1px solid ${C.accent}`, margin: '24px 0', fontSize: 12,
    }}>
      {[
        { label: t('story.abtAndLabel'), color: C.teal,   bg: '#ECFEFF', text: t('story.abtAndText') },
        { label: t('story.abtButLabel'), color: C.warn,   bg: C.warnL,   text: t('story.abtButText') },
        { label: t('story.abtThereforeLabel'), color: C.green, bg: C.greenL, text: t('story.abtThereforeText') },
      ].map(item => (
        <div key={item.label} style={{ flex: 1, background: item.bg, padding: '12px 16px' }}>
          <div style={{ fontWeight: 900, fontSize: 13, color: item.color,
                         letterSpacing: '0.1em', marginBottom: 6 }}>{item.label}</div>
          <div style={{ color: C.dark, lineHeight: 1.6 }}>{item.text}</div>
        </div>
      ))}
    </div>
  )
}

function Stat({ number, label, sub }: { number: string; label: string; sub?: string }) {
  return (
    <div style={{ textAlign: 'center' as const, padding: '16px 12px' }}>
      <div style={{ fontSize: 28, fontWeight: 900, color: C.accent, lineHeight: 1 }}>{number}</div>
      <div style={{ fontSize: 12, fontWeight: 700, color: C.dark, marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

// ── child mode ─────────────────────────────────────────────────────────────────

function ChildStory({ t }: { t: T }) {
  const sections = [
    {
      emoji: '🏗️', title: t('story.childProblemTitle'),
      color: '#E53E3E', bg: '#FFF5F5',
      text: t('story.childProblemText'),
    },
    {
      emoji: '🎯', title: t('story.childRobotTitle'),
      color: C.accent, bg: C.accentL,
      text: t('story.childRobotText'),
    },
    {
      emoji: '🐜', title: t('story.childAntTitle'),
      color: C.purple, bg: C.purpleL,
      text: t('story.childAntText'),
    },
    {
      emoji: '🔦', title: t('story.childFlashlightsTitle'),
      color: C.teal, bg: '#ECFEFF',
      text: t('story.childFlashlightsText'),
    },
    {
      emoji: '🔬', title: t('story.childInstrumentTitle'),
      color: C.green, bg: C.greenL,
      text: t('story.childInstrumentText'),
    },
    {
      emoji: '🗺️', title: t('story.childFakeMapTitle'),
      color: C.warn, bg: C.warnL,
      text: t('story.childFakeMapText'),
    },
    {
      emoji: '🌟', title: t('story.childMeaningTitle'),
      color: '#805AD5', bg: C.purpleL,
      text: t('story.childMeaningText'),
    },
  ]

  return (
    <div style={{ maxWidth: 760 }}>
      <div style={{
        background: '#FFF9C4', border: '2px solid #F9A825',
        borderRadius: 16, padding: '20px 24px', marginBottom: 28,
        fontSize: 15, color: C.dark, lineHeight: 1.9,
      }}>
        <div style={{ fontSize: 20, fontWeight: 900, marginBottom: 12 }}>
          🎓 {t('story.childIntroTitle')}
        </div>
        <p>{t('story.childIntroBody')}</p>
      </div>

      {sections.map((section, i) => (
        <div key={i} style={{
          background: section.bg, border: `1.5px solid ${section.color}`,
          borderRadius: 12, padding: '18px 22px', marginBottom: 16,
        }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 28 }}>{section.emoji}</span>
            <span style={{ fontWeight: 800, fontSize: 15, color: section.color }}>{section.title}</span>
          </div>
          <div style={{ fontSize: 13, color: C.dark, lineHeight: 1.85, whiteSpace: 'pre-line' as const }}>
            {section.text}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── main ───────────────────────────────────────────────────────────────────────

export default function StoryPage() {
  const t = useT()
  const [mode, setMode] = useState<'science' | 'child'>('science')

  const analogyLabel = t('story.analogyLabel')

  return (
    <div style={{ padding: '32px 40px', maxWidth: 900, fontFamily: 'Georgia, "Times New Roman", serif',
                  color: C.dark }}>

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 28, fontFamily: 'Inter,system-ui,sans-serif' }}>
        {([['science', `🔬 ${t('story.modeScience')}`], ['child', `🎈 ${t('story.modeChild')}`]] as const).map(([m, label]) => (
          <button key={m} onClick={() => setMode(m)} style={{
            padding: '8px 18px', borderRadius: 20, fontSize: 13, fontWeight: 700,
            border: `2px solid ${mode === m ? C.accent : '#E2E8F0'}`,
            background: mode === m ? C.accent : '#fff',
            color: mode === m ? '#fff' : C.neutral,
            cursor: 'pointer', transition: 'all 0.15s',
            fontFamily: 'Inter,system-ui,sans-serif',
          }}>{label}</button>
        ))}
      </div>

      {mode === 'child' ? <ChildStory t={t} /> : (
        <>
          {/* Title */}
          <div style={{ marginBottom: 32 }}>
            <div style={{
              fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', color: C.muted,
              textTransform: 'uppercase' as const, marginBottom: 10,
              fontFamily: 'Inter,system-ui,sans-serif',
            }}>{t('story.eyebrow')}</div>
            <h1 style={{ fontSize: 30, fontWeight: 900, color: C.dark, marginBottom: 14, lineHeight: 1.2,
                          fontFamily: 'Inter,system-ui,sans-serif' }}>
              {t('story.title')}
            </h1>
            <p style={{ fontSize: 15, color: C.neutral, lineHeight: 1.85, maxWidth: 740, marginBottom: 20 }}>
              {t('story.lead')}
            </p>

            {/* ABT summary */}
            <ABTBar t={t} />
          </div>

          {/* ── ACT 1: ESTABLISH ── */}
          <ActHeader act={t('story.act1Act')} title={t('story.act1Title')} sub={t('story.act1Sub')} color={C.teal} />

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act1Para1')}
          </p>
          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act1Para2')}
          </p>

          <PullQuote>
            {t('story.act1Quote')}
          </PullQuote>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act1Para3')}
          </p>
          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act1Para4')}
          </p>

          <Analogy icon="🔧" label={analogyLabel} title={t('story.analogyCylindersTitle')}>
            {t('story.analogyCylindersBody')}
          </Analogy>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act1Para5a')} <strong>{t('story.act1Para5b')}</strong>
          </p>

          {/* Stats row */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
            background: C.accentL, borderRadius: 10, margin: '24px 0',
            fontFamily: 'Inter,system-ui,sans-serif',
          }}>
            <Stat number="30+" label={t('story.statYearsLabel')} sub={t('story.statYearsSub')} />
            <Stat number="6" label={t('story.statDimsLabel')} sub={t('story.statDimsSub')} />
            <Stat number="0" label={t('story.statInstrumentsLabel')} sub={t('story.statInstrumentsSub')} />
            <Stat number="2" label={t('story.statSameAucLabel')} sub={t('story.statSameAucSub')} />
          </div>

          {/* ── ACT 2: PROVE ── */}
          <ActHeader act={t('story.act2Act')} title={t('story.act2Title')} sub={t('story.act2Sub')} color={C.purple} />

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para1')}
          </p>

          <Analogy icon="🐜" label={analogyLabel} title={t('story.analogyAntTitle')}>
            {t('story.analogyAntBody1')}
            <br /><br />
            {t('story.analogyAntBody2')}
          </Analogy>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para2')}
          </p>

          <Analogy icon="🛸" label={analogyLabel} title={t('story.analogyKalmanTitle')}>
            {t('story.analogyKalmanBody1')}
            <br /><br />
            {t('story.analogyKalmanBody2')}
          </Analogy>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para3')}
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para4')}
          </p>

          <PullQuote color={C.warn}>
            {t('story.act2Quote')}
          </PullQuote>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para5')}
          </p>

          <Analogy icon="⚖️" label={analogyLabel} title={t('story.analogyScaleTitle')}>
            {t('story.analogyScaleBody')}
          </Analogy>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para6')}
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act2Para7')}
          </p>

          <Analogy icon="🗺️" label={analogyLabel} title={t('story.analogyFakeMapTitle')}>
            {t('story.analogyFakeMapBody1')}
            <br /><br />
            {t('story.analogyFakeMapBody2')}
          </Analogy>

          {/* ── ACT 3: CONVINCE ── */}
          <ActHeader act={t('story.act3Act')} title={t('story.act3Title')} sub={t('story.act3Sub')} color={C.green} />

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act3Para1')}
          </p>

          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
            gap: 12, margin: '24px 0', fontFamily: 'Inter,system-ui,sans-serif',
          }}>
            {[
              { label: t('story.resultRealLabel'), value: '+0.053', sub: t('story.resultRealSub'), color: C.green },
              { label: t('story.resultShuffledLabel'), value: '≈ 0', sub: t('story.resultShuffledSub'), color: C.muted },
              { label: t('story.resultPLabel'), value: '< 0.01', sub: t('story.resultPSub'), color: C.accent },
            ].map(s => (
              <div key={s.label} style={{
                border: `1.5px solid ${s.color}`, borderRadius: 10, padding: '16px',
                textAlign: 'center' as const, background: `${s.color}10`,
              }}>
                <div style={{ fontSize: 26, fontWeight: 900, color: s.color }}>{s.value}</div>
                <div style={{ fontWeight: 700, fontSize: 12, color: C.dark, marginTop: 4 }}>{s.label}</div>
                <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{s.sub}</div>
              </div>
            ))}
          </div>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act3Para2')}
          </p>

          <PullQuote color={C.green}>
            {t('story.act3Quote')}
          </PullQuote>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act3Para3')}
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act3Para4')}
          </p>

          <Analogy icon="🔭" label={analogyLabel} title={t('story.analogyTelescopeTitle')}>
            {t('story.analogyTelescopeBody1')}
            <br /><br />
            {t('story.analogyTelescopeBody2')}
          </Analogy>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 18 }}>
            {t('story.act3Para5')}
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.95, marginBottom: 24 }}>
            {t('story.act3Para6')}
          </p>

          <div style={{
            background: C.dark, color: '#E2E8F0', borderRadius: 12,
            padding: '24px 28px', fontFamily: 'Inter,system-ui,sans-serif',
            lineHeight: 1.8, fontSize: 13,
          }}>
            <div style={{ fontWeight: 900, fontSize: 16, color: '#fff', marginBottom: 14 }}>
              {t('story.summaryTitle')}
            </div>
            <p style={{ margin: '0 0 12px' }}>
              <span style={{ color: '#67E8F9', fontWeight: 700 }}>{t('story.abtAndLabel')}</span> — {t('story.summaryAnd')}
            </p>
            <p style={{ margin: '0 0 12px' }}>
              <span style={{ color: '#FCD34D', fontWeight: 700 }}>{t('story.abtButLabel')}</span> — {t('story.summaryBut')}
            </p>
            <p style={{ margin: '0' }}>
              <span style={{ color: '#4ADE80', fontWeight: 700 }}>{t('story.abtThereforeLabel')}</span> — {t('story.summaryTherefore')}
            </p>
          </div>
        </>
      )}

      <NextSteps />
    </div>
  )
}
