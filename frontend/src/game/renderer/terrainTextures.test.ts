import { describe, expect, it } from 'vitest'

import { hasTerrainTexture, isRaisedTerrain, TERRAIN_SPRITE, terrainRuntimeTextureUrl, terrainTextureUrl, terrainPreloadUrls } from './terrainTextures'

describe('terrain textures', () => {
  it('provides image textures for visual terrain types', () => {
    expect(terrainTextureUrl({ terrain: 'grass' })).toBe('/assets/terrain/tiles/runtime/grass.webp')
    expect(terrainTextureUrl({ terrain: 'forest' })).toBe('/assets/terrain/tiles/runtime/forest.webp')
    expect(terrainTextureUrl({ terrain: 'water' })).toBe('/assets/terrain/tiles/runtime/water.webp')
    expect(terrainTextureUrl({ terrain: 'mountain' })).toBe('/assets/terrain/tiles/runtime/mountain_detail_ridge.webp')
    expect(terrainTextureUrl({ terrain: 'oil_well' })).toBe('/assets/terrain/tiles/runtime/oil_well.webp')
    expect(terrainTextureUrl({ terrain: 'ruins' })).toBe('/assets/terrain/tiles/runtime/ruins.webp')
  })

  it('points terrain ids to runtime sprite assets', () => {
    expect(terrainRuntimeTextureUrl({ terrain: 'grass' })).toBe('/assets/terrain/tiles/runtime/grass.webp')
    expect(terrainRuntimeTextureUrl({ terrain: 'forest' })).toBe('/assets/terrain/tiles/runtime/forest.webp')
    expect(terrainRuntimeTextureUrl({ terrain: 'water' })).toBe('/assets/terrain/tiles/runtime/water.webp')
    expect(terrainRuntimeTextureUrl({ terrain: 'mountain' })).toBe('/assets/terrain/tiles/runtime/mountain_detail_ridge.webp')
    expect(terrainRuntimeTextureUrl({ terrain: 'oil_well' })).toBe('/assets/terrain/tiles/runtime/oil_well.webp')
    expect(terrainRuntimeTextureUrl({ terrain: 'ruins' })).toBe('/assets/terrain/tiles/runtime/ruins.webp')
  })

  it('connects generated ruins variants to runtime terrain sprites', () => {
    expect(terrainTextureUrl({ terrain: 'ruins_archive' })).toBe('/assets/terrain/tiles/runtime/ruins_archive.webp')
    expect(terrainTextureUrl({ terrain: 'ruins_wind_shrine' })).toBe('/assets/terrain/tiles/runtime/ruins_wind_shrine.webp')
    for (const variant of [
      'ruins_town_square', 'ruins_archive', 'ruins_mint', 'ruins_storage',
      'ruins_greenhouse', 'ruins_water_station', 'ruins_bastion',
      'ruins_mechanic_workshop', 'ruins_wind_shrine', 'ruins_ore_obelisk',
      'ruins_rift_watch', 'ruins_river_lighthouse',
    ]) {
      expect(terrainTextureUrl({ terrain: 'ruins', ruin_type: variant })).toBe(`/assets/terrain/tiles/runtime/${variant}.webp`)
    }
    expect(terrainTextureUrl({ terrain: 'ruins', ruin_type: 'unknown' })).toBe('/assets/terrain/tiles/runtime/ruins.webp')
  })

  it('selects a stable mountain variant for each coordinate without changing its terrain type', () => {
    const variants = new Set<string>()
    for (let x = -3; x <= 3; x += 1) {
      for (let y = -3; y <= 3; y += 1) {
        const tile = { terrain: 'mountain', x, y }
        const texture = terrainTextureUrl(tile)
        expect(terrainTextureUrl(tile)).toBe(texture)
        expect(isRaisedTerrain(tile)).toBe(true)
        variants.add(texture!)
      }
    }
    expect(variants).toEqual(new Set([
      '/assets/terrain/tiles/runtime/mountain_detail_ridge.webp',
      '/assets/terrain/tiles/runtime/mountain_detail_spire.webp',
      '/assets/terrain/tiles/runtime/mountain_detail_snowcap.webp',
    ]))
  })

  it('uses the new ground-road model for legacy road terrain', () => {
    expect(hasTerrainTexture({ terrain: 'road' })).toBe(true)
    expect(terrainTextureUrl({ terrain: 'road' })).toBe('/assets/buildings/roads/ground_road/ground_road_cross_active.png?v=road-kits-v3-2026-11-05')
  })

  it('places raised terrain in the depth-sorted object layer', () => {
    expect(isRaisedTerrain({ terrain: 'forest' })).toBe(true)
    expect(isRaisedTerrain({ terrain: 'mountain' })).toBe(true)
    expect(isRaisedTerrain({ terrain: 'ruins_archive' })).toBe(true)
    expect(isRaisedTerrain({ terrain: 'grass' })).toBe(false)
    expect(isRaisedTerrain({ terrain: 'oil_well' })).toBe(false)
  })

  it('shows forest clearing through canopy density', () => {
    expect(terrainTextureUrl({ terrain: 'forest', forest_density: 3 })).toBe('/assets/terrain/tiles/runtime/forest.webp')
    expect(terrainTextureUrl({ terrain: 'forest', forest_density: 2 })).toBe('/assets/terrain/tiles/runtime/forest_thinned.webp')
    expect(terrainTextureUrl({ terrain: 'forest', forest_density: 1 })).toBe('/assets/terrain/tiles/runtime/forest_sparse.webp')
    expect(terrainTextureUrl({ terrain: 'grass', forest_density: 0 })).toBe('/assets/terrain/tiles/runtime/grass.webp')
  })

  it('matches the Blender tile footprint without aspect distortion', () => {
    const scale = 240 / TERRAIN_SPRITE.footprintWidth
    expect(TERRAIN_SPRITE.width * scale).toBe(256)
    expect(TERRAIN_SPRITE.height * scale).toBe(256)
    expect(TERRAIN_SPRITE.anchorY * TERRAIN_SPRITE.height).toBe(320)
  })

  it('preloads only terrain variants present in the initial viewport', () => {
    expect(terrainPreloadUrls([
      { terrain: 'grass' }, { terrain: 'grass' },
      { terrain: 'forest', forest_density: 2 },
      { terrain: 'ruins', ruin_type: 'ruins_archive' },
    ])).toEqual([
      '/assets/terrain/tiles/runtime/grass.webp',
      '/assets/terrain/tiles/runtime/forest_thinned.webp',
      '/assets/terrain/tiles/runtime/ruins_archive.webp',
    ])
  })
})
