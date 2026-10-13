import { describe, expect, it } from 'vitest'

import { dugoutModelLevel, dugoutModelState } from './dugout'

describe('dugout renderer', () => {
  it('clamps model level to available dugout variants', () => {
    expect(dugoutModelLevel(0)).toBe(1)
    expect(dugoutModelLevel(3)).toBe(3)
    expect(dugoutModelLevel(9)).toBe(5)
  })

  it('chooses construction, damaged and ruined states from health threshold', () => {
    expect(dugoutModelState({ status: 'construction', state: 'building', health: 100 })).toBe('construction')
    expect(dugoutModelState({ status: 'active', state: 'damaged', health: 100, maxHealth: 100 })).toBe('active')
    expect(dugoutModelState({ status: 'active', state: 'active', health: 20, maxHealth: 100 })).toBe('damaged')
    expect(dugoutModelState({ status: 'active', state: 'ruined', health: 100 })).toBe('ruined')
  })
})
