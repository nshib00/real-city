import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { listBuildings, toPlacedBuilding } from '../../shared/api/buildings'
import { useAuthStore } from '../auth/useAuthStore'

export function BuildingSync() {
  const addBuilding = useGameStore((state) => state.addBuilding)
  const focusTile = useGameStore((state) => state.focusTile)
  const player = useAuthStore((state) => state.player)
  const focusedPlayerIdRef = useRef<string | null>(null)
  const query = useQuery({
    queryKey: ['buildings'],
    queryFn: listBuildings,
    retry: false,
  })

  useEffect(() => {
    if (!query.data) {
      return
    }
    for (const building of query.data.buildings) {
      addBuilding(toPlacedBuilding(building))
    }
    if (player && focusedPlayerIdRef.current !== player.id) {
      const townHall = query.data.buildings.find((building) => building.owner_id === player.id && building.type === 'town_hall')
      if (townHall) {
        focusTile({
          tile: { x: townHall.tile_x, y: townHall.tile_y },
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight,
        })
        focusedPlayerIdRef.current = player.id
      }
    }
  }, [addBuilding, focusTile, player, query.data])

  return null
}
