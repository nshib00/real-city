import { describe, expect, it, vi } from 'vitest'

import { hasTerrainTexture, isRaisedTerrain, TERRAIN_SPRITE, terrainPngTextureUrl, terrainTextureUrl } from './terrainTextures'

const { loadTerrainAsset } = vi.hoisted(() => ({
  loadTerrainAsset: vi.fn(() => Promise.resolve({})),
}))

vi.mock('pixi.js', () => ({
  Assets: {
    load: loadTerrainAsset,
  },
}))

describe('terrain textures', () => {
  it('provides image textures for visual terrain types', () => {
    expect(terrainTextureUrl({ terrain: 'grass' })).toBe('/assets/terrain/tiles/grass.png')
    expect(terrainTextureUrl({ terrain: 'forest' })).toBe('/assets/terrain/tiles/forest.png')
    expect(terrainTextureUrl({ terrain: 'water' })).toBe('/assets/terrain/tiles/water.png')
    expect(terrainTextureUrl({ terrain: 'mountain' })).toBe('/assets/terrain/tiles/mountain_detail_staging/mountain_detail_ridge.png')
    expect(terrainTextureUrl({ terrain: 'oil_well' })).toBe('/assets/terrain/tiles/oil_well.png')
    expect(terrainTextureUrl({ terrain: 'ruins' })).toBe('/assets/terrain/tiles/ruins.png')
  })

  it('points terrain ids to PNG sprite assets', () => {
    expect(terrainPngTextureUrl({ terrain: 'grass' })).toBe('/assets/terrain/tiles/grass.png')
    expect(terrainPngTextureUrl({ terrain: 'forest' })).toBe('/assets/terrain/tiles/forest.png')
    expect(terrainPngTextureUrl({ terrain: 'water' })).toBe('/assets/terrain/tiles/water.png')
    expect(terrainPngTextureUrl({ terrain: 'mountain' })).toBe('/assets/terrain/tiles/mountain_detail_staging/mountain_detail_ridge.png')
    expect(terrainPngTextureUrl({ terrain: 'oil_well' })).toBe('/assets/terrain/tiles/oil_well.png')
    expect(terrainPngTextureUrl({ terrain: 'ruins' })).toBe('/assets/terrain/tiles/ruins.png')
  })

  it('connects generated ruins variants to runtime terrain sprites', () => {
    expect(terrainTextureUrl({ terrain: 'ruins_archive' })).toBe('/assets/terrain/tiles/ruins_archive.png')
    expect(terrainTextureUrl({ terrain: 'ruins_wind_shrine' })).toBe('/assets/terrain/tiles/ruins_wind_shrine.png')
    for (const variant of [
      'ruins_town_square', 'ruins_archive', 'ruins_mint', 'ruins_storage',
      'ruins_greenhouse', 'ruins_water_station', 'ruins_bastion',
      'ruins_mechanic_workshop', 'ruins_wind_shrine', 'ruins_ore_obelisk',
      'ruins_rift_watch', 'ruins_river_lighthouse',
    ]) {
      expect(terrainTextureUrl({ terrain: 'ruins', ruin_type: variant })).toBe(`/assets/terrain/tiles/${variant}.png`)
    }
    expect(terrainTextureUrl({ terrain: 'ruins', ruin_type: 'unknown' })).toBe('/assets/terrain/tiles/ruins.png')
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
      '/assets/terrain/tiles/mountain_detail_staging/mountain_detail_ridge.png',
      '/assets/terrain/tiles/mountain_detail_staging/mountain_detail_spire.png',
      '/assets/terrain/tiles/mountain_detail_staging/mountain_detail_snowcap.png',
    ]))
  })

  it('provides a regenerated road sprite', () => {
    expect(hasTerrainTexture({ terrain: 'road' })).toBe(true)
    expect(terrainTextureUrl({ terrain: 'road' })).toBe('/assets/terrain/tiles/road.png')
  })

  it('places raised terrain in the depth-sorted object layer', () => {
    expect(isRaisedTerrain({ terrain: 'forest' })).toBe(true)
    expect(isRaisedTerrain({ terrain: 'mountain' })).toBe(true)
    expect(isRaisedTerrain({ terrain: 'ruins_archive' })).toBe(true)
    expect(isRaisedTerrain({ terrain: 'grass' })).toBe(false)
    expect(isRaisedTerrain({ terrain: 'oil_well' })).toBe(false)
  })

  it('shows forest clearing through canopy density', () => {
    expect(terrainTextureUrl({ terrain: 'forest', forest_density: 3 })).toBe('/assets/terrain/tiles/forest.png')
    expect(terrainTextureUrl({ terrain: 'forest', forest_density: 2 })).toBe('/assets/terrain/tiles/forest_thinned.png')
    expect(terrainTextureUrl({ terrain: 'forest', forest_density: 1 })).toBe('/assets/terrain/tiles/forest_sparse.png')
    expect(terrainTextureUrl({ terrain: 'grass', forest_density: 0 })).toBe('/assets/terrain/tiles/grass.png')
  })

  it('matches the Blender tile footprint without aspect distortion', () => {
    const scale = 240 / TERRAIN_SPRITE.footprintWidth
    expect(TERRAIN_SPRITE.width * scale).toBe(256)
    expect(TERRAIN_SPRITE.height * scale).toBe(256)
    expect(TERRAIN_SPRITE.anchorY * TERRAIN_SPRITE.height).toBe(320)
  })

  it('preloads PNG textures through Pixi assets so Texture.from can read the cache', async () => {
    const { preloadTerrainPngTextures } = await import('./terrainTextures')

    await preloadTerrainPngTextures()

    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/grass.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/forest.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/water.png')
    for (const variant of ['ridge', 'spire', 'snowcap']) {
      expect(loadTerrainAsset).toHaveBeenCalledWith(`/assets/terrain/tiles/mountain_detail_staging/mountain_detail_${variant}.png`)
    }
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/oil_well.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/ruins.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/ruins_archive.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/ruins_wind_shrine.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/road.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/forest_thinned.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/forest_sparse.png')
  })
})
