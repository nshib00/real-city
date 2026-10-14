import { useQuery } from '@tanstack/react-query'

import { CHUNK_SIZE, tileToChunk } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import { listThreats } from '../../shared/api/monsters'

export function useThreatLevel() {
  const selectedTile = useGameStore((state) => state.selectedTile)
  const viewport = useGameStore((state) => state.viewport)
  const centerChunk = tileToChunk(viewport.center)
  const queryCenter = chunkCenterTile(centerChunk)
  const radiusTiles = viewport.radius * CHUNK_SIZE + CHUNK_SIZE
  const query = useQuery({
    queryKey: ['threats', centerChunk.x, centerChunk.y, viewport.radius],
    queryFn: () => listThreats({ x: queryCenter.x, y: queryCenter.y, radius: radiusTiles }),
    retry: false,
    refetchInterval: 12000,
    staleTime: 5000,
  })
  if (!selectedTile || !query.data) {
    return null
  }
  return query.data.threats.find((item) => item.tile_x === selectedTile.x && item.tile_y === selectedTile.y) ?? null
}

function chunkCenterTile(chunk: { x: number; y: number }) {
  return {
    x: chunk.x * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2),
    y: chunk.y * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2),
  }
}
