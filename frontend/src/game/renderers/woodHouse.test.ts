import { describe, expect, it } from 'vitest'

import { woodHouseModelLevel, woodHouseModelState } from './woodHouse'

describe('wood house renderer', () => {
  it('clamps model level to available wood house variants', () => {
    expect(woodHouseModelLevel(0)).toBe(1)
    expect(woodHouseModelLevel(4)).toBe(4)
    expect(woodHouseModelLevel(9)).toBe(6)
  })

  it('chooses construction, damaged and ruined states from health threshold', () => {
    expect(woodHouseModelState({ status: 'construction', state: 'building', health: 1200 })).toBe('construction')
    expect(woodHouseModelState({ status: 'active', state: 'damaged', health: 1200, maxHealth: 1200 })).toBe('active')
    expect(woodHouseModelState({ status: 'active', state: 'active', health: 240, maxHealth: 1200 })).toBe('damaged')
    expect(woodHouseModelState({ status: 'active', state: 'ruined', health: 1200 })).toBe('ruined')
  })
})
