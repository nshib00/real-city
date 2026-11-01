import { WORLD_SIZE, CHUNK_SIZE as SHARED_CHUNK_SIZE, normalizeTile, wrappedDistance } from '../../../../shared/world/coordinates'

export type GridCoord = {
  x: number
  y: number
}

export type ScreenCoord = {
  x: number
  y: number
}

export const TILE_WIDTH = 240
export const TILE_HEIGHT = 120
export const CHUNK_SIZE = SHARED_CHUNK_SIZE
export const WORLD_WRAP_TILES = WORLD_SIZE
export function gridToScreen(coord: GridCoord): ScreenCoord {
  return {
    x: (coord.x - coord.y) * (TILE_WIDTH / 2),
    y: (coord.x + coord.y) * (TILE_HEIGHT / 2),
  }
}

export function screenToGrid(coord: ScreenCoord): GridCoord {
  return {
    x: coord.x / TILE_WIDTH + coord.y / TILE_HEIGHT,
    y: coord.y / TILE_HEIGHT - coord.x / TILE_WIDTH,
  }
}

export function tileToChunk(coord: GridCoord): GridCoord {
  return {
    x: Math.floor(coord.x / CHUNK_SIZE),
    y: Math.floor(coord.y / CHUNK_SIZE),
  }
}

export function roundGridCoord(coord: GridCoord): GridCoord {
  return {
    x: Math.round(coord.x),
    y: Math.round(coord.y),
  }
}

export function wrapGridCoord(coord: GridCoord): GridCoord {
  return normalizeTile(coord)
}

export function nearestWrappedScreenCoord(coord: GridCoord, target: ScreenCoord): ScreenCoord {
  let nearest = gridToScreen(coord)
  let nearestDistance = screenDistance(nearest, target)
  const targetGrid = screenToGrid(target)
  const wrapX = Math.round((targetGrid.x - coord.x) / WORLD_WRAP_TILES)
  const wrapY = Math.round((targetGrid.y - coord.y) / WORLD_WRAP_TILES)

  for (let y = wrapY - 1; y <= wrapY + 1; y++) {
    for (let x = wrapX - 1; x <= wrapX + 1; x++) {
      const candidate = gridToScreen({
        x: coord.x + x * WORLD_WRAP_TILES,
        y: coord.y + y * WORLD_WRAP_TILES,
      })
      const distance = screenDistance(candidate, target)
      if (distance < nearestDistance) {
        nearest = candidate
        nearestDistance = distance
      }
    }
  }

  return nearest
}

export function wrappedGridDistance(a: number, b: number) {
  return wrappedDistance(a, b)
}

function screenDistance(a: ScreenCoord, b: ScreenCoord) {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y)
}

function wrapNumber(value: number, size: number, centered = false) {
  const wrapped = ((value % size) + size) % size
  return centered && wrapped > size / 2 ? wrapped - size : wrapped
}
