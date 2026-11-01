import config from '../../data/world/config.json'
export const WORLD_SIZE = config.size_tiles
export const CHUNK_SIZE = config.chunk_size
export function wrapNumber(value: number, size = WORLD_SIZE) { return ((value % size) + size) % size }
export function normalizeTile(coord: { x: number; y: number }) { return { x: wrapNumber(coord.x), y: wrapNumber(coord.y) } }
export function normalizeChunk(coord: { x: number; y: number }) { return { x: wrapNumber(coord.x, WORLD_SIZE / CHUNK_SIZE), y: wrapNumber(coord.y, WORLD_SIZE / CHUNK_SIZE) } }
export function wrappedDistance(a: number, b: number) { const d = wrapNumber(a - b); return Math.min(d, WORLD_SIZE - d) }
export function visibleChunks(center: { x: number; y: number }, radius: number) {
 const seen = new Map<string, { x: number; y: number }>()
 for (let y = center.y - radius; y <= center.y + radius; y++) for (let x = center.x - radius; x <= center.x + radius; x++) {
  const chunk = normalizeChunk({ x, y }); seen.set(`${chunk.x}:${chunk.y}`, chunk)
 }
 return [...seen.values()]
}
