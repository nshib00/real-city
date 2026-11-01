import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'

import { CHUNK_SIZE, tileToChunk } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import { listMonsters, toMonster } from '../../shared/api/monsters'

export function MonsterSync() {
  const viewport = useGameStore((state) => state.viewport)
  const setMonsters = useGameStore((state) => state.setMonsters)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const centerChunk = tileToChunk(viewport.center)
  const queryCenter = chunkCenterTile(centerChunk)
  const radiusTiles = viewport.radius * CHUNK_SIZE + CHUNK_SIZE
  const query = useQuery({
    queryKey: ['monsters', centerChunk.x, centerChunk.y, viewport.radius],
    queryFn: () => listMonsters({ x: queryCenter.x, y: queryCenter.y, radius: radiusTiles }),
    retry: false,
    refetchInterval: realtimeStatus === 'connected' ? 60_000 : 8000,
    staleTime: 5000,
  })

  useEffect(() => {
    if (query.data) {
      setMonsters(query.data.monsters.map(toMonster))
    }
  }, [query.data, setMonsters])

  return null
}

function chunkCenterTile(chunk: { x: number; y: number }) {
  return {
    x: chunk.x * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2),
    y: chunk.y * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2),
  }
}
