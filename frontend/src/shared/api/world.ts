import { request } from './client'
import type { InventoryResponse } from './economy'
import type { WorldChunk, WorldMap, WorldTile } from '../contracts'
import { normalizeChunk, normalizeTile } from '../../../../shared/world/coordinates'

export type ChunksResponse = {
  chunks: WorldChunk[]
}

export function getWorld() {
  return request<WorldMap>('/world')
}

export function getChunks(center: { x: number; y: number }, radius = 1) {
  center = normalizeChunk(center)
  const params = new URLSearchParams({
    x: String(center.x),
    y: String(center.y),
    radius: String(radius),
  })
  return request<ChunksResponse>(`/world/chunks?${params.toString()}`)
}

export function getViewport(center: { x: number; y: number }, radius = 48) {
  center = normalizeTile(center)
  const params = new URLSearchParams({
    x: String(center.x),
    y: String(center.y),
    radius: String(radius),
  })
  return request<ChunksResponse>(`/world/viewport?${params.toString()}`)
}

export function chopForest(tile: { x: number; y: number }) {
  tile = normalizeTile(tile)
  return request<{ tile: WorldTile; inventory: InventoryResponse }>('/world/tiles/chop-forest', {
    method: 'POST',
    body: JSON.stringify({ tile_x: tile.x, tile_y: tile.y }),
  })
}
