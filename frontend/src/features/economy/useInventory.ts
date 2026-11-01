import { useQuery } from '@tanstack/react-query'

import { getInventory } from '../../shared/api/economy'
import { useGameStore } from '../../game/state/useGameStore'

export function useInventory() {
  const connected = useGameStore((state) => state.realtimeStatus === 'connected')
  return useQuery({
    queryKey: ['economy', 'inventory'],
    queryFn: getInventory,
    retry: false,
    staleTime: 5000,
    refetchInterval: connected ? 30_000 : 5000,
  })
}

export function inventoryAmount(items: { resource: string; amount: number }[] | undefined, resource: string) {
  return items?.find((item) => item.resource === resource)?.amount ?? 0
}

export function availablePopulation(items: { resource: string; amount: number }[] | undefined) {
  return inventoryAmount(items, 'population')
}
