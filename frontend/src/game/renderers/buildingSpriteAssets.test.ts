import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import { buildingSpriteAsset } from './buildingSpriteAssets'

describe('building sprite assets', () => {
  it('connects visible building kinds to png sprites', () => {
    expect(buildingSpriteAsset(building({ kind: 'town_hall', level: 12, status: 'active', state: 'active', health: 1000 }))).toBe(
      '/assets/buildings/center/town_hall/town_hall_l10_active.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'dugout', level: 0, status: 'construction', state: 'building', health: 100 }))).toBe(
      '/assets/buildings/housing/dugout/dugout_l01_construction.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'wood_house', level: 4, status: 'active', state: 'damaged', health: 100 }))).toBe(
      '/assets/buildings/housing/wood_house/wood_house_l04_damaged.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'lumber_yard', level: 1, status: 'active', state: 'ruined', health: 0 }))).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'lumber_yard', level: 99, status: 'active', state: 'active', health: 100 }))).toBe(
      '/assets/buildings/industry/lumber_yard/lumber_yard_l13_active.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'field_bed', level: 3, status: 'active', state: 'damaged', health: 100 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_damaged.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'field_bed', level: 99, status: 'construction', state: 'building', health: 100 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_construction.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'field_bed', level: 11, status: 'active', state: 'active', health: 100 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_active.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'field_bed', level: 2, status: 'active', state: 'active', health: 100, fieldStage: 4 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l02_stage04.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'field_bed', level: 3, status: 'active', state: 'active', health: 100, superStage: 6 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_super_stage06.png',
    )
  })

  it('keeps unsupported css fallback buildings without sprite urls', () => {
    expect(buildingSpriteAsset(building({ kind: 'warehouse', level: 1, status: 'active', state: 'active', health: 100 }))).toBeNull()
  })
})

function building(overrides: Pick<PlacedBuilding, 'kind' | 'level' | 'status' | 'state' | 'health'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'building-1',
    name: 'Постройка',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}
