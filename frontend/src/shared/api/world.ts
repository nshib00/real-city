import { request } from './client'
import type { InventoryResponse } from './economy'
import type { WorldChunk, WorldMap, WorldTile } from '../contracts'
import { normalizeChunk, normalizeTile, visibleChunks } from '../../../../shared/world/coordinates'

export type ChunksResponse = {
  chunks: WorldChunk[]
}

export function getWorld() {
  return request<WorldMap>('/world')
}

export async function getChunks(center: { x: number; y: number }, radius = 1, previous?: ChunksResponse) {
  center = normalizeChunk(center)
  const params = new URLSearchParams({
    x: String(center.x),
    y: String(center.y),
    radius: String(radius),
  })
  const requested = new Set(visibleChunks(center, radius).map((chunk) => `${chunk.x}:${chunk.y}`))
  const known = previous?.chunks.filter((chunk) => requested.has(`${chunk.chunk_x}:${chunk.chunk_y}`)) ?? []
  if (known.length) params.set('known', known.map((chunk) => `${chunk.chunk_x}:${chunk.chunk_y}:${chunk.version}`).join(','))
  const response = await request<ChunksResponse>(`/world/chunks?${params.toString()}`)
  if (!known.length) return response
  const merged = new Map(known.map((chunk) => [`${chunk.chunk_x}:${chunk.chunk_y}`, chunk]))
  for (const chunk of response.chunks) merged.set(`${chunk.chunk_x}:${chunk.chunk_y}`, chunk)
  return { chunks: [...merged.entries()].filter(([key]) => requested.has(key)).map(([, chunk]) => chunk) }
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
