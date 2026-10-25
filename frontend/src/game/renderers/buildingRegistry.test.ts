import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import {
  buildingAssetLevel,
  buildingAssetState,
  buildingRegistryEntry,
  canResolveBuildingModelAsset,
  registeredBuildingAssetFamilies,
  resolveBuildingModelAsset,
  resolveBuildingSpriteAsset,
} from './buildingRegistry'

describe('building asset registry', () => {
  it('registers public and src-backed building families', () => {
    expect(registeredBuildingAssetFamilies().length).toBeGreaterThanOrEqual(10)
    expect(buildingRegistryEntry('town_hall')).toMatchObject({ assetId: 'town_hall', modelSource: 'src-models' })
    expect(buildingRegistryEntry('stone_house')).toMatchObject({ assetId: 'stone_house', modelSource: 'public' })
    expect(buildingRegistryEntry('villa')).toMatchObject({ assetId: 'villa', levels: [1, 2, 3, 4, 5], states: ['active'], modelSource: 'public' })
    expect(buildingRegistryEntry('mine')).toMatchObject({ assetId: 'mine', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('oil_well')).toMatchObject({ assetId: 'oil_well', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('military_factory')).toMatchObject({ assetId: 'military_factory', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('paper_workshop')).toMatchObject({ assetId: 'paper_workshop', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('tile_factory')).toMatchObject({ assetId: 'tile_factory', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('weaving_yard')).toMatchObject({ assetId: 'weaving_yard', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('mushroom_grove')).toMatchObject({ assetId: 'mushroom_grove', category: 'fields', modelSource: 'public' })
    expect(buildingRegistryEntry('reed_bed')).toMatchObject({ assetId: 'reed_bed', category: 'fields', modelSource: 'public' })
  })

  it('resolves the modeled defense families at their last specified levels', () => {
    const families = [
      ['defense_stakes', 6, 'armed'],
      ['defense_resin_snare', 4, 'armed'],
      ['defense_bolt_thrower', 8, 'active'],
      ['defense_storm_coil', 6, 'active'],
      ['defense_automaton_bay', 5, 'active'],
      ['defense_guardian_enclosure', 5, 'active'],
    ] as const
    for (const [kind, level, state] of families) {
      const model = resolveBuildingModelAsset(building({ kind, level, cannonEnabled: true }))
      expect(buildingAssetState(building({ kind, level, cannonEnabled: true }))).toBe(state)
      expect(model).toContain(`/assets/buildings/defense/${kind}/${kind}_l${String(level).padStart(2, '0')}_${state}_LOD0.glb`)
    }
    expect(buildingAssetState(building({ kind: 'defense_stakes', trapCharges: 0 }))).toBe('empty')
  })

  it('clamps levels through manifest policy', () => {
    expect(buildingAssetLevel(building({ kind: 'town_hall', level: 99 }))).toBe(10)
    expect(buildingAssetLevel(building({ kind: 'dugout', level: 0 }))).toBe(1)
    expect(buildingAssetLevel(building({ kind: 'lumber_yard', level: 99 }))).toBe(13)
    expect(buildingAssetLevel(building({ kind: 'herb_bed', level: 99 }))).toBe(9)
  })

  it('uses construction state for planned and building entities', () => {
    expect(buildingAssetState(building({ kind: 'mine', status: 'construction', state: 'building' }))).toBe('construction')
    expect(buildingAssetState(building({ kind: 'wood_house', status: 'active', state: 'planned' }))).toBe('construction')
  })

  it('uses damaged state only at the critical hp threshold', () => {
    expect(buildingAssetState(building({ kind: 'mine', health: 21, maxHealth: 100 }))).toBe('active')
    expect(buildingAssetState(building({ kind: 'mine', health: 20, maxHealth: 100 }))).toBe('damaged')
  })

  it('falls back from ruined to damaged when a manifest has no ruined asset', () => {
    const asset = resolveBuildingSpriteAsset(building({ kind: 'mine', level: 3, state: 'ruined', health: 0 }))
    expect(buildingAssetState(building({ kind: 'mine', state: 'ruined', health: 0 }))).toBe('damaged')
    expect(asset).toContain('/assets/buildings/industry/mine/mine_l03_damaged.png')
  })

  it('resolves the last military factory upgrade and its damaged model', () => {
    const factory = building({ kind: 'military_factory', level: 10, health: 10, maxHealth: 100 })
    expect(resolveBuildingSpriteAsset(factory)).toContain('/assets/buildings/industry/military_factory/military_factory_l10_damaged.png')
    expect(resolveBuildingModelAsset(factory)).toContain('/assets/buildings/industry/military_factory/military_factory_l10_damaged_LOD0.glb')
  })

  it('resolves stone house models and sprites for every available level and state', () => {
    for (let level = 1; level <= 6; level++) {
      for (const state of ['active', 'construction', 'damaged'] as const) {
        const house = building({ kind: 'stone_house', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/housing/stone_house/stone_house_l${String(level).padStart(2, '0')}_${state}`
        expect(resolveBuildingSpriteAsset(house)).toBe(`${base}.png?v=stone-house-l01-l06-runtime-glb-2026-10-22`)
        expect(resolveBuildingModelAsset(house)).toBe(`${base}.glb?v=stone-house-l01-l06-runtime-glb-2026-10-22`)
        expect(canResolveBuildingModelAsset(house)).toBe(true)
      }
    }
    expect(buildingAssetState(building({ kind: 'stone_house', state: 'ruined', health: 0 }))).toBe('damaged')
  })

  it('resolves every villa level without inventing missing states', () => {
    for (let level = 1; level <= 5; level++) {
      const villa = building({ kind: 'villa', level })
      const base = `/assets/buildings/housing/villa/villa_l${String(level).padStart(2, '0')}_active`
      expect(resolveBuildingSpriteAsset(villa)).toBe(`${base}.png?v=villa-l01-l05-2026-10-24`)
      expect(resolveBuildingModelAsset(villa)).toBe(`${base}_LOD0.glb?v=villa-l01-l05-2026-10-24`)
      expect(canResolveBuildingModelAsset(villa)).toBe(true)
    }

    for (const unavailable of [
      building({ kind: 'villa', level: 4, status: 'construction', state: 'building' }),
      building({ kind: 'villa', level: 4, health: 10, maxHealth: 100 }),
      building({ kind: 'villa', level: 4, state: 'ruined', health: 0 }),
    ]) {
      expect(buildingAssetState(unavailable)).toBeNull()
      expect(resolveBuildingSpriteAsset(unavailable)).toBeNull()
      expect(resolveBuildingModelAsset(unavailable)).toBeNull()
      expect(canResolveBuildingModelAsset(unavailable)).toBe(false)
    }
  })

  it('resolves paper workshop construction and late damaged exports', () => {
    const construction = building({ kind: 'paper_workshop', level: 1, status: 'construction', state: 'building' })
    const damaged = building({ kind: 'paper_workshop', level: 10, health: 10, maxHealth: 100 })
    expect(resolveBuildingSpriteAsset(construction)).toContain('/assets/buildings/industry/paper_workshop/paper_workshop_l01_construction.png')
    expect(resolveBuildingModelAsset(damaged)).toContain('/assets/buildings/industry/paper_workshop/paper_workshop_l10_damaged_LOD0.glb')
  })

  it('resolves tile factory construction and late damaged exports', () => {
    const construction = building({ kind: 'tile_factory', level: 1, status: 'construction', state: 'building' })
    const damaged = building({ kind: 'tile_factory', level: 10, health: 10, maxHealth: 100 })
    expect(resolveBuildingSpriteAsset(construction)).toContain('/assets/buildings/industry/tile_factory/tile_factory_l01_construction.png')
    expect(resolveBuildingModelAsset(damaged)).toContain('/assets/buildings/industry/tile_factory/tile_factory_l10_damaged_LOD0.glb')
  })

  it('resolves weaving yard construction and late damaged exports', () => {
    const construction = building({ kind: 'weaving_yard', level: 1, status: 'construction', state: 'building' })
    const damaged = building({ kind: 'weaving_yard', level: 10, health: 10, maxHealth: 100 })
    expect(resolveBuildingSpriteAsset(construction)).toContain('/assets/buildings/industry/weaving_yard/weaving_yard_l01_construction.png')
    expect(resolveBuildingModelAsset(damaged)).toContain('/assets/buildings/industry/weaving_yard/weaving_yard_l10_damaged_LOD0.glb')
  })

  it('keeps explicit ruined state for manifests that provide it', () => {
    expect(resolveBuildingSpriteAsset(building({ kind: 'coin_storage', level: 12, state: 'ruined', health: 0 }))).toContain(
      '/assets/buildings/storage/coin_storage/coin_storage_l12_ruined.png',
    )
  })

  it('resolves modular path assets through the same registry', () => {
    expect(resolveBuildingSpriteAsset(building({ kind: 'standard_road' }), { shape: 'straight_ew' })).toBe(
      '/assets/buildings/roads/common_road/common_road_straight_ew_active.png',
    )
  })

  it('resolves every wooden wall level with its connection shape and state', () => {
    for (let level = 1; level <= 3; level++) {
      for (const state of ['active', 'construction', 'damaged', 'ruined'] as const) {
        const wall = building({ kind: 'wooden_wall', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'ruined' ? 0 : state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/roads/wooden_wall/wooden_wall_l${String(level).padStart(2, '0')}_corner_ne_${state}`
        expect(resolveBuildingSpriteAsset(wall, { shape: 'corner_ne' })).toBe(`${base}.png`)
        expect(resolveBuildingModelAsset(wall, { shape: 'corner_ne' })).toBe(`${base}_LOD0.glb`)
      }
    }
  })

  it('resolves every stone wall level with its connection shape and state', () => {
    for (let level = 4; level <= 7; level++) {
      for (const state of ['active', 'construction', 'damaged', 'ruined'] as const) {
        const wall = building({ kind: 'stone_wall', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'ruined' ? 0 : state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/roads/stone_wall/stone_wall_l${String(level).padStart(2, '0')}_corner_ne_${state}`
        expect(resolveBuildingSpriteAsset(wall, { shape: 'corner_ne' })).toBe(`${base}.png`)
        expect(resolveBuildingModelAsset(wall, { shape: 'corner_ne' })).toBe(`${base}_LOD0.glb`)
      }
    }
  })

  it('resolves every concrete wall level with its connection shape and state', () => {
    for (let level = 8; level <= 10; level++) {
      for (const state of ['active', 'construction', 'damaged', 'ruined'] as const) {
        const wall = building({ kind: 'concrete_wall', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'ruined' ? 0 : state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/roads/concrete_wall/concrete_wall_l${String(level).padStart(2, '0')}_corner_ne_${state}`
        expect(resolveBuildingSpriteAsset(wall, { shape: 'corner_ne' })).toBe(`${base}.png`)
        expect(resolveBuildingModelAsset(wall, { shape: 'corner_ne' })).toBe(`${base}_LOD0.glb`)
      }
    }
  })

  it('resolves every modern wall level with its connection shape and state', () => {
    for (let level = 11; level <= 13; level++) {
      for (const state of ['active', 'construction', 'damaged', 'ruined'] as const) {
        const wall = building({ kind: 'modern_wall', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'ruined' ? 0 : state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/roads/modern_wall/modern_wall_l${level}_corner_ne_${state}`
        expect(resolveBuildingSpriteAsset(wall, { shape: 'corner_ne' })).toBe(`${base}.png`)
        expect(resolveBuildingModelAsset(wall, { shape: 'corner_ne' })).toBe(`${base}_LOD0.glb`)
      }
    }
  })

  it('keeps src-backed GLB models out of synchronous asset lookup', () => {
    const townHall = building({ kind: 'town_hall' })

    expect(canResolveBuildingModelAsset(townHall)).toBe(true)
    expect(resolveBuildingModelAsset(townHall)).toBeNull()
  })

  it('keeps public GLB model lookup synchronous for asset links', () => {
    const mine = building({ kind: 'mine' })

    expect(canResolveBuildingModelAsset(mine)).toBe(true)
    expect(resolveBuildingModelAsset(mine)).toContain('/assets/buildings/industry/mine/mine_l01_active.glb')
  })

  it('resolves every clay quarry level and model state', () => {
    for (let level = 1; level <= 12; level++) {
      for (const state of ['active', 'construction', 'damaged'] as const) {
        const quarry = building({ kind: 'clay_quarry', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : 'active', health: state === 'damaged' ? 10 : 100 })
        const fileName = `clay_quarry_l${String(level).padStart(2, '0')}_${state}`
        expect(resolveBuildingModelAsset(quarry)).toContain(`/assets/buildings/industry/clay_quarry/${fileName}.glb`)
        expect(resolveBuildingSpriteAsset(quarry)).toContain(`/assets/buildings/industry/clay_quarry/${fileName}.png`)
      }
    }
    expect(resolveBuildingModelAsset(building({ kind: 'clay_quarry', level: 12, state: 'ruined', health: 0 }))).toContain('clay_quarry_l12_damaged.glb')
  })

  it('resolves every brick yard level and model state', () => {
    for (let level = 1; level <= 10; level++) {
      for (const state of ['active', 'construction', 'damaged'] as const) {
        const yard = building({ kind: 'brick_yard', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/industry/brick_yard/brick_yard_l${String(level).padStart(2, '0')}_${state}`
        expect(resolveBuildingSpriteAsset(yard)).toContain(`${base}.png`)
        expect(resolveBuildingModelAsset(yard)).toContain(`${base}_LOD0.glb`)
      }
    }
  })

  it('resolves oil well building sprites and models for all runtime states', () => {
    expect(resolveBuildingSpriteAsset(building({ kind: 'oil_well', level: 3 }))).toContain(
      '/assets/buildings/industry/oil_well/oil_well_l03_active.png',
    )
    expect(resolveBuildingModelAsset(building({ kind: 'oil_well', level: 2, state: 'ruined', health: 0 }))).toContain(
      '/assets/buildings/industry/oil_well/oil_well_l02_ruined.glb',
    )
  })

  it('resolves documented copper mine levels and states', () => {
    for (let level = 1; level <= 10; level++) {
      for (const state of ['active', 'construction', 'damaged'] as const) {
        const mine = building({ kind: 'copper_mine', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/industry/copper_mine/copper_mine_l${String(level).padStart(2, '0')}_${state}`
        expect(resolveBuildingSpriteAsset(mine)).toBe(`${base}.png`)
        expect(resolveBuildingModelAsset(mine)).toBe(`${base}_LOD0.glb`)
      }
    }
    expect(buildingAssetState(building({ kind: 'copper_mine', level: 10, state: 'ruined', health: 0 }))).toBe('damaged')
  })

  it('resolves cannon assets for every level and state', () => {
    for (let level = 1; level <= 12; level++) {
      for (const state of ['active', 'construction', 'damaged', 'ruined'] as const) {
        const cannon = building({ kind: 'defense_cannon', level, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : state, health: state === 'ruined' ? 0 : state === 'damaged' ? 10 : 100 })
        const base = `/assets/buildings/defense/defense_cannon/defense_cannon_l${String(level).padStart(2, '0')}_${state}`
        expect(resolveBuildingSpriteAsset(cannon)).toContain(`${base}.png`)
        expect(resolveBuildingModelAsset(cannon)).toContain(`${base}_LOD0.glb`)
      }
    }
    expect(buildingAssetState(building({ kind: 'defense_cannon', state: 'damaged', health: 80, maxHealth: 100 }))).toBe('damaged')
  })

  it('resolves watchtower construction, active and damaged assets', () => {
    for (const state of ['construction', 'active', 'damaged'] as const) {
      const tower = building({ kind: 'tower', level: 1, status: state === 'construction' ? 'construction' : 'active', state: state === 'construction' ? 'building' : 'active', health: state === 'damaged' ? 10 : 100 })
      const base = `/assets/buildings/defense/tower/tower_l01_${state}`
      expect(resolveBuildingSpriteAsset(tower)).toContain(`${base}.png`)
      expect(resolveBuildingModelAsset(tower)).toContain(`${base}_LOD0.glb`)
    }
    expect(buildingAssetState(building({ kind: 'tower', state: 'ruined', health: 0 }))).toBe('damaged')
  })
})

function building(overrides: Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'building-1',
    kind: 'town_hall',
    name: 'Постройка',
    level: 1,
    tile: { x: 0, y: 0 },
    owner: 'test',
    status: 'active',
    state: 'active',
    health: 100,
    maxHealth: 100,
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}
