import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { playUiSound } from '../../audio/playUiSound'
import type { InventoryResponse } from '../../shared/api/economy'
import { playConfirmedCoinChange, playConfirmedRareReward, productionMaterialVariant } from '../economy/economyAudio'
import { listProductionRecipes, patchProductionJob, startProduction } from '../../shared/api/economy'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { ResourceIcon } from '../resources/ResourceIcon'
import { formatRemaining } from '../../shared/time/formatRemaining'
import { updateProductionCache } from './updateProductionCache'
import { useProductionJobs } from './useProductionJobs'
import { showToast } from '../notifications/toast'
import { useInventory, inventoryAmount, availablePopulation } from '../economy/useInventory'

export function ProductionPanel() {
  const [expanded, setExpanded] = useState(() => !window.matchMedia?.('(max-width: 760px), (max-height: 500px) and (max-width: 1000px)').matches)
  const queryClient = useQueryClient()
  const buildings = useGameStore((state) => state.buildings)
  const player = useAuthStore((state) => state.player)
  const now = useGameStore((state) => state.constructionNow)
  const inventoryQuery = useInventory()
  const inventory = inventoryQuery.data?.inventory.items
  const recipesQuery = useQuery({ queryKey: ['production', 'recipes'], queryFn: listProductionRecipes, retry: false, staleTime: 5 * 60_000, gcTime: 30 * 60_000 })
  const jobsQuery = useProductionJobs()
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
      <details open={expanded} onToggle={(event) => setExpanded(event.currentTarget.open)}>
      <summary><h2>Производство</h2></summary>
      {recipesQuery.isPending || jobsQuery.isPending ? <p role="status">Загружаем рецепты и задания…</p> : null}
      {recipesQuery.error || jobsQuery.error ? <p role="alert">Не удалось обновить производство. <button type="button" onClick={() => { void recipesQuery.refetch(); void jobsQuery.refetch() }}>Повторить</button></p> : null}
      {!recipesQuery.isPending && !recipesQuery.error && !recipes.length ? <p>Рецептов пока нет. Осмотрите доступные производственные здания в каталоге.</p> : null}
      <div className="production-recipes">
        {recipeIds.map((recipeId) => {
          const building = buildings.find((item) => item.owner === player?.id && item.status === 'active' && recipes.some((recipe) => recipe.id === recipeId && recipe.building_type === item.kind && recipe.required_level <= item.level))
          const recipe = recipes.find((item) => item.id === recipeId && item.required_level === building?.level)
            ?? recipes.find((item) => item.id === recipeId && item.required_level === 0)
            ?? recipes.find((item) => item.id === recipeId)
          if (!recipe) return null
          const shortage = recipe.input.find((item) => inventoryAmount(inventory, item.resource) < item.amount)
          const busy = building && jobs.some((job) => job.building_id === building.id && ['running', 'ready'].includes(job.state))
          const blocked = !building ? 'Нужна действующая постройка этого типа.' : !inventory ? 'Ожидаем данные о запасах.' : busy ? 'В здании уже есть задание. Завершите или отмените его.' : shortage ? `Не хватает ресурса: ${shortage.resource} (${inventoryAmount(inventory, shortage.resource)}/${shortage.amount}).` : availablePopulation(inventory) < recipe.workers ? `Нужно свободных рабочих: ${recipe.workers}.` : null
          return (
            <article className="production-card" key={recipe.id}>
              <strong>{recipe.name}</strong>
              <span>{formatSeconds(recipe.duration_sec)} · рабочих {recipe.workers}</span>
              <div className="production-cost">
                <small>Расход:</small>
                {recipe.input.map((item) => (
                  <span key={`${recipe.id}-${item.resource}`}>
                    <ResourceIcon id={item.resource} label={item.resource} /> {item.amount}
                  </span>
                ))}
                <small>Результат:</small>
                {recipe.output.map((item) => (
                  <span key={`${recipe.id}-out-${item.resource}`}>
                    +<ResourceIcon id={item.resource} label={item.resource} /> {item.amount}
                  </span>
                ))}
                {recipe.rare_output.length ? <small>Возможный редкий результат:</small> : null}
                {recipe.rare_output.map((item, index) => (
                  <span key={`${recipe.id}-rare-${item.resource}-${index}`}>
                    +<ResourceIcon id={item.resource} label={item.resource} /> {item.amount} · {formatChance(item.chance)}
                  </span>
                ))}
              </div>
              {recipe.rare_output.some((item, index, items) => items.findIndex((other) => other.resource === item.resource) !== index) ? <small>Редкие количества одного ресурса — альтернативные результаты.</small> : null}
              <button
                type="button"
                disabled={Boolean(blocked) || startMutation.isPending}
                onClick={() => {
                  if (building) {
                    startMutation.mutate({ building_id: building.id, recipe_id: recipe.id })
                  }
                }}
              >
                Запустить
              </button>
              {blocked ? <small>{blocked}</small> : null}
            </article>
          )
        })}
      </div>
      <div className="production-jobs">
        <h3>Задания</h3>
        {!jobsQuery.isPending && !jobsQuery.error && !jobs.length ? <p>Заданий нет. Выберите рецепт и запустите производство.</p> : null}
        {jobs.map((job) => (
          <article className="production-job" key={job.id}>
            <strong>{recipes.find((recipe) => recipe.id === job.recipe_id)?.name ?? job.recipe_id}</strong>
            <span>{job.state === 'running' ? Date.parse(job.completes_at) > now ? `готово через ${formatRemaining(Date.parse(job.completes_at) - now)}` : 'Ожидаем подтверждения готовности сервером' : statusLabel[job.state]}</span>
            {job.state === 'running' ? <progress aria-label="Прогресс производства" max={Math.max(1, Date.parse(job.completes_at) - Date.parse(job.started_at))} value={Math.max(0, Math.min(now, Date.parse(job.completes_at)) - Date.parse(job.started_at))} /> : null}
            <button type="button" disabled={patchMutation.isPending || (job.state !== 'running' && job.state !== 'ready')} onClick={() => patchMutation.mutate({ id: job.id, action: job.state === 'ready' ? 'complete' : 'cancel' })}>
              {job.state === 'ready' ? 'Собрать' : job.state === 'running' ? 'Отменить' : statusLabel[job.state]}
            </button>
          </article>
        ))}
      </div>
      </details>
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
