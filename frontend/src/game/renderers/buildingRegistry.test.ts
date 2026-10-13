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
    expect(buildingRegistryEntry('mine')).toMatchObject({ assetId: 'mine', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('oil_well')).toMatchObject({ assetId: 'oil_well', category: 'industry', modelSource: 'public' })
    expect(buildingRegistryEntry('mushroom_grove')).toMatchObject({ assetId: 'mushroom_grove', category: 'fields', modelSource: 'public' })
    expect(buildingRegistryEntry('reed_bed')).toMatchObject({ assetId: 'reed_bed', category: 'fields', modelSource: 'public' })
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

  it('resolves oil well building sprites and models for all runtime states', () => {
    expect(resolveBuildingSpriteAsset(building({ kind: 'oil_well', level: 3 }))).toContain(
      '/assets/buildings/industry/oil_well/oil_well_l03_active.png',
    )
    expect(resolveBuildingModelAsset(building({ kind: 'oil_well', level: 2, state: 'ruined', health: 0 }))).toContain(
      '/assets/buildings/industry/oil_well/oil_well_l02_ruined.glb',
    )
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
