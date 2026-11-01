import { useQuery } from '@tanstack/react-query'

import { listProductionJobs, type ProductionJobResponse } from '../../shared/api/economy'
import { useGameStore } from '../../game/state/useGameStore'

export function productionJobsPollInterval(jobs: readonly Pick<ProductionJobResponse, 'state'>[] | undefined, connected: boolean) {
  if (jobs?.some((job) => job.state === 'running')) return 5000
  return connected ? 30_000 : 10_000
}

export function useProductionJobs(enabled = true) {
  const connected = useGameStore((state) => state.realtimeStatus === 'connected')
  return useQuery({
    queryKey: ['production', 'jobs'],
    queryFn: listProductionJobs,
    enabled,
    retry: false,
    refetchInterval: (query) => productionJobsPollInterval(query.state.data?.jobs, connected),
  })
}
