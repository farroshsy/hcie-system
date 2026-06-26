import { trace, context, SpanStatusCode, Span } from '@opentelemetry/api'

// Initialize OpenTelemetry for frontend
export function initTelemetry() {
  if (typeof window === 'undefined') return

  // Simple initialization - the backend otel-collector will receive traces
  console.log('[OpenTelemetry] Frontend tracing initialized')
}

// Helper function to create a span
export function createSpan(name: string, fn: (span: Span) => void) {
  const tracer = trace.getTracer('hcie-frontend')
  const span = tracer.startSpan(name)

  try {
    fn(span)
  } catch (error) {
    span.recordException(error as Error)
    span.setStatus({ code: SpanStatusCode.ERROR, message: (error as Error).message })
    throw error
  } finally {
    span.end()
  }
}

// Send custom metrics to otel-collector
// Only fires when NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT is explicitly configured.
// Silently skips when the collector is absent so the console stays clean.
export function sendMetric(name: string, value: number, attributes: Record<string, string> = {}) {
  if (typeof window === 'undefined') return

  const endpoint = process.env.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT
  // No endpoint configured → skip silently. Avoids spamming the console
  // when the otel-collector container is not running (--profile tracing).
  if (!endpoint) return

  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, value, attributes, timestamp: Date.now() }),
  }).catch(() => {
    // Suppress network errors — collector may be temporarily unavailable.
  })
}

// Track errors with context
export function trackError(error: Error, context: Record<string, string> = {}) {
  const tracer = trace.getTracer('hcie-frontend')
  const span = tracer.startSpan('error')

  span.recordException(error)
  span.setAttributes({
    'error.message': error.message,
    'error.name': error.name,
    'error.stack': error.stack || '',
    ...context,
  })
  span.setStatus({ code: SpanStatusCode.ERROR, message: error.message })
  span.end()

  // Also send as metric for error tracking
  sendMetric('frontend_error', 1, {
    error_type: error.name,
    error_message: error.message,
    ...context,
  })
}

// Track user interactions
export function trackInteraction(name: string, properties: Record<string, string> = {}) {
  const tracer = trace.getTracer('hcie-frontend')
  const span = tracer.startSpan(`interaction.${name}`)

  span.setAttributes(properties)
  span.end()

  sendMetric('user_interaction', 1, {
    interaction_type: name,
    ...properties,
  })
}

