import type { WorldTile } from '../../shared/contracts'
import { CHUNK_SIZE, WORLD_WRAP_TILES, wrappedGridDistance } from '../coordinates/iso'

type IndexedTile = { tile: WorldTile; index: number }
export type WorldTileIndex = { tiles: WorldTile[]; buckets: Map<string, IndexedTile[]> }

export function indexWorldTiles(tiles: WorldTile[]): WorldTileIndex {
  const buckets = new Map<string, IndexedTile[]>()
  tiles.forEach((tile, index) => {
    const key = `${Math.floor(wrap(tile.x) / CHUNK_SIZE)}:${Math.floor(wrap(tile.y) / CHUNK_SIZE)}`
    const bucket = buckets.get(key) ?? []
    bucket.push({ tile, index })
    buckets.set(key, bucket)
  })
  return { tiles, buckets }
}

export function worldTilesNear(index: WorldTileIndex, center: { x: number; y: number }, reach: number) {
  if (reach * 2 >= WORLD_WRAP_TILES) return index.tiles
  const bucketCount = WORLD_WRAP_TILES / CHUNK_SIZE
  const seen = new Set<string>()
  const candidates: IndexedTile[] = []
  for (let y = Math.floor((center.y - reach) / CHUNK_SIZE); y <= Math.floor((center.y + reach) / CHUNK_SIZE); y += 1) {
    for (let x = Math.floor((center.x - reach) / CHUNK_SIZE); x <= Math.floor((center.x + reach) / CHUNK_SIZE); x += 1) {
      const key = `${wrap(x, bucketCount)}:${wrap(y, bucketCount)}`
      if (seen.has(key)) continue
      seen.add(key)
      candidates.push(...(index.buckets.get(key) ?? []))
    }
  }
  candidates.sort((left, right) => left.index - right.index)
  return candidates.map(({ tile }) => tile)
}

function wrap(value: number, size = WORLD_WRAP_TILES) {
  return ((value % size) + size) % size
}
