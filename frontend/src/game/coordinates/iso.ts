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
export const CHUNK_SIZE = 32
export const WORLD_WRAP_TILES = 160
export const WORLD_WRAP_SCREEN = {
  x: TILE_WIDTH * WORLD_WRAP_TILES,
  y: TILE_HEIGHT * WORLD_WRAP_TILES,
}

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
  return {
    x: wrapNumber(coord.x, WORLD_WRAP_TILES),
    y: wrapNumber(coord.y, WORLD_WRAP_TILES),
  }
}

export function wrapCameraOffset(offset: ScreenCoord): ScreenCoord {
  return {
    x: wrapNumber(offset.x, WORLD_WRAP_SCREEN.x, true),
    y: wrapNumber(offset.y, WORLD_WRAP_SCREEN.y, true),
  }
}

export function nearestWrappedScreenCoord(coord: GridCoord, target: ScreenCoord): ScreenCoord {
  let nearest = gridToScreen(coord)
  let nearestDistance = screenDistance(nearest, target)

  for (let y = -1; y <= 1; y++) {
    for (let x = -1; x <= 1; x++) {
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

function screenDistance(a: ScreenCoord, b: ScreenCoord) {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y)
}

function wrapNumber(value: number, size: number, centered = false) {
  const wrapped = ((value % size) + size) % size
  return centered && wrapped > size / 2 ? wrapped - size : wrapped
}
