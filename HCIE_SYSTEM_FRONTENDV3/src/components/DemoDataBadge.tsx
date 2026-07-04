/**
 * Visible "demo / not live" banner for surfaces that show ILLUSTRATIVE placeholder numbers
 * (not derived from a sealed run or the viewer's real learning data). Integrity guard for the
 * Tier-B fabricated surfaces (/profile Intelligence, /concepts, /research) — see
 * FRONTEND_GROUNDING_PLAN.md. Replace with real data wiring when the endpoint is grounded, then
 * remove the badge.
 */
export function DemoDataBadge({ what }: { what?: string }) {
  return (
    <div
      role="note"
      style={{
        margin: '0 0 14px',
        padding: '9px 14px',
        borderRadius: 8,
        background: '#FEF3C7',
        border: '1px solid #FCD34D',
        color: '#92400E',
        fontSize: 12.5,
        fontWeight: 600,
        display: 'flex',
        gap: 8,
        alignItems: 'center',
        lineHeight: 1.45,
      }}
    >
      <span aria-hidden="true">⚠</span>
      <span>
        Illustrative / demo — not live data{what ? ` (${what})` : ''}. These figures are placeholders
        for layout; they are NOT derived from your learning data or a sealed run.
      </span>
    </div>
  )
}
