import { useQuery } from '@tanstack/react-query'

import { getChunks } from '../../shared/api/world'
import type { WorldChunk } from '../../shared/contracts'

export function useVisibleChunks(center: { x: number; y: number }, radius = 1) {
  return useQuery({
    queryKey: ['world', 'chunks', center.x, center.y, radius],
    queryFn: () => getChunks(center, radius),
    placeholderData: (previous) => previous,
  })
}

export function flattenChunkTiles(chunks: WorldChunk[] | undefined) {
  return chunks?.flatMap((chunk) => chunk.tiles) ?? []
}
