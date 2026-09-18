import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import { buildingModelAsset } from './buildingModelAssets'

describe('building model assets', () => {
  it('connects lumber yard states to public glb models', () => {
    expect(buildingModelAsset(lumberYard({ status: 'active', state: 'active', health: 100 }))).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l01_active.glb',
    )
    expect(buildingModelAsset(lumberYard({ status: 'construction', state: 'building', health: 100 }))).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l01_construction.glb',
    )
    expect(buildingModelAsset(lumberYard({ status: 'active', state: 'damaged', health: 100 }))).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.glb',
    )
    expect(buildingModelAsset(lumberYard({ status: 'active', state: 'ruined', health: 0 }))).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.glb',
    )
    expect(buildingModelAsset({ ...lumberYard({ status: 'active', state: 'active', health: 100 }), level: 99 })).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l13_active.glb',
    )
  })

  it('connects windleaf bed states to public glb models', () => {
    expect(buildingModelAsset(windleafBed({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l01_active.glb',
    )
    expect(buildingModelAsset(windleafBed({ status: 'construction', state: 'building', health: 100, level: 2 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l02_construction.glb',
    )
    expect(buildingModelAsset(windleafBed({ status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_damaged.glb',
    )
    expect(buildingModelAsset(windleafBed({ status: 'active', state: 'active', health: 100, level: 11 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_active.glb',
    )
  })
})

function lumberYard(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health'>): PlacedBuilding {
  return {
    id: 'lumber-yard-1',
    kind: 'lumber_yard',
    name: 'Лесопильный двор',
    level: 1,
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function windleafBed(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'>): PlacedBuilding {
  return {
    id: 'windleaf-bed-1',
    kind: 'field_bed',
    name: 'Грядка ветролиста',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}
