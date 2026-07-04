import { describe, expect, it } from 'vitest'

import { buildApiUrl, normalizeBackendUrl } from './backend-url'

describe('backend URL helpers', () => {
  it('normalizes backend roots whether env includes /v3 or not', () => {
    expect(normalizeBackendUrl('http://localhost:8011/v3')).toBe('http://localhost:8011')
    expect(normalizeBackendUrl('http://localhost:8011')).toBe('http://localhost:8011')
    expect(normalizeBackendUrl('http://localhost:8011/')).toBe('http://localhost:8011')
  })

  it('joins V3 paths without duplicating the /v3 prefix', () => {
    expect(buildApiUrl('http://localhost:8011/v3', '/v3/auth/login')).toBe(
      'http://localhost:8011/v3/auth/login',
    )
    expect(buildApiUrl('http://localhost:8011', 'v3/learner/recommend')).toBe(
      'http://localhost:8011/v3/learner/recommend',
    )
  })
})
