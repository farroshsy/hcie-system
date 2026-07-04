'use client'

/**
 * ProvenanceBadge — P4-2 evidence-integrity surface.
 *
 * Every review/evidence panel must visibly declare WHAT data it is showing so a
 * reviewer can tell a live recompute from a frozen export, and can pin a figure
 * to its source run + as-of time. This directly addresses the provenance gap
 * found in the Phase 2 audit: the same experiment_run_id yields different exact
 * statistics at different times (it accreted re-runs), so a bare number with no
 * run_id + as-of is not reproducible. The badge makes the anchor explicit.
 *
 * Reuses the live/static colour convention established in /review/replay.
 */

export type ProvenanceSource = 'live_db' | 'frozen' | 'loading'

export interface ProvenanceBadgeProps {
  /** 'live_db' = recomputed from the running DB now; 'frozen' = sealed static export. */
  source: ProvenanceSource
  /** ISO timestamp the frozen export was generated (the "as-of" of the numbers). */
  generatedAt?: string | null
  /** Canonical experiment run id the figures derive from. */
  runId?: string | null
  /** Row / interaction count behind the statistics (N). */
  n?: number | null
  /** Optional one-line note, e.g. the reproduce command or a caveat. */
  note?: string
}

const STYLES: Record<ProvenanceSource, { bg: string; text: string; border: string; label: string }> = {
  live_db: { bg: '#D5F5E3', text: '#1E8449', border: '#A9DFBF', label: '● Live DB' },
  frozen:  { bg: '#FEF9E7', text: '#7D6008', border: '#F9E79F', label: '○ Frozen export (sealed)' },
  loading: { bg: '#F7FAFC', text: '#718096', border: '#E2E8F0', label: '○ Loading…' },
}

function fmtDate(iso?: string | null): string | null {
  if (!iso) return null
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    return d.toISOString().slice(0, 19).replace('T', ' ') + ' UTC'
  } catch {
    return iso
  }
}

export default function ProvenanceBadge({ source, generatedAt, runId, n, note }: ProvenanceBadgeProps) {
  const s = STYLES[source]
  const asOf = fmtDate(generatedAt)
  return (
    <div
      data-testid="provenance-badge"
      style={{
        display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10,
        padding: '8px 12px', borderRadius: 8, fontSize: 11, lineHeight: 1.5,
        background: s.bg, color: s.text, border: `1px solid ${s.border}`,
        marginBottom: 16,
      }}
    >
      <span style={{ fontWeight: 700, whiteSpace: 'nowrap' }}>{s.label}</span>
      {asOf && (
        <span>
          <strong>as of</strong> {asOf}
        </span>
      )}
      {n != null && (
        <span>
          <strong>N</strong> = {n.toLocaleString()}
        </span>
      )}
      {runId && (
        <span style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
          <strong>run</strong> {runId}
        </span>
      )}
      {source === 'frozen' && (
        <span style={{ opacity: 0.85 }}>
          — sealed snapshot; exact statistics are pinned to this run + time, not the live DB.
        </span>
      )}
      {note && <span style={{ opacity: 0.85 }}>{note}</span>}
    </div>
  )
}
