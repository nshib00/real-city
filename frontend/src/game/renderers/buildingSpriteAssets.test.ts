import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import { resolveBuildingAtlasSource } from './buildingRegistry'
import { COIN_STORAGE_ASSET_REVISION, FLAX_FIELD_ASSET_REVISION, GLASS_WORKSHOP_ASSET_REVISION, HERB_BED_ASSET_REVISION, LUMBER_YARD_ASSET_REVISION, MINE_ASSET_REVISION, MUSHROOM_GROVE_ASSET_REVISION, OILSEED_FIELD_ASSET_REVISION, REED_BED_ASSET_REVISION, ROPE_YARD_ASSET_REVISION, SAND_QUARRY_ASSET_REVISION, SEED_GARDEN_ASSET_REVISION, buildingSpriteAsset } from './buildingSpriteAssets'

describe('building sprite assets', () => {
  it('connects visible building kinds to png sprites', () => {
    expect(buildingSpriteAsset(building({ kind: 'town_hall', level: 12, status: 'active', state: 'active', health: 1000 }))).toBe(
      '/assets/buildings/center/town_hall/town_hall_l10_active.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'dugout', level: 0, status: 'construction', state: 'building', health: 100 }))).toBe(
      '/assets/buildings/housing/dugout/dugout_l01_construction.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'wood_house', level: 4, status: 'active', state: 'active', health: 100, maxHealth: 1200 }))).toBe(
      '/assets/buildings/housing/wood_house/wood_house_l04_damaged.png',
    )
    expect(buildingSpriteAsset(building({ kind: 'lumber_yard', level: 1, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.png?v=${LUMBER_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'lumber_yard', level: 99, status: 'active', state: 'active', health: 100 }))).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l13_active.png?v=${LUMBER_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'glass_workshop', level: 12, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l12_ruined.png?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'glass_workshop', level: 99, status: 'active', state: 'active', health: 100 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l12_active.png?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'rope_yard', level: 99, status: 'active', state: 'active', health: 100 }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l08_active.png?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'rope_yard', level: 3, status: 'active', state: 'active', health: 100, productionState: 'ready' }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l03_ready.png?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'rope_yard', level: 4, status: 'active', state: 'active', health: 100, noInput: true }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l04_idle_no_input.png?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'rope_yard', level: 5, status: 'active', state: 'active', health: 100, noWorkers: true }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l05_idle_no_workers.png?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'rope_yard', level: 8, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l08_ruined.png?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'sand_quarry', level: 99, status: 'active', state: 'active', health: 100 }))).toBe(
      `/assets/buildings/industry/sand_quarry/sand_quarry_l11_active.png?v=${SAND_QUARRY_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'sand_quarry', level: 2, status: 'construction', state: 'building', health: 100 }))).toBe(
      `/assets/buildings/industry/sand_quarry/sand_quarry_l02_construction.png?v=${SAND_QUARRY_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'mine', level: 99, status: 'active', state: 'active', health: 100 }))).toBe(
      `/assets/buildings/industry/mine/mine_l12_active.png?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'mine', level: 2, status: 'construction', state: 'building', health: 100 }))).toBe(
      `/assets/buildings/industry/mine/mine_l02_construction.png?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'mine', level: 11, status: 'active', state: 'active', health: 20, maxHealth: 2562 }))).toBe(
      `/assets/buildings/industry/mine/mine_l11_damaged.png?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'coin_storage', level: 2, status: 'construction', state: 'building', health: 100 }))).toBe(
      `/assets/buildings/storage/coin_storage/coin_storage_l02_construction.png?v=${COIN_STORAGE_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'coin_storage', level: 99, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/storage/coin_storage/coin_storage_l12_ruined.png?v=${COIN_STORAGE_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'field_bed', level: 3, status: 'active', state: 'active', health: 20, maxHealth: 170 }))).toBe(
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
    expect(buildingSpriteAsset(building({ kind: 'seed_garden', level: 2, status: 'active', state: 'active', health: 100, fieldStage: 3 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l02_stage03.png?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'seed_garden', level: 3, status: 'active', state: 'active', health: 100, superStage: 6 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l03_super_stage06.png?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'seed_garden', level: 99, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l10_ruined.png?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'flax_field', level: 2, status: 'active', state: 'active', health: 100, fieldStage: 3 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l02_stage03.png?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'flax_field', level: 3, status: 'active', state: 'active', health: 100, superStage: 6 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l03_super_stage06.png?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'flax_field', level: 10, status: 'active', state: 'active', health: 100, superStage: 6 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l10_super_stage06.png?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'flax_field', level: 99, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l10_ruined.png?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'oilseed_field', level: 2, status: 'active', state: 'active', health: 100, fieldStage: 3 }))).toBe(
      `/assets/buildings/fields/oilseed_field/oilseed_field_l02_stage03.png?v=${OILSEED_FIELD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'oilseed_field', level: 99, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/fields/oilseed_field/oilseed_field_l07_ruined.png?v=${OILSEED_FIELD_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'mushroom_grove', level: 10, status: 'active', state: 'active', health: 100, superStage: 6 }))).toBe(
      `/assets/buildings/fields/mushroom_grove/mushroom_grove_l10_super_stage06.png?v=${MUSHROOM_GROVE_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'herb_bed', level: 99, status: 'active', state: 'active', health: 100, fieldStage: 3 }))).toBe(
      `/assets/buildings/fields/herb_bed/herb_bed_l09_stage03.png?v=${HERB_BED_ASSET_REVISION}`,
    )
    expect(buildingSpriteAsset(building({ kind: 'reed_bed', level: 99, status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/fields/reed_bed/reed_bed_l10_ruined.png?v=${REED_BED_ASSET_REVISION}`,
    )
  })

  it('keeps unsupported css fallback buildings without sprite urls', () => {
    expect(buildingSpriteAsset(building({ kind: 'warehouse', level: 1, status: 'active', state: 'active', health: 100 }))).toBeNull()
  })

  it('resolves atlas metadata with PNG fallback for atlas-ready buildings', () => {
    expect(resolveBuildingAtlasSource(building({ kind: 'lumber_yard', level: 1, status: 'active', state: 'active', health: 100 }))).toMatchObject({
      assetId: 'lumber_yard',
      basePath: '/assets/buildings/industry/lumber_yard',
      fallbackUrl: `/assets/buildings/industry/lumber_yard/lumber_yard_l01_active.png?v=${LUMBER_YARD_ASSET_REVISION}`,
      requiredFrames: expect.arrayContaining(['lumber_yard_l01_active.png', 'lumber_yard_working_0000.png']),
    })
  })
})

function building(
  overrides: Pick<PlacedBuilding, 'kind' | 'level' | 'status' | 'state' | 'health'> & Partial<PlacedBuilding> & {
    productionState?: string
    noInput?: boolean
    noWorkers?: boolean
  },
): PlacedBuilding {
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
