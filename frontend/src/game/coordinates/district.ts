import { WORLD_WRAP_TILES, type GridCoord } from './iso'

export const DISTRICT_COUNT = 5
export const DISTRICT_SIZE = WORLD_WRAP_TILES / DISTRICT_COUNT
const DISTRICT_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXY'

export function districtFromTile(tile: GridCoord): GridCoord {
  const wrapped = wrappedTile(tile)
  return {
    x: Math.floor(wrapped.x / DISTRICT_SIZE),
    y: Math.floor(wrapped.y / DISTRICT_SIZE),
  }
}

export function districtLabel(district: GridCoord): string {
  return DISTRICT_LABELS[district.y * DISTRICT_COUNT + district.x] ?? '?'
}

export function cellLabel(tile: GridCoord): string {
  const wrapped = wrappedTile(tile)
  const district = districtFromTile(wrapped)
  const localX = wrapped.x % DISTRICT_SIZE
  const localY = wrapped.y % DISTRICT_SIZE
  return `${districtLabel(district)}${localY * DISTRICT_SIZE + localX + 1}`
}

function wrappedTile(tile: GridCoord): GridCoord {
  return {
    x: ((tile.x % WORLD_WRAP_TILES) + WORLD_WRAP_TILES) % WORLD_WRAP_TILES,
    y: ((tile.y % WORLD_WRAP_TILES) + WORLD_WRAP_TILES) % WORLD_WRAP_TILES,
  }
}
