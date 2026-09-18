import { useQuery } from '@tanstack/react-query'

import { useGameStore } from '../../game/state/useGameStore'
import { listThreats } from '../../shared/api/monsters'

export function useThreatLevel() {
  const selectedTile = useGameStore((state) => state.selectedTile)
  const viewport = useGameStore((state) => state.viewport)
  const query = useQuery({
    queryKey: ['threats', viewport.center.x, viewport.center.y, viewport.radius],
    queryFn: () => listThreats({ x: viewport.center.x, y: viewport.center.y, radius: viewport.radius * 48 }),
    retry: false,
    refetchInterval: 12000,
  })
  if (!selectedTile || !query.data) {
    return null
  }
  return query.data.threats.find((item) => item.tile_x === selectedTile.x && item.tile_y === selectedTile.y) ?? null
}
