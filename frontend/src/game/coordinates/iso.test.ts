import { describe, expect, it } from 'vitest'

import { gridToScreen, nearestWrappedScreenCoord, screenToGrid, tileToChunk, WORLD_WRAP_TILES, wrapGridCoord, wrappedGridDistance } from './iso'

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

  it('wraps world coordinates cyclically', () => {
    expect(wrapGridCoord({ x: -1, y: WORLD_WRAP_TILES + 2 })).toEqual({ x: WORLD_WRAP_TILES - 1, y: 2 })
  })

  it('finds the nearest copy after moving across multiple world periods', () => {
    const target = gridToScreen({ x: WORLD_WRAP_TILES * 3 + 4, y: -WORLD_WRAP_TILES * 2 + 7 })
    expect(nearestWrappedScreenCoord({ x: 4, y: 7 }, target)).toEqual(target)
    expect(wrappedGridDistance(159, -1)).toBe(0)
    expect(wrappedGridDistance(159, 1)).toBe(2)
  })
})
