import { describe, expect, it } from 'vitest'

import { townHallModelLevel, townHallModelState } from './townHall'

describe('town hall renderer', () => {
  it('clamps model level to available town hall variants', () => {
    expect(townHallModelLevel(0)).toBe(1)
    expect(townHallModelLevel(6)).toBe(6)
    expect(townHallModelLevel(99)).toBe(10)
  })

  it('chooses construction, damaged and ruined states from health threshold', () => {
    expect(townHallModelState({ status: 'construction', state: 'building', health: 1000 })).toBe('construction')
    expect(townHallModelState({ status: 'active', state: 'damaged', health: 1000, maxHealth: 1000 })).toBe('active')
    expect(townHallModelState({ status: 'active', state: 'active', health: 200, maxHealth: 1000 })).toBe('damaged')
    expect(townHallModelState({ status: 'active', state: 'ruined', health: 1000 })).toBe('ruined')
  })
})
