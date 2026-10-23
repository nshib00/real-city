import { QueryClient } from '@tanstack/react-query'
import { describe, expect, it } from 'vitest'

import type { InventoryResponse, ProductionJobResponse } from '../../shared/api/economy'
import { updateProductionCache } from './updateProductionCache'

describe('updateProductionCache', () => {
  it('shows the returned job and inventory without waiting for another request', async () => {
    const queryClient = new QueryClient()
    const job: ProductionJobResponse = {
      id: 'job-1', building_id: 'building-1', recipe_id: 'planks_from_wood', state: 'running',
      started_at: '2026-10-19T12:00:00Z', completes_at: '2026-10-19T12:05:00Z',
    }
    const inventory: InventoryResponse = {
      player_id: 'player-1', items: [{ resource: 'wood', amount: 10 }],
      coin_capacity: 100, updated_at: '2026-10-19T12:00:00Z',
    }
    queryClient.setQueryData(['production', 'jobs'], { jobs: [] })

    await updateProductionCache(queryClient, { job, inventory })
    expect(queryClient.getQueryData(['production', 'jobs'])).toEqual({ jobs: [job] })
    expect(queryClient.getQueryData(['economy', 'inventory'])).toEqual({ inventory })

    const completed = { ...job, state: 'completed' as const }
    await updateProductionCache(queryClient, { job: completed, inventory })
    expect(queryClient.getQueryData(['production', 'jobs'])).toEqual({ jobs: [completed] })
  })
})
