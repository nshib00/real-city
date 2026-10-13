import { describe, expect, it } from 'vitest'

import { glassWorkshopModelLevel, glassWorkshopModelState } from './glassWorkshop'

describe('glass workshop renderer', () => {
  it('clamps model level to generated glass workshop variants', () => {
    expect(glassWorkshopModelLevel(0)).toBe(1)
    expect(glassWorkshopModelLevel(1)).toBe(1)
    expect(glassWorkshopModelLevel(9)).toBe(9)
    expect(glassWorkshopModelLevel(12)).toBe(12)
    expect(glassWorkshopModelLevel(99)).toBe(12)
  })

  it('chooses construction, damaged and ruined states from building data', () => {
    expect(glassWorkshopModelState({ status: 'construction', state: 'building', health: 100 })).toBe('construction')
    expect(glassWorkshopModelState({ status: 'active', state: 'active', health: 87, maxHealth: 436 })).toBe('damaged')
    expect(glassWorkshopModelState({ status: 'active', state: 'active', health: 100, maxHealth: 436 })).toBe('active')
    expect(glassWorkshopModelState({ status: 'active', state: 'ruined', health: 100 })).toBe('ruined')
  })
})
