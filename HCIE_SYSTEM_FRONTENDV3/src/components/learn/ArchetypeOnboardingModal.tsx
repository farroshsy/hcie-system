'use client'

/**
 * 8-question self-report onboarding for learner archetype profiling.
 *
 * Slice 5b design note: scores are stored for *observational* analysis only —
 * they never feed back into MAB scoring. The instructor dashboard uses them
 * for Archetype × Concept research.
 */

import { useState } from 'react'
import { useT } from '@/contexts/language_context'

const ONBOARDING_KEY = 'hcie_archetype_onboarded'

export function hasCompletedOnboarding(): boolean {
  try {
    return localStorage.getItem(ONBOARDING_KEY) === '1'
  } catch {
    return false
  }
}

export function markOnboardingComplete(skipped = false): void {
  try {
    localStorage.setItem(ONBOARDING_KEY, skipped ? 'skipped' : '1')
  } catch { /* ignore */ }
}

type Option = { id: string; labelKey: string; labelFallback: string; scores: Record<string, number> }

type Question = {
  id: string
  axis: 'vark' | 'behav' | 'motiv'
  titleKey: string
  titleFallback: string
  options: Option[]
}

const QUESTIONS: Question[] = [
  {
    id: 'q1', axis: 'vark',
    titleKey: 'learn.archetype.q1',
    titleFallback: 'When learning something new, what helps you MOST?',
    options: [
      { id: 'visual', labelKey: 'learn.archetype.q1a', labelFallback: 'Charts, diagrams, or videos', scores: { visual: 1 } },
      { id: 'auditory', labelKey: 'learn.archetype.q1b', labelFallback: 'Listening to someone explain', scores: { auditory: 1 } },
      { id: 'reading', labelKey: 'learn.archetype.q1c', labelFallback: 'Reading text or notes', scores: { reading: 1 } },
      { id: 'kinesthetic', labelKey: 'learn.archetype.q1d', labelFallback: 'Trying it hands-on', scores: { kinesthetic: 1 } },
    ],
  },
  {
    id: 'q2', axis: 'vark',
    titleKey: 'learn.archetype.q2',
    titleFallback: 'When revising for a test, you usually…',
    options: [
      { id: 'visual', labelKey: 'learn.archetype.q2a', labelFallback: 'Draw mind maps or highlight notes', scores: { visual: 1 } },
      { id: 'auditory', labelKey: 'learn.archetype.q2b', labelFallback: 'Explain it aloud to someone', scores: { auditory: 1 } },
      { id: 'reading', labelKey: 'learn.archetype.q2c', labelFallback: 'Re-read the textbook or articles', scores: { reading: 1 } },
      { id: 'kinesthetic', labelKey: 'learn.archetype.q2d', labelFallback: 'Do practice problems', scores: { kinesthetic: 1 } },
    ],
  },
  {
    id: 'q3', axis: 'behav',
    titleKey: 'learn.archetype.q3',
    titleFallback: 'In a group lesson, you tend to be…',
    options: [
      { id: 'participant', labelKey: 'learn.archetype.q3a', labelFallback: 'Actively contributing and asking questions', scores: { participant: 1 } },
      { id: 'passenger', labelKey: 'learn.archetype.q3b', labelFallback: 'Present but doing only what is required', scores: { passenger: 1 } },
      { id: 'partner', labelKey: 'learn.archetype.q3c', labelFallback: 'Helping classmates understand', scores: { partner: 1 } },
      { id: 'pathfinder', labelKey: 'learn.archetype.q3d', labelFallback: 'Exploring ahead on your own', scores: { pathfinder: 1 } },
    ],
  },
  {
    id: 'q4', axis: 'behav',
    titleKey: 'learn.archetype.q4',
    titleFallback: 'When instructions feel unclear, you…',
    options: [
      { id: 'pathfinder', labelKey: 'learn.archetype.q4a', labelFallback: 'Figure out a different approach yourself', scores: { pathfinder: 1 } },
      { id: 'pirate', labelKey: 'learn.archetype.q4b', labelFallback: 'Question or test the rules', scores: { pirate: 1 } },
      { id: 'participant', labelKey: 'learn.archetype.q4c', labelFallback: 'Ask the instructor to clarify', scores: { participant: 1 } },
      { id: 'prisoner', labelKey: 'learn.archetype.q4d', labelFallback: 'Do the minimum and move on', scores: { prisoner: 1 } },
    ],
  },
  {
    id: 'q5', axis: 'behav',
    titleKey: 'learn.archetype.q5',
    titleFallback: 'Your attitude toward mandatory tasks is…',
    options: [
      { id: 'participant', labelKey: 'learn.archetype.q5a', labelFallback: 'Engaged — I want to do them well', scores: { participant: 1 } },
      { id: 'partner', labelKey: 'learn.archetype.q5b', labelFallback: 'Collaborative — I help others finish', scores: { partner: 1 } },
      { id: 'passenger', labelKey: 'learn.archetype.q5c', labelFallback: 'Compliant — I finish but without deep focus', scores: { passenger: 1 } },
      { id: 'prisoner', labelKey: 'learn.archetype.q5d', labelFallback: 'Resistant — I do the bare minimum', scores: { prisoner: 1 } },
    ],
  },
  {
    id: 'q6', axis: 'motiv',
    titleKey: 'learn.archetype.q6',
    titleFallback: 'You learn best when…',
    options: [
      { id: 'social', labelKey: 'learn.archetype.q6a', labelFallback: 'Working with classmates', scores: { social: 1 } },
      { id: 'solitary', labelKey: 'learn.archetype.q6b', labelFallback: 'Studying alone at your own pace', scores: { solitary: 1 } },
      { id: 'logical', labelKey: 'learn.archetype.q6c', labelFallback: 'Understanding the why and how', scores: { logical: 1 } },
      { id: 'explorer', labelKey: 'learn.archetype.q6d', labelFallback: 'Discovering something new on your own', scores: { explorer: 1 } },
    ],
  },
  {
    id: 'q7', axis: 'motiv',
    titleKey: 'learn.archetype.q7',
    titleFallback: 'What motivates you most to study computer science?',
    options: [
      { id: 'logical', labelKey: 'learn.archetype.q7a', labelFallback: 'Solving puzzles and understanding systems', scores: { logical: 1 } },
      { id: 'explorer', labelKey: 'learn.archetype.q7b', labelFallback: 'Building skills for your future', scores: { explorer: 1 } },
      { id: 'social', labelKey: 'learn.archetype.q7c', labelFallback: 'Creating things others will use', scores: { social: 1 } },
      { id: 'solitary', labelKey: 'learn.archetype.q7d', labelFallback: 'Personal curiosity and mastery', scores: { solitary: 1 } },
    ],
  },
  {
    id: 'q8', axis: 'vark',
    titleKey: 'learn.archetype.q8',
    titleFallback: 'A concept "clicks" for you when you…',
    options: [
      { id: 'visual', labelKey: 'learn.archetype.q8a', labelFallback: 'See a diagram or demo', scores: { visual: 1 } },
      { id: 'auditory', labelKey: 'learn.archetype.q8b', labelFallback: 'Hear a clear explanation', scores: { auditory: 1 } },
      { id: 'reading', labelKey: 'learn.archetype.q8c', labelFallback: 'Read a well-written explanation', scores: { reading: 1 } },
      { id: 'kinesthetic', labelKey: 'learn.archetype.q8d', labelFallback: 'Build or code it yourself', scores: { kinesthetic: 1 } },
    ],
  },
]

function normalize(scores: Record<string, number>, keys: string[]): Record<string, number> {
  const out: Record<string, number> = {}
  for (const k of keys) out[k] = scores[k] ?? 0
  const total = Object.values(out).reduce((a, b) => a + b, 0)
  if (total <= 0) {
    const n = keys.length
    return Object.fromEntries(keys.map(k => [k, Math.round(100 / n) / 100]))
  }
  return Object.fromEntries(keys.map(k => [k, Math.round((out[k] / total) * 1000) / 1000]))
}

export function buildProfileFromAnswers(answers: Record<string, string>) {
  const vark: Record<string, number> = { visual: 0, auditory: 0, reading: 0, kinesthetic: 0 }
  const behav: Record<string, number> = {
    participant: 0, passenger: 0, partner: 0, pathfinder: 0, pirate: 0, prisoner: 0,
  }
  const motiv: Record<string, number> = { social: 0, solitary: 0, logical: 0, explorer: 0 }

  for (const q of QUESTIONS) {
    const chosen = answers[q.id]
    if (!chosen) continue
    const opt = q.options.find(o => o.id === chosen)
    if (!opt) continue
    const target = q.axis === 'vark' ? vark : q.axis === 'behav' ? behav : motiv
    for (const [k, v] of Object.entries(opt.scores)) {
      target[k] = (target[k] ?? 0) + v
    }
  }

  return {
    vark_scores: normalize(vark, ['visual', 'auditory', 'reading', 'kinesthetic']),
    behav_scores: normalize(behav, ['participant', 'passenger', 'partner', 'pathfinder', 'pirate', 'prisoner']),
    motiv_scores: normalize(motiv, ['social', 'solitary', 'logical', 'explorer']),
    source: 'self_report' as const,
    confidence: 0.7,
    raw_responses: answers,
  }
}

interface Props {
  open: boolean
  onComplete: () => void
  onSkip: () => void
  onSubmit: (profile: ReturnType<typeof buildProfileFromAnswers>) => Promise<void>
}

export function ArchetypeOnboardingModal({ open, onComplete, onSkip, onSubmit }: Props) {
  const t = useT()
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  if (!open) return null

  const q = QUESTIONS[step]
  const progress = ((step + 1) / QUESTIONS.length) * 100

  const pick = (optionId: string) => {
    const next = { ...answers, [q.id]: optionId }
    setAnswers(next)
    if (step < QUESTIONS.length - 1) {
      setTimeout(() => setStep(s => s + 1), 180)
    }
  }

  const finish = async () => {
    setSubmitting(true)
    try {
      await onSubmit(buildProfileFromAnswers(answers))
      markOnboardingComplete(false)
      onComplete()
    } catch {
      markOnboardingComplete(false)
      onComplete()
    } finally {
      setSubmitting(false)
    }
  }

  const handleSkip = () => {
    markOnboardingComplete(true)
    onSkip()
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(15,23,42,0.55)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 16, maxWidth: 520, width: '100%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden',
      }}>
        <div style={{ padding: '20px 24px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#6C3483', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {t('learn.archetype.title', 'Learning style survey')}
            </div>
            <button type="button" onClick={handleSkip}
              style={{ background: 'none', border: 'none', color: '#A0AEC0', fontSize: 12, cursor: 'pointer' }}>
              {t('learn.archetype.skip', 'Skip')} →
            </button>
          </div>
          <p style={{ fontSize: 12, color: '#718096', margin: '0 0 12px', lineHeight: 1.5 }}>
            {t('learn.archetype.subtitle',
              '8 quick questions (~90 sec). Helps us understand how you learn — does not change which tasks you get.')}
          </p>
          <div style={{ height: 4, background: '#EDF2F7', borderRadius: 2, marginBottom: 16 }}>
            <div style={{ height: '100%', width: `${progress}%`, background: '#6C3483', borderRadius: 2, transition: 'width 0.2s' }} />
          </div>
          <div style={{ fontSize: 10, color: '#A0AEC0', marginBottom: 6 }}>
            {step + 1} / {QUESTIONS.length}
          </div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: '#1A2332', margin: '0 0 16px', lineHeight: 1.4 }}>
            {t(q.titleKey, q.titleFallback)}
          </h2>
        </div>

        <div style={{ padding: '0 24px 20px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {q.options.map(opt => {
            const selected = answers[q.id] === opt.id
            return (
              <button key={opt.id} type="button" onClick={() => pick(opt.id)}
                style={{
                  textAlign: 'left', padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                  border: selected ? '2px solid #6C3483' : '1px solid #E2E8F0',
                  background: selected ? '#F5EEF8' : '#fff',
                  fontSize: 13, color: '#2D3748', fontWeight: selected ? 600 : 400,
                  transition: 'all 0.15s',
                }}>
                {t(opt.labelKey, opt.labelFallback)}
              </button>
            )
          })}
        </div>

        <div style={{ padding: '12px 24px 20px', borderTop: '1px solid #EDF2F7', display: 'flex', gap: 8, justifyContent: 'space-between' }}>
          <button type="button" disabled={step === 0}
            onClick={() => setStep(s => Math.max(0, s - 1))}
            style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #E2E8F0', background: '#fff', fontSize: 12, cursor: step === 0 ? 'default' : 'pointer', opacity: step === 0 ? 0.4 : 1 }}>
            ← {t('common.back', 'Back')}
          </button>
          {step === QUESTIONS.length - 1 ? (
            <button type="button" disabled={!answers[q.id] || submitting} onClick={finish}
              style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: '#6C3483', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', opacity: (!answers[q.id] || submitting) ? 0.5 : 1 }}>
              {submitting ? '…' : t('learn.archetype.finish', 'Finish')}
            </button>
          ) : (
            <button type="button" disabled={!answers[q.id]}
              onClick={() => setStep(s => s + 1)}
              style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: '#6C3483', color: '#fff', fontSize: 13, fontWeight: 700, cursor: answers[q.id] ? 'pointer' : 'default', opacity: answers[q.id] ? 1 : 0.5 }}>
              {t('common.next', 'Next')} →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
