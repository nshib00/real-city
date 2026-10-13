import { useQuery } from '@tanstack/react-query'

import type { PlacedBuilding } from '../../game/state/useGameStore'
import { getInventory } from '../../shared/api/economy'

export function useInventory() {
  return useQuery({
    queryKey: ['economy', 'inventory'],
    queryFn: getInventory,
    retry: false,
    staleTime: 5000,
  })
}

export function inventoryAmount(items: { resource: string; amount: number }[] | undefined, resource: string) {
  return items?.find((item) => item.resource === resource)?.amount ?? 0
}

export function availablePopulation(
  items: { resource: string; amount: number }[] | undefined,
  buildings: PlacedBuilding[] = [],
  ownerId?: string,
) {
  const serverAmount = inventoryAmount(items, 'population')
  if (serverAmount > 0) {
    return serverAmount
  }
  const ownerBuildings = ownerId ? buildings.filter((building) => building.owner === ownerId) : buildings
  const hasActiveTownHall = ownerBuildings.some((building) => building.kind === 'town_hall' && building.status === 'active' && building.state !== 'ruined')
  const hasActiveConstruction = ownerBuildings.some((building) => building.status === 'construction' || building.state === 'building' || building.state === 'planned')
  return hasActiveTownHall && !hasActiveConstruction ? 3 : serverAmount
}
