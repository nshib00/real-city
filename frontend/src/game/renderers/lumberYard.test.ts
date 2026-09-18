import { describe, expect, it } from 'vitest'

import { lumberYardModelLevel, lumberYardModelState } from './lumberYard'

describe('lumber yard renderer', () => {
  it('clamps model level to available lumber yard variants', () => {
    expect(lumberYardModelLevel(0)).toBe(1)
    expect(lumberYardModelLevel(1)).toBe(1)
    expect(lumberYardModelLevel(9)).toBe(9)
    expect(lumberYardModelLevel(13)).toBe(13)
    expect(lumberYardModelLevel(99)).toBe(13)
  })

  it('chooses construction, damaged and ruined states from building state', () => {
    expect(lumberYardModelState({ status: 'construction', state: 'building', health: 100 })).toBe('construction')
    expect(lumberYardModelState({ status: 'active', state: 'damaged', health: 100 })).toBe('damaged')
    expect(lumberYardModelState({ status: 'active', state: 'active', health: 20 })).toBe('damaged')
    expect(lumberYardModelState({ status: 'active', state: 'ruined', health: 100 })).toBe('ruined')
  })
})
