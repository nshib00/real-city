import { Assets } from 'pixi.js'
import type { WorldTile } from '../../shared/contracts'

const RUINS_VARIANTS = [
  'ruins_town_square',
  'ruins_archive',
  'ruins_mint',
  'ruins_storage',
  'ruins_greenhouse',
  'ruins_water_station',
  'ruins_bastion',
  'ruins_mechanic_workshop',
  'ruins_wind_shrine',
  'ruins_ore_obelisk',
  'ruins_rift_watch',
  'ruins_river_lighthouse',
] as const
const TEXTURED_TERRAINS = new Set(['grass', 'forest', 'water', 'mountain', 'road', 'oil_well', 'ruins', ...RUINS_VARIANTS])
const TERRAIN_SPRITES = [...TEXTURED_TERRAINS, 'forest_thinned', 'forest_sparse']
type TerrainTile = { terrain: string } & Partial<Pick<WorldTile, 'forest_density'>>

export const TERRAIN_SPRITE = {
  width: 512,
  height: 512,
  footprintWidth: 480,
  anchorX: 0.5,
  anchorY: 0.625,
} as const
const terrainPngTextureChecks = new Map<string, Promise<void>>()

export function terrainPngTextureUrl(tile: TerrainTile) {
  if (!TEXTURED_TERRAINS.has(tile.terrain)) {
    return undefined
  }
  let sprite: string = tile.terrain
  if (tile.terrain === 'forest') {
    if (tile.forest_density === 2) sprite = 'forest_thinned'
    if (tile.forest_density === 1) sprite = 'forest_sparse'
  }
  return `/assets/terrain/tiles/${sprite}.png`
}

export function terrainTextureUrl(tile: TerrainTile) {
  return terrainPngTextureUrl(tile)
}

export function hasTerrainTexture(tile: TerrainTile) {
  return Boolean(terrainTextureUrl(tile))
}

export function preloadTerrainPngTextures() {
  return Promise.all(TERRAIN_SPRITES.map((terrain) => checkTerrainPngTexture(terrain))).then(() => undefined)
}

function checkTerrainPngTexture(terrain: string) {
  const existing = terrainPngTextureChecks.get(terrain)
  if (existing) {
    return existing
  }

  const promise = Assets.load(`/assets/terrain/tiles/${terrain}.png`).then(
    () => undefined,
    () => undefined,
  )
  terrainPngTextureChecks.set(terrain, promise)
  return promise
}
