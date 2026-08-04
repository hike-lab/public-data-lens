// 계약 버전 게이팅(P0) — 구버전 서버에서 v1.5 기능 진입점을 숨긴다
import { describe, it, expect } from 'vitest'
import { supportsPlan } from './api.js'

describe('supportsPlan', () => {
  const st = (v) => ({ meta: { schemaVersion: v } })

  it('1.5.0 이상에서만 true', () => {
    expect(supportsPlan(st('1.4.0'))).toBe(false)
    expect(supportsPlan(st('1.5.0'))).toBe(true)
    expect(supportsPlan(st('1.6.0'))).toBe(true)
    expect(supportsPlan(st('2.0.0'))).toBe(true)
  })

  it('status 부재·버전 부재면 false(안전한 기본값)', () => {
    expect(supportsPlan(null)).toBe(false)
    expect(supportsPlan({})).toBe(false)
    expect(supportsPlan({ meta: {} })).toBe(false)
  })
})
