import { describe, expect, it } from 'vitest'

import { formatRemaining } from './formatRemaining'

describe('formatRemaining', () => {
  it('shows minutes and seconds below one hour', () => {
    expect(formatRemaining(59_000)).toBe('00:59')
    expect(formatRemaining(3_599_000)).toBe('59:59')
  })

  it('shows hours when at least one hour remains', () => {
    expect(formatRemaining(3_600_000)).toBe('01:00:00')
    expect(formatRemaining(3_661_000)).toBe('01:01:01')
  })

  it('shows days when at least one day remains', () => {
    expect(formatRemaining(86_400_000)).toBe('01:00:00:00')
    expect(formatRemaining(2 * 86_400_000 + 3_661_000)).toBe('02:01:01:01')
  })

  it('rounds up fractional seconds and clamps expired timers', () => {
    expect(formatRemaining(3_599_001)).toBe('01:00:00')
    expect(formatRemaining(-1_000)).toBe('00:00')
  })
})
