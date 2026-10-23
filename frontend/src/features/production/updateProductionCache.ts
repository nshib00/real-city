import type { QueryClient } from '@tanstack/react-query'

import type { InventoryResponse, ProductionJobResponse } from '../../shared/api/economy'

type ProductionResult = { job: ProductionJobResponse; inventory?: InventoryResponse }

export async function updateProductionCache(queryClient: QueryClient, result: ProductionResult) {
  await Promise.all([
    queryClient.cancelQueries({ queryKey: ['production', 'jobs'] }),
    queryClient.cancelQueries({ queryKey: ['economy', 'inventory'] }),
  ])

  const jobsKey = ['production', 'jobs'] as const
  const cachedJobs = queryClient.getQueryData<{ jobs: ProductionJobResponse[] }>(jobsKey)
  if (cachedJobs) {
    queryClient.setQueryData(jobsKey, {
      ...cachedJobs,
      jobs: cachedJobs.jobs.some((job) => job.id === result.job.id)
        ? cachedJobs.jobs.map((job) => job.id === result.job.id ? result.job : job)
        : [...cachedJobs.jobs, result.job],
    })
  } else {
    void queryClient.invalidateQueries({ queryKey: jobsKey })
  }

  if (result.inventory) {
    queryClient.setQueryData(['economy', 'inventory'], { inventory: result.inventory })
  } else {
    void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
  }
}
