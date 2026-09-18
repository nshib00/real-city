import { describe, expect, it, vi } from 'vitest'

import { hasTerrainTexture, TERRAIN_SPRITE, terrainPngTextureUrl, terrainTextureUrl } from './terrainTextures'

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
    expect(terrainTextureUrl({ terrain: 'mountain' })).toBe('/assets/terrain/tiles/mountain.png')
    expect(terrainTextureUrl({ terrain: 'oil_well' })).toBe('/assets/terrain/tiles/oil_well.png')
    expect(terrainTextureUrl({ terrain: 'ruins' })).toBe('/assets/terrain/tiles/ruins.png')
  })

  it('points terrain ids to PNG sprite assets', () => {
    expect(terrainPngTextureUrl({ terrain: 'grass' })).toBe('/assets/terrain/tiles/grass.png')
    expect(terrainPngTextureUrl({ terrain: 'forest' })).toBe('/assets/terrain/tiles/forest.png')
    expect(terrainPngTextureUrl({ terrain: 'water' })).toBe('/assets/terrain/tiles/water.png')
    expect(terrainPngTextureUrl({ terrain: 'mountain' })).toBe('/assets/terrain/tiles/mountain.png')
    expect(terrainPngTextureUrl({ terrain: 'oil_well' })).toBe('/assets/terrain/tiles/oil_well.png')
    expect(terrainPngTextureUrl({ terrain: 'ruins' })).toBe('/assets/terrain/tiles/ruins.png')
  })

  it('provides a regenerated road sprite', () => {
    expect(hasTerrainTexture({ terrain: 'road' })).toBe(true)
    expect(terrainTextureUrl({ terrain: 'road' })).toBe('/assets/terrain/tiles/road.png')
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
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/mountain.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/oil_well.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/ruins.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/road.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/forest_thinned.png')
    expect(loadTerrainAsset).toHaveBeenCalledWith('/assets/terrain/tiles/forest_sparse.png')
  })
})
