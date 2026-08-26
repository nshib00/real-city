import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { listBuildings, toPlacedBuilding } from '../../shared/api/buildings'

export function BuildingSync() {
  const addBuilding = useGameStore((state) => state.addBuilding)
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
  }, [addBuilding, query.data])

  return null
}
