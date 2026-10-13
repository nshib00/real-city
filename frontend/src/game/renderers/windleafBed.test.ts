import { describe, expect, it } from 'vitest'

import { windleafBedModelLevel, windleafBedModelState } from './windleafBed'

describe('windleaf bed renderer', () => {
  it('clamps model level to generated windleaf bed variants', () => {
    expect(windleafBedModelLevel(0)).toBe(1)
    expect(windleafBedModelLevel(2)).toBe(2)
    expect(windleafBedModelLevel(11)).toBe(3)
  })

  it('chooses growth and super growth stages from field progress', () => {
    expect(windleafBedModelState({ status: 'active', state: 'active', health: 100, fieldStage: 2 })).toBe('stage02')
    expect(windleafBedModelState({ status: 'active', state: 'active', health: 100, cropStage: 9 })).toBe('stage04')
    expect(windleafBedModelState({ status: 'active', state: 'active', health: 100, superStage: 5 })).toBe('super_stage05')
    expect(windleafBedModelState({ status: 'active', state: 'active', health: 100, growthStage: 3, isSuperCrop: true })).toBe('super_stage03')
  })

  it('keeps structural building states ahead of crop stages', () => {
    expect(windleafBedModelState({ status: 'construction', state: 'building', health: 100, fieldStage: 3 })).toBe('construction')
    expect(windleafBedModelState({ status: 'active', state: 'damaged', health: 100, maxHealth: 100, superStage: 4 })).toBe('super_stage04')
    expect(windleafBedModelState({ status: 'active', state: 'active', health: 20, maxHealth: 100, superStage: 4 })).toBe('damaged')
    expect(windleafBedModelState({ status: 'active', state: 'ruined', health: 100, fieldStage: 4 })).toBe('ruined')
  })
})
