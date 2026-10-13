import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import { buildingModelAsset } from './buildingModelAssets'
import { COIN_STORAGE_ASSET_REVISION, FLAX_FIELD_ASSET_REVISION, GLASS_WORKSHOP_ASSET_REVISION, HERB_BED_ASSET_REVISION, LUMBER_YARD_ASSET_REVISION, MINE_ASSET_REVISION, MUSHROOM_GROVE_ASSET_REVISION, OILSEED_FIELD_ASSET_REVISION, REED_BED_ASSET_REVISION, ROPE_YARD_ASSET_REVISION, SAND_QUARRY_ASSET_REVISION, SEED_GARDEN_ASSET_REVISION } from './buildingSpriteAssets'

describe('building model assets', () => {
  it('connects lumber yard states to public glb models', () => {
    expect(buildingModelAsset(lumberYard({ status: 'active', state: 'active', health: 100 }))).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l01_active.glb?v=${LUMBER_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(lumberYard({ status: 'construction', state: 'building', health: 100 }))).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l01_construction.glb?v=${LUMBER_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(lumberYard({ status: 'active', state: 'active', health: 20, maxHealth: 120 }))).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.glb?v=${LUMBER_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(lumberYard({ status: 'active', state: 'ruined', health: 0 }))).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.glb?v=${LUMBER_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset({ ...lumberYard({ status: 'active', state: 'active', health: 100 }), level: 99 })).toBe(
      `/assets/buildings/industry/lumber_yard/lumber_yard_l13_active.glb?v=${LUMBER_YARD_ASSET_REVISION}`,
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
    expect(buildingModelAsset(windleafBed({ status: 'active', state: 'active', health: 100, level: 2, growthStage: 1 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l02_stage01.glb',
    )
    expect(buildingModelAsset(windleafBed({ status: 'active', state: 'active', health: 100, level: 3, superStage: 6 }))).toBe(
      '/assets/buildings/fields/windleaf_bed/windleaf_bed_l03_super_stage06.glb',
    )
  })

  it('connects seed garden states to public glb models', () => {
    expect(buildingModelAsset(seedGarden({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l01_active.glb?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(seedGarden({ status: 'active', state: 'active', health: 100, level: 2, growthStage: 3 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l02_stage03.glb?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(seedGarden({ status: 'active', state: 'active', health: 100, level: 3, superStage: 6 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l03_super_stage06.glb?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(seedGarden({ status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      `/assets/buildings/fields/seed_garden/seed_garden_l10_ruined.glb?v=${SEED_GARDEN_ASSET_REVISION}`,
    )
  })

  it('connects flax field states to public glb models', () => {
    expect(buildingModelAsset(flaxField({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l01_active.glb?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(flaxField({ status: 'active', state: 'active', health: 100, level: 2, growthStage: 3 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l02_stage03.glb?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(flaxField({ status: 'active', state: 'active', health: 100, level: 3, superStage: 6 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l03_super_stage06.glb?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(flaxField({ status: 'active', state: 'active', health: 100, level: 10, superStage: 6 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l10_super_stage06.glb?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(flaxField({ status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      `/assets/buildings/fields/flax_field/flax_field_l10_ruined.glb?v=${FLAX_FIELD_ASSET_REVISION}`,
    )
  })

  it('connects oilseed field states to public glb models', () => {
    expect(buildingModelAsset(oilseedField({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/fields/oilseed_field/oilseed_field_l01_active.glb?v=${OILSEED_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(oilseedField({ status: 'active', state: 'active', health: 100, level: 2, growthStage: 3 }))).toBe(
      `/assets/buildings/fields/oilseed_field/oilseed_field_l02_stage03.glb?v=${OILSEED_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(oilseedField({ status: 'active', state: 'active', health: 100, level: 7, superStage: 6 }))).toBe(
      `/assets/buildings/fields/oilseed_field/oilseed_field_l07_super_stage06.glb?v=${OILSEED_FIELD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(oilseedField({ status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      `/assets/buildings/fields/oilseed_field/oilseed_field_l07_ruined.glb?v=${OILSEED_FIELD_ASSET_REVISION}`,
    )
  })

  it('connects remaining field beds to public glb models', () => {
    expect(buildingModelAsset(fieldCrop('mushroom_grove', { status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/fields/mushroom_grove/mushroom_grove_l01_active.glb?v=${MUSHROOM_GROVE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(fieldCrop('mushroom_grove', { status: 'active', state: 'active', health: 100, level: 10, superStage: 6 }))).toBe(
      `/assets/buildings/fields/mushroom_grove/mushroom_grove_l10_super_stage06.glb?v=${MUSHROOM_GROVE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(fieldCrop('herb_bed', { status: 'active', state: 'active', health: 100, level: 99, growthStage: 3 }))).toBe(
      `/assets/buildings/fields/herb_bed/herb_bed_l09_stage03.glb?v=${HERB_BED_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(fieldCrop('reed_bed', { status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      `/assets/buildings/fields/reed_bed/reed_bed_l10_ruined.glb?v=${REED_BED_ASSET_REVISION}`,
    )
  })

  it('connects sand quarry states to public glb models', () => {
    expect(buildingModelAsset(sandQuarry({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/industry/sand_quarry/sand_quarry_l01_active.glb?v=${SAND_QUARRY_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(sandQuarry({ status: 'construction', state: 'building', health: 100, level: 2 }))).toBe(
      `/assets/buildings/industry/sand_quarry/sand_quarry_l02_construction.glb?v=${SAND_QUARRY_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(sandQuarry({ status: 'active', state: 'active', health: 20, maxHealth: 324, level: 3 }))).toBe(
      `/assets/buildings/industry/sand_quarry/sand_quarry_l03_damaged.glb?v=${SAND_QUARRY_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(sandQuarry({ status: 'active', state: 'active', health: 100, level: 11 }))).toBe(
      `/assets/buildings/industry/sand_quarry/sand_quarry_l11_active.glb?v=${SAND_QUARRY_ASSET_REVISION}`,
    )
  })

  it('connects glass workshop states to public glb models', () => {
    expect(buildingModelAsset(glassWorkshop({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l01_active.glb?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(glassWorkshop({ status: 'construction', state: 'building', health: 100, level: 2 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l02_construction.glb?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(glassWorkshop({ status: 'active', state: 'active', health: 87, maxHealth: 436, level: 3 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l03_damaged.glb?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(glassWorkshop({ status: 'active', state: 'ruined', health: 0, level: 12 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l12_ruined.glb?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(glassWorkshop({ status: 'active', state: 'active', health: 100, level: 99 }))).toBe(
      `/assets/buildings/industry/glass_workshop/glass_workshop_l12_active.glb?v=${GLASS_WORKSHOP_ASSET_REVISION}`,
    )
  })

  it('connects rope yard production states to public glb models', () => {
    expect(buildingModelAsset(ropeYard({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l01_active.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(ropeYard({ status: 'active', state: 'active', health: 100, level: 3, productionState: 'ready' }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l03_ready.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(ropeYard({ status: 'active', state: 'active', health: 100, level: 4, noInput: true }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l04_idle_no_input.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(ropeYard({ status: 'active', state: 'active', health: 100, level: 5, noWorkers: true }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l05_idle_no_workers.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(ropeYard({ status: 'construction', state: 'building', health: 100, level: 6 }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l06_construction.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(ropeYard({ status: 'active', state: 'active', health: 160, maxHealth: 850, level: 7 }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l07_damaged.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(ropeYard({ status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      `/assets/buildings/industry/rope_yard/rope_yard_l08_ruined.glb?v=${ROPE_YARD_ASSET_REVISION}`,
    )
  })

  it('connects mine states to public glb models', () => {
    expect(buildingModelAsset(mine({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/industry/mine/mine_l01_active.glb?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(mine({ status: 'construction', state: 'building', health: 100, level: 2 }))).toBe(
      `/assets/buildings/industry/mine/mine_l02_construction.glb?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(mine({ status: 'active', state: 'active', health: 35, maxHealth: 176, level: 3 }))).toBe(
      `/assets/buildings/industry/mine/mine_l03_damaged.glb?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(mine({ status: 'construction', state: 'building', health: 100, level: 12 }))).toBe(
      `/assets/buildings/industry/mine/mine_l12_construction.glb?v=${MINE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(mine({ status: 'active', state: 'active', health: 100, level: 99 }))).toBe(
      `/assets/buildings/industry/mine/mine_l12_active.glb?v=${MINE_ASSET_REVISION}`,
    )
  })

  it('connects coin storage states to public glb models', () => {
    expect(buildingModelAsset(coinStorage({ status: 'active', state: 'active', health: 100, level: 1 }))).toBe(
      `/assets/buildings/storage/coin_storage/coin_storage_l01_active.glb?v=${COIN_STORAGE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(coinStorage({ status: 'construction', state: 'building', health: 100, level: 2 }))).toBe(
      `/assets/buildings/storage/coin_storage/coin_storage_l02_construction.glb?v=${COIN_STORAGE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(coinStorage({ status: 'active', state: 'active', health: 18, maxHealth: 120, level: 7 }))).toBe(
      `/assets/buildings/storage/coin_storage/coin_storage_l07_damaged.glb?v=${COIN_STORAGE_ASSET_REVISION}`,
    )
    expect(buildingModelAsset(coinStorage({ status: 'active', state: 'ruined', health: 0, level: 99 }))).toBe(
      `/assets/buildings/storage/coin_storage/coin_storage_l12_ruined.glb?v=${COIN_STORAGE_ASSET_REVISION}`,
    )
  })
})

function lumberYard(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health'> & Partial<PlacedBuilding>): PlacedBuilding {
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

function windleafBed(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
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

function seedGarden(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'seed-garden-1',
    kind: 'seed_garden',
    name: 'Семенной огород',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function flaxField(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'flax-field-1',
    kind: 'flax_field',
    name: 'Льняное поле',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function oilseedField(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'oilseed-field-1',
    kind: 'oilseed_field',
    name: 'Масличное поле',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function fieldCrop(
  kind: 'herb_bed' | 'mushroom_grove' | 'reed_bed',
  overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>,
): PlacedBuilding {
  return {
    id: `${kind}-1`,
    kind,
    name: kind,
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function sandQuarry(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'sand-quarry-1',
    kind: 'sand_quarry',
    name: 'Песчаный карьер',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function glassWorkshop(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'glass-workshop-1',
    kind: 'glass_workshop',
    name: 'Стекольная мастерская',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function ropeYard(
  overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding> & {
    productionState?: string
    noInput?: boolean
    noWorkers?: boolean
  },
): PlacedBuilding {
  return {
    id: 'rope-yard-1',
    kind: 'rope_yard',
    name: 'Канатный двор',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function mine(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'mine-1',
    kind: 'mine',
    name: 'Шахта',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}

function coinStorage(overrides: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'level'> & Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'coin-storage-1',
    kind: 'coin_storage',
    name: 'Хранилище монет',
    tile: { x: 0, y: 0 },
    owner: 'test',
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}
