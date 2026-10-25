import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { playUiSound } from '../../audio/playUiSound'
import type { InventoryResponse } from '../../shared/api/economy'
import { playConfirmedCoinChange, playConfirmedRareReward, productionMaterialVariant } from '../economy/economyAudio'
import { listProductionJobs, listProductionRecipes, patchProductionJob, startProduction } from '../../shared/api/economy'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { ResourceIcon } from '../resources/ResourceIcon'
import { formatRemaining } from '../../shared/time/formatRemaining'
import { updateProductionCache } from './updateProductionCache'
import { showToast } from '../notifications/toast'

export function ProductionPanel() {
  const queryClient = useQueryClient()
  const buildings = useGameStore((state) => state.buildings)
  const player = useAuthStore((state) => state.player)
  const recipesQuery = useQuery({ queryKey: ['production', 'recipes'], queryFn: listProductionRecipes, retry: false, staleTime: 5 * 60_000, gcTime: 30 * 60_000 })
  const jobsQuery = useQuery({ queryKey: ['production', 'jobs'], queryFn: listProductionJobs, retry: false, refetchInterval: 5000 })
  const previousJobs = useRef<Map<string, string> | null>(null)
  useEffect(() => {
    if (!jobsQuery.data) return
    const next = new Map(jobsQuery.data.jobs.map((job) => [job.id, job.state]))
    if (previousJobs.current && player?.profile.settings.notifications.production_ready) {
      const ready = jobsQuery.data.jobs.find((job) => job.state === 'ready' && previousJobs.current?.get(job.id) === 'running')
      if (ready) playUiSound('economy.production.ready', productionMaterialVariant(buildings.find((building) => building.id === ready.building_id)?.kind))
    }
    previousJobs.current = next
  }, [buildings, jobsQuery.data, player?.profile.settings.notifications.production_ready])
  const startMutation = useMutation({
    mutationFn: startProduction,
    onSuccess: (result, variables) => {
      playUiSound('economy.production.started', productionMaterialVariant(buildings.find((building) => building.id === variables.building_id)?.kind))
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      void updateProductionCache(queryClient, result)
    },
    onError: (error) => showToast('warning', error instanceof Error ? error.message : 'Не удалось запустить добычу'),
  })
  const patchMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'complete' | 'cancel' }) => patchProductionJob(id, action),
    onSuccess: (result, variables) => {
      if (variables.action === 'complete') {
        playUiSound('economy.production.collected', productionMaterialVariant(buildings.find((building) => building.id === result.job.building_id)?.kind))
        playConfirmedRareReward(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
        playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      }
      void updateProductionCache(queryClient, result)
      if (variables.action === 'complete') void queryClient.invalidateQueries({ queryKey: ['resources', 'nodes'] })
    },
    onError: (error) => showToast('warning', error instanceof Error ? error.message : 'Не удалось завершить добычу'),
  })

  const recipes = recipesQuery.data?.recipes ?? []
  const recipeIds = [...new Set(recipes.map((recipe) => recipe.id))]
  const jobs = jobsQuery.data?.jobs ?? []

  return (
    <aside className="production-panel" aria-label="Производство">
      <h2>Производство</h2>
      <div className="production-recipes">
        {recipeIds.map((recipeId) => {
          const building = buildings.find((item) => item.owner === player?.id && item.status === 'active' && recipes.some((recipe) => recipe.id === recipeId && recipe.building_type === item.kind))
          const recipe = recipes.find((item) => item.id === recipeId && item.required_level === building?.level)
            ?? recipes.find((item) => item.id === recipeId && item.required_level === 0)
            ?? recipes.find((item) => item.id === recipeId)
          if (!recipe) return null
          return (
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
                disabled={!building}
                onClick={() => {
                  if (building) {
                    startMutation.mutate({ building_id: building.id, recipe_id: recipe.id })
                  }
                }}
              >
                Запустить
              </button>
            </article>
          )
        })}
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
  const remainingSeconds = seconds % 60
  return remainingSeconds ? `${minutes} мин. ${remainingSeconds} сек.` : `${minutes} мин.`
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

export { formatSeconds as productionFormatSeconds }
