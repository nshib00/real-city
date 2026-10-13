import { describe, expect, it } from 'vitest'

import { mineModelLevel, mineModelState } from './mine'

describe('mine renderer', () => {
  it('clamps model level to generated mine variants', () => {
    expect(mineModelLevel(0)).toBe(1)
    expect(mineModelLevel(1)).toBe(1)
    expect(mineModelLevel(3)).toBe(3)
    expect(mineModelLevel(12)).toBe(12)
    expect(mineModelLevel(99)).toBe(12)
  })

  it('chooses construction, damaged and ruined states from health threshold', () => {
    expect(mineModelState({ status: 'construction', state: 'building', health: 100 })).toBe('construction')
    expect(mineModelState({ status: 'active', state: 'damaged', health: 100, maxHealth: 100 })).toBe('active')
    expect(mineModelState({ status: 'active', state: 'active', health: 35, maxHealth: 176 })).toBe('damaged')
    expect(mineModelState({ status: 'active', state: 'ruined', health: 100 })).toBe('ruined')
  })
})
