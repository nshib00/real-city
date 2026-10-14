import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { listProductionJobs, listProductionRecipes, patchProductionJob, startProduction } from '../../shared/api/economy'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { ResourceIcon } from '../resources/ResourceIcon'

export function ProductionPanel() {
  const queryClient = useQueryClient()
  const buildings = useGameStore((state) => state.buildings)
  const player = useAuthStore((state) => state.player)
  const recipesQuery = useQuery({ queryKey: ['production', 'recipes'], queryFn: listProductionRecipes, retry: false, staleTime: 5 * 60_000, gcTime: 30 * 60_000 })
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
              {recipe.output.map((item) => (
                <span key={`${recipe.id}-out-${item.resource}`}>
                  +<ResourceIcon id={item.resource} label={item.resource} /> {item.amount}
                </span>
              ))}
              {recipe.rare_output.map((item) => (
                <span key={`${recipe.id}-rare-${item.resource}`}>
                  +<ResourceIcon id={item.resource} label={item.resource} /> {item.amount} · {formatChance(item.chance)}
                </span>
              ))}
            </div>
            <button
              type="button"
              disabled={!findProductionBuildingId(buildings, player?.id, recipe.building_type)}
              onClick={() => {
                const buildingId = findProductionBuildingId(buildings, player?.id, recipe.building_type)
                if (buildingId) {
                  startMutation.mutate({ building_id: buildingId, recipe_id: recipe.id })
                }
              }}
            >
              Запустить
            </button>
          </article>
        ))}
      </div>
      <div className="production-jobs">
        {jobs.map((job) => (
          <article className="production-job" key={job.id}>
            <strong>{job.recipe_id}</strong>
            <span>{job.state === 'running' ? `готово через ${formatRemaining(Date.parse(job.completes_at) - Date.now())}` : statusLabel[job.state]}</span>
            <button type="button" disabled={job.state !== 'running' && job.state !== 'ready'} onClick={() => patchMutation.mutate({ id: job.id, action: job.state === 'ready' || Date.parse(job.completes_at) <= Date.now() ? 'complete' : 'cancel' })}>
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

function formatChance(chance: number) {
  return `${(chance * 100).toLocaleString('ru-RU', { maximumFractionDigits: 1 })}%`
}

const statusLabel = {
  running: 'в работе',
  ready: 'готово',
  completed: 'собрано',
  cancelled: 'отменено',
} as const

function findProductionBuildingId(buildings: ReturnType<typeof useGameStore.getState>['buildings'], playerId: string | undefined, kind: string) {
  return buildings.find((building) => building.owner === playerId && building.status === 'active' && building.kind === kind)?.id ?? null
}

export { formatSeconds as productionFormatSeconds }
