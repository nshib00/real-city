import { useQuery } from '@tanstack/react-query'

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

