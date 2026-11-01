import { describe, it, expect } from 'vitest'
import { visibleChunks, normalizeChunk, normalizeTile, wrappedDistance } from '../../../../shared/world/coordinates'
import { visibleChunksQueryOptions, flattenChunkTiles } from './useVisibleChunks'
describe('toroidal viewport', () => {
 it('normalizes negative tiles and aliases chunk caches', () => {
  expect(normalizeTile({ x:-1,y:320 })).toEqual({ x:159,y:0 })
  expect(normalizeChunk({ x:-1,y:5 })).toEqual({ x:4,y:0 })
  expect(visibleChunksQueryOptions({ x:-1,y:5 }).queryKey).toEqual(visibleChunksQueryOptions({ x:4,y:0 }).queryKey)
  expect(wrappedDistance(159,0)).toBe(1)
 })
 it('loads each chunk once around both seams', () => {
  const chunks=visibleChunks({x:0,y:0},3)
  expect(chunks).toHaveLength(25)
  expect(new Set(chunks.map(c=>`${c.x}:${c.y}`)).size).toBe(25)
  expect(flattenChunkTiles(undefined)).toEqual([])
 })
})
