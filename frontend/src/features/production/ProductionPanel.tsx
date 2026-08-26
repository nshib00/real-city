import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { listProductionJobs, listProductionRecipes, patchProductionJob, startProduction } from '../../shared/api/economy'
import { ResourceIcon } from '../resources/ResourceIcon'

export function ProductionPanel() {
  const queryClient = useQueryClient()
  const recipesQuery = useQuery({ queryKey: ['production', 'recipes'], queryFn: listProductionRecipes, retry: false })
  const jobsQuery = useQuery({ queryKey: ['production', 'jobs'], queryFn: listProductionJobs, retry: false, refetchInterval: 5000 })
  const startMutation = useMutation({
    mutationFn: startProduction,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['production'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const patchMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'complete' | 'cancel' }) => patchProductionJob(id, action),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['production'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })

  const recipes = recipesQuery.data?.recipes ?? []
  const jobs = jobsQuery.data?.jobs ?? []

  return (
    <aside className="production-panel" aria-label="Производство">
      <h2>Производство</h2>
      <div className="production-recipes">
        {recipes.map((recipe) => (
          <article className="production-card" key={recipe.id}>
            <strong>{recipe.name}</strong>
            <span>{formatSeconds(recipe.duration_sec)} · рабочих {recipe.workers}</span>
            <div className="production-cost">
              {recipe.input.map((item) => (
                <span key={`${recipe.id}-${item.resource}`}>
                  <ResourceIcon id={item.resource} label={item.resource} /> {item.amount}
                </span>
              ))}
            </div>
            <button type="button" onClick={() => startMutation.mutate({ building_id: recipe.building_type, recipe_id: recipe.id })}>Запустить</button>
          </article>
        ))}
      </div>
      <div className="production-jobs">
        {jobs.map((job) => (
          <article className="production-job" key={job.id}>
            <strong>{job.recipe_id}</strong>
            <span>{job.state === 'running' ? `готово через ${formatRemaining(Date.parse(job.completes_at) - Date.now())}` : statusLabel[job.state]}</span>
            <button type="button" disabled={job.state !== 'running'} onClick={() => patchMutation.mutate({ id: job.id, action: Date.parse(job.completes_at) <= Date.now() ? 'complete' : 'cancel' })}>
              {Date.parse(job.completes_at) <= Date.now() ? 'Собрать' : 'Отменить'}
            </button>
          </article>
        ))}
      </div>
    </aside>
  )
}

function formatSeconds(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  return `${minutes} мин.`
}

function formatRemaining(ms: number) {
  const seconds = Math.max(0, Math.ceil(ms / 1000))
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}

const statusLabel = {
  running: 'в работе',
  completed: 'собрано',
  cancelled: 'отменено',
} as const

export { formatSeconds as productionFormatSeconds }

