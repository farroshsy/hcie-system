'use client'

/**
 * GovernanceTelemetryPanel
 *
 * Surfaces the FINAL backend's research-grade learner telemetry directly
 * in the UI:
 *   - Ensemble weights (Lyapunov / Bayesian / Kalman)
 *   - 6D JT attribution shares (ΔM, T_realized, T_prospective, C, U, Z)
 *   - Adaptive Dimension Controller (ADC) interpretive verdict per
 *     dimension, derived client-side from the JT-attribution payload.
 *
 * Backed by `/v3/research/learner/governance/ensemble-weights` and
 * `/v3/research/learner/jt-attribution` — see
 * `research_validation/docs/FRONTEND_API_COVERAGE_AUDIT.md` Group 1.
 *
 * This component is intentionally read-only. It demonstrates the
 * "operational substrate" claim in Chapter 4.10.6 without altering any
 * runtime state.
 */

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { useMemo } from 'react'

interface EnsembleWeights {
  lyapunov?: number
  bayesian?: number
  kalman?: number
  [k: string]: number | undefined
}

interface JtAttribution {
  delta_m?: number
  transfer_realized?: number
  transfer_prospective?: number
  challenge?: number
  uncertainty?: number
  zpd?: number
  [k: string]: number | undefined
}

const DIMENSION_LABELS: Record<string, string> = {
  delta_m: 'ΔM (mastery gain)',
  transfer_realized: 'T_realized',
  transfer_prospective: 'T_prospective',
  challenge: 'Challenge',
  uncertainty: 'Uncertainty',
  zpd: 'ZPD',
}

const ACTIVATION_FLOOR = 0.01
const COLLAPSE_DOMINANCE = 4.0

interface DimensionVerdict {
  dimension: string
  contribution: number
  active: boolean
  dormant: boolean
  suppressed: boolean
  rationale: string
}

function classifyDimensions(attribution: JtAttribution): DimensionVerdict[] {
  const entries = Object.keys(DIMENSION_LABELS).map((k) => ({
    dimension: k,
    contribution: Number(attribution[k] ?? 0),
  }))
  const maxContribution = Math.max(0, ...entries.map((e) => e.contribution))
  return entries.map((e) => {
    const dormant = e.contribution < ACTIVATION_FLOOR
    const suppressed =
      !dormant &&
      maxContribution > 0 &&
      e.contribution > 0 &&
      maxContribution / Math.max(e.contribution, 1e-9) > COLLAPSE_DOMINANCE
    const active = !dormant && !suppressed
    let rationale: string
    if (dormant) {
      rationale = 'dormant — substrate signal below activation floor'
    } else if (suppressed) {
      rationale = 'suppressed — dominated by another dimension'
    } else {
      rationale = 'active — substrate signal and contribution engaged'
    }
    return { ...e, active, dormant, suppressed, rationale }
  })
}

function tone(verdict: DimensionVerdict): string {
  if (verdict.active) return 'bg-green-50 border-green-200 text-green-900'
  if (verdict.suppressed) return 'bg-orange-50 border-orange-200 text-orange-900'
  return 'bg-gray-100 border-gray-200 text-gray-700'
}

interface GovernanceTelemetryPanelProps {
  userId: string
}

export function GovernanceTelemetryPanel({ userId }: GovernanceTelemetryPanelProps) {
  const enabled = Boolean(userId)

  const weightsQuery = useQuery({
    queryKey: ['v3-research-ensemble-weights', userId],
    queryFn: () => apiClient.getResearchEnsembleWeights(userId),
    enabled,
    retry: 1,
  })

  const attributionQuery = useQuery({
    queryKey: ['v3-research-jt-attribution', userId],
    queryFn: () => apiClient.getResearchJtAttribution(userId),
    enabled,
    retry: 1,
  })

  const weights: EnsembleWeights = useMemo(() => {
    const raw = weightsQuery.data
    if (!raw || typeof raw !== 'object') return {}
    return (raw as { weights?: EnsembleWeights }).weights ?? (raw as EnsembleWeights)
  }, [weightsQuery.data])

  const attribution: JtAttribution = useMemo(() => {
    const raw = attributionQuery.data
    if (!raw || typeof raw !== 'object') return {}
    return (
      (raw as { attribution?: JtAttribution }).attribution ??
      (raw as { jt_attribution?: JtAttribution }).jt_attribution ??
      (raw as JtAttribution)
    )
  }, [attributionQuery.data])

  const verdicts = useMemo(() => classifyDimensions(attribution), [attribution])

  if (!enabled) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Governance Telemetry</h2>
        <p className="text-gray-600">
          Enter a user ID above to inspect ensemble weights, 6D JT
          attribution, and Adaptive Dimension Controller verdicts.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-6">
      <header>
        <h2 className="text-xl font-bold text-gray-900">Governance Telemetry</h2>
        <p className="text-sm text-gray-600 mt-1">
          Live data from <code>/v3/research/learner/*</code>. ADC verdicts
          computed client-side per <code>analyze_governance_ecology.py</code>{' '}
          thresholds ({`α_floor=${ACTIVATION_FLOOR}`}, {`ρ_coll=${COLLAPSE_DOMINANCE}`}).
        </p>
      </header>

      <section>
        <h3 className="font-semibold text-gray-800 mb-3">Ensemble weights</h3>
        {weightsQuery.isLoading && <p className="text-gray-500">Loading…</p>}
        {weightsQuery.isError && (
          <p className="text-red-600 text-sm">
            Could not load ensemble weights for user <code>{userId}</code>.
          </p>
        )}
        {!weightsQuery.isLoading && !weightsQuery.isError && (
          <div className="grid grid-cols-3 gap-3">
            {(['lyapunov', 'bayesian', 'kalman'] as const).map((learner) => (
              <div key={learner} className="bg-blue-50 rounded-lg p-3 border border-blue-100">
                <p className="text-xs uppercase tracking-wide text-blue-700 font-semibold">
                  {learner}
                </p>
                <p className="text-2xl font-bold text-blue-900">
                  {(weights[learner] ?? 0).toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 className="font-semibold text-gray-800 mb-3">
          6D JT attribution & ADC activation verdict
        </h3>
        {attributionQuery.isLoading && <p className="text-gray-500">Loading…</p>}
        {attributionQuery.isError && (
          <p className="text-red-600 text-sm">
            Could not load JT attribution for user <code>{userId}</code>.
          </p>
        )}
        {!attributionQuery.isLoading && !attributionQuery.isError && (
          <div className="space-y-2">
            {verdicts.map((v) => (
              <div
                key={v.dimension}
                className={`flex items-center justify-between rounded-lg border px-4 py-3 ${tone(v)}`}
              >
                <div>
                  <p className="font-semibold">{DIMENSION_LABELS[v.dimension] ?? v.dimension}</p>
                  <p className="text-xs opacity-80">{v.rationale}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-mono font-bold">{v.contribution.toFixed(4)}</p>
                  <p className="text-xs uppercase tracking-wide opacity-80">
                    {v.active ? 'active' : v.suppressed ? 'suppressed' : 'dormant'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default GovernanceTelemetryPanel
