import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { getChunks } from '../../shared/api/world'
import type { WorldChunk } from '../../shared/contracts'

export function useVisibleChunks(center: { x: number; y: number }, radius = 1) {
  return useQuery({
    ...visibleChunksQueryOptions(center, radius),
    placeholderData: keepPreviousData,
  })
}

export function visibleChunksQueryOptions(center: { x: number; y: number }, radius = 1) {
  return {
    queryKey: ['world', 'chunks', center.x, center.y, radius] as const,
    queryFn: () => getChunks(center, radius),
    staleTime: 60_000,
    gcTime: 10 * 60_000,
  }
}

export function flattenChunkTiles(chunks: WorldChunk[] | undefined) {
  return chunks?.flatMap((chunk) => chunk.tiles) ?? []
}
