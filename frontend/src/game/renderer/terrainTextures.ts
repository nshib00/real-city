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
const MOUNTAIN_VARIANTS = [
  'mountain_detail_ridge',
  'mountain_detail_spire',
  'mountain_detail_snowcap',
] as const
export function terrainPreloadUrls(tiles: readonly TerrainTile[]) {
  return [...new Set(tiles.map(terrainTextureUrl).filter((url): url is string => Boolean(url)))]
}
type TerrainTile = { terrain: string } & Partial<Pick<WorldTile, 'x' | 'y' | 'forest_density' | 'ruin_type'>>

export function isRaisedTerrain(tile: TerrainTile) {
  return tile.terrain === 'forest' || tile.terrain === 'mountain' || tile.terrain === 'ruins' || tile.terrain.startsWith('ruins_')
}

export const TERRAIN_SPRITE = {
  width: 512,
  height: 512,
  footprintWidth: 480,
  anchorX: 0.5,
  anchorY: 0.625,
} as const

export function terrainRuntimeTextureUrl(tile: TerrainTile) {
  if (!TEXTURED_TERRAINS.has(tile.terrain)) {
    return undefined
  }
  let sprite: string = tile.terrain
  if (tile.terrain === 'forest') {
    if (tile.forest_density === 2) sprite = 'forest_thinned'
    if (tile.forest_density === 1) sprite = 'forest_sparse'
  }
  if (tile.terrain === 'ruins' && tile.ruin_type && RUINS_VARIANTS.includes(tile.ruin_type as typeof RUINS_VARIANTS[number])) {
    sprite = tile.ruin_type
  }
  if (tile.terrain === 'mountain') {
    const variant = Math.abs(Math.imul(tile.x ?? 0, 73856093) ^ Math.imul(tile.y ?? 0, 19349663)) % MOUNTAIN_VARIANTS.length
    sprite = MOUNTAIN_VARIANTS[variant]
  }
  return `/assets/terrain/tiles/runtime/${sprite}.webp`
}

export function terrainTextureUrl(tile: TerrainTile) {
  return terrainRuntimeTextureUrl(tile)
}

export function hasTerrainTexture(tile: TerrainTile) {
  return Boolean(terrainTextureUrl(tile))
}
