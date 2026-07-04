'use client'

import { useEffect } from 'react'
import { onCLS, onLCP, onFCP, onTTFB, onINP, Metric } from 'web-vitals'
import { sendMetric } from '@/lib/telemetry'

export function WebVitals() {
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Core Web Vitals
    onCLS((metric: Metric) => {
      sendMetric('web_vitals_cls', metric.value, {
        name: metric.name,
        rating: metric.rating,
        delta: metric.delta.toString(),
      })
    })

    onINP((metric: Metric) => {
      sendMetric('web_vitals_inp', metric.value, {
        name: metric.name,
        rating: metric.rating,
        delta: metric.delta.toString(),
      })
    })

    onLCP((metric: Metric) => {
      sendMetric('web_vitals_lcp', metric.value, {
        name: metric.name,
        rating: metric.rating,
        delta: metric.delta.toString(),
      })
    })

    // Additional Web Vitals
    onFCP((metric: Metric) => {
      sendMetric('web_vitals_fcp', metric.value, {
        name: metric.name,
        rating: metric.rating,
        delta: metric.delta.toString(),
      })
    })

    onTTFB((metric: Metric) => {
      sendMetric('web_vitals_ttfb', metric.value, {
        name: metric.name,
        rating: metric.rating,
        delta: metric.delta.toString(),
      })
    })
  }, [])

  return null
}
