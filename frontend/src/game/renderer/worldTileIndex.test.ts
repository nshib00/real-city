import { describe, expect, it } from 'vitest'

import type { WorldTile } from '../../shared/contracts'
import { wrappedGridDistance } from '../coordinates/iso'
import { indexWorldTiles, worldTilesNear } from './worldTileIndex'

describe('world tile index', () => {
  it('contains every tile in reach at several wrapped camera positions', () => {
    const tiles = Array.from({ length: 160 * 160 }, (_, id) => ({ x: id % 160, y: Math.floor(id / 160) }) as WorldTile)
    const index = indexWorldTiles(tiles)
    for (const center of [{ x: 0, y: 0 }, { x: 159, y: 159 }, { x: -1, y: 161 }, { x: 320, y: -160 }]) {
      const expected = tiles.filter((tile) => wrappedGridDistance(tile.x, center.x) <= 12 && wrappedGridDistance(tile.y, center.y) <= 12)
      const candidates = worldTilesNear(index, center, 12)
      expect(candidates.filter((tile) => wrappedGridDistance(tile.x, center.x) <= 12 && wrappedGridDistance(tile.y, center.y) <= 12)).toEqual(expected)
      expect(candidates.length).toBeLessThan(tiles.length)
    }
  })
})
