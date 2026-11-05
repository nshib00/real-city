import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'

import { normalizeChunk } from '../../../../shared/world/coordinates'
import { getChunks } from '../../shared/api/world'
import type { ChunksResponse } from '../../shared/api/world'
import type { WorldChunk } from '../../shared/contracts'

export function useVisibleChunks(center: { x: number; y: number }, radius = 1) {
  const queryClient = useQueryClient()
  return useQuery({
    ...visibleChunksQueryOptions(center, radius, queryClient),
    placeholderData: keepPreviousData,
  })
}

export function visibleChunksQueryOptions(center: { x: number; y: number }, radius = 1, queryClient?: QueryClient) {
  center = normalizeChunk(center)
  const queryKey = ['world', 'chunks', center.x, center.y, radius] as const
  return {
    queryKey,
    queryFn: () => getChunks(center, radius, queryClient?.getQueryData<ChunksResponse>(queryKey)),
    staleTime: 60_000,
    gcTime: 10 * 60_000,
  }
}

export function flattenChunkTiles(chunks: WorldChunk[] | undefined) {
  return [...new Map((chunks?.flatMap((chunk) => chunk.tiles) ?? []).map((tile) => [`${tile.x}:${tile.y}`, tile])).values()]
}
