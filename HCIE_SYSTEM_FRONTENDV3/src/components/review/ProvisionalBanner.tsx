'use client'

/**
 * ProvisionalBanner — pairs with ProvenanceBadge to declare a SCOPE caveat on
 * /review/* pages whose numbers predate the Option-2 sealed re-run. The
 * provenance badge above pins WHICH run + time. This banner answers a different
 * question: is the SCOPE of that run the protocol the hypothesis actually
 * asks for?
 *
 * Removed (or `tone="anchored"`) once the re-run lands and the page is
 * re-pointed at the sealed train-on-few / eval-on-unseen artifact.
 */

import Link from 'next/link'
import { useT } from '@/contexts/language_context'

export type ProvisionalTone = 'provisional' | 'partial' | 'anchored'

export interface ProvisionalBannerProps {
  /** Severity. `provisional` = full scope caveat. `partial` = single-axis caveat.
   *  `anchored` = re-run landed; renders a green confirmation strip instead. */
  tone?: ProvisionalTone
  /** Short headline of the caveat, e.g. "Small-N graph regime". */
  headline: string
  /** One-paragraph explanation of WHY the current numbers are not yet anchored. */
  body: React.ReactNode
  /** Bullet list of what flips after the sealed re-run. */
  flipsAfter?: string[]
}

const TONE_VISUAL: Record<ProvisionalTone, { bg: string; border: string; text: string; tag: string; tagBg: string }> = {
  provisional: { bg: '#FDEDEC', border: '#F5B7B1', text: '#922B21', tag: '#C0392B', tagBg: '#F5B7B1' },
  partial:     { bg: '#FEF9E7', border: '#F9E79F', text: '#7D6008', tag: '#9A7D0A', tagBg: '#F9E79F' },
  anchored:    { bg: '#D5F5E3', border: '#A9DFBF', text: '#1E8449', tag: '#1E8449', tagBg: '#A9DFBF' },
}

const TONE_LABEL_KEY: Record<ProvisionalTone, string> = {
  provisional: 'provisional.label',
  partial:     'provisional.partial',
  anchored:    'provisional.anchored',
}

export default function ProvisionalBanner({
  tone = 'provisional', headline, body, flipsAfter,
}: ProvisionalBannerProps) {
  const tx = useT()
  const t = TONE_VISUAL[tone]
  const label = tx(TONE_LABEL_KEY[tone])
  return (
    <div
      data-testid="provisional-banner"
      style={{
        background: t.bg, border: `1px solid ${t.border}`, color: t.text,
        borderRadius: 10, padding: '14px 18px', marginBottom: 16, lineHeight: 1.55,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
        <span style={{
          fontSize: 10, fontWeight: 800, letterSpacing: '0.06em',
          color: t.tag, background: t.tagBg, padding: '3px 8px', borderRadius: 10,
          textTransform: 'uppercase', whiteSpace: 'nowrap',
        }}>
          {label}
        </span>
        <span style={{ fontSize: 13, fontWeight: 800 }}>{headline}</span>
      </div>
      <div style={{ fontSize: 12, marginBottom: flipsAfter?.length ? 8 : 0 }}>
        {body}
      </div>
      {flipsAfter && flipsAfter.length > 0 && (
        <div style={{ fontSize: 11, opacity: 0.92 }}>
          <strong>{tx('provisional.flipsAfter')}:</strong>
          <ul style={{ margin: '4px 0 0 18px', padding: 0 }}>
            {flipsAfter.map(item => <li key={item} style={{ marginBottom: 2 }}>{item}</li>)}
          </ul>
        </div>
      )}
      {tone !== 'anchored' && (
        <div style={{ marginTop: 8, fontSize: 11, opacity: 0.85 }}>
          <Link href="/infrastructure" style={{ color: 'inherit', textDecoration: 'underline' }}>
            /{tx('nav.infrastructure').toLowerCase()} → {tx('infrastructure.sealedRuns')}
          </Link>
        </div>
      )}
    </div>
  )
}
