import { describe, expect, it } from 'vitest'

import { sandQuarryModelLevel, sandQuarryModelState } from './sandQuarry'

describe('sand quarry renderer', () => {
  it('clamps model level to generated sand quarry variants', () => {
    expect(sandQuarryModelLevel(0)).toBe(1)
    expect(sandQuarryModelLevel(1)).toBe(1)
    expect(sandQuarryModelLevel(11)).toBe(11)
    expect(sandQuarryModelLevel(99)).toBe(11)
  })

  it('chooses construction, damaged and ruined states from health threshold', () => {
    expect(sandQuarryModelState({ status: 'construction', state: 'building', health: 100 })).toBe('construction')
    expect(sandQuarryModelState({ status: 'active', state: 'damaged', health: 100, maxHealth: 100 })).toBe('active')
    expect(sandQuarryModelState({ status: 'active', state: 'active', health: 16, maxHealth: 84 })).toBe('damaged')
    expect(sandQuarryModelState({ status: 'active', state: 'ruined', health: 100 })).toBe('ruined')
  })
})
