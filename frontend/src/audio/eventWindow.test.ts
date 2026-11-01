import { describe, expect, it } from 'vitest'
import { AudioEventWindow } from './eventWindow'

describe('bounded audio replay window', () => {
  it('expires low traffic entries without waiting for capacity', () => {
    let now = 0
    const events = new AudioEventWindow(2, 100, () => now)
    expect(events.accept('a')).toBe(true)
    expect(events.accept('a')).toBe(false)
    now = 100
    expect(events.accept('a')).toBe(true)
  })
  it('evicts the oldest entry during a burst and retains recent duplicates', () => {
    const events = new AudioEventWindow(2, 100, () => 0)
    events.accept('a'); events.accept('b'); events.accept('c')
    expect(events.accept('b')).toBe(false)
    expect(events.accept('c')).toBe(false)
    expect(events.accept('a')).toBe(true)
  })
})
