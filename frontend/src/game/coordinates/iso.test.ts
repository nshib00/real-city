import { describe, expect, it } from 'vitest'

import { gridToScreen, screenToGrid, tileToChunk, WORLD_WRAP_SCREEN, WORLD_WRAP_TILES, wrapCameraOffset, wrapGridCoord } from './iso'

describe('isometric coordinates', () => {
  it('round-trips grid and screen coordinates', () => {
    const screen = gridToScreen({ x: 4, y: 2 })
    const grid = screenToGrid(screen)

    expect(grid.x).toBeCloseTo(4)
    expect(grid.y).toBeCloseTo(2)
  })

  it('maps tiles to chunk coordinates', () => {
    expect(tileToChunk({ x: 0, y: 0 })).toEqual({ x: 0, y: 0 })
    expect(tileToChunk({ x: 32, y: 63 })).toEqual({ x: 1, y: 1 })
    expect(tileToChunk({ x: -1, y: -33 })).toEqual({ x: -1, y: -2 })
  })

  it('wraps world coordinates and camera offsets cyclically', () => {
    expect(wrapGridCoord({ x: -1, y: WORLD_WRAP_TILES + 2 })).toEqual({ x: WORLD_WRAP_TILES - 1, y: 2 })
    expect(wrapCameraOffset({ x: WORLD_WRAP_SCREEN.x + 240, y: -WORLD_WRAP_SCREEN.y - 120 })).toEqual({ x: 240, y: -120 })
  })
})
