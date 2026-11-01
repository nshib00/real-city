import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { createPortal } from 'react-dom'
import { useQueryClient } from '@tanstack/react-query'

import type { WorldTile } from '../../shared/contracts'
import type { MonsterEntity, PlacedBuilding } from '../../game/state/useGameStore'
import type { useVisibleChunks } from '../world/useVisibleChunks'
import { initialAssetTasks, loadInitialAssetTasks, type InitialAssetProgress, type InitialAssetTask } from './initialAssets'
import { LoadingScreenView } from './LoadingScreenView'

type Props = {
  query: ReturnType<typeof useVisibleChunks>
  tiles: WorldTile[]
  buildings: PlacedBuilding[]
  allBuildings: PlacedBuilding[]
  monsters: MonsterEntity[]
  rendererReady: boolean
  rendererFailed: boolean
  stageReady: boolean
  retryRenderer: () => void
}

const emptyProgress: InitialAssetProgress = { loaded: 0, failed: 0, total: 0, group: 'terrain' }
const groupLabels = {
  terrain: 'Загрузка мира…',
  objects: 'Загрузка графики…',
  interface: 'Загрузка оформления…',
}

export function InitialLoadingScreen({ query, tiles, buildings, allBuildings, monsters, rendererReady, rendererFailed, stageReady, retryRenderer }: Props) {
  const queryClient = useQueryClient()
  const initialQueriesSettled = useSyncExternalStore(
    (notify) => queryClient.getQueryCache().subscribe(notify),
    () => initialWorldQueriesSettled(queryClient),
    () => false,
  )
  const [canStart, setCanStart] = useState(false)
  const [progress, setProgress] = useState(emptyProgress)
  const [attempt, setAttempt] = useState(0)
  const [finished, setFinished] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const [slow, setSlow] = useState(false)
  const tasksRef = useRef<InitialAssetTask[] | null>(null)
  const completedRef = useRef(new Set<string>())
  const runningRef = useRef(false)

  useEffect(() => {
    if (!query.data || query.isPlaceholderData || !tiles.length || !initialQueriesSettled || !stageReady) return
    // Let the synchronization effects publish their first objects to the store.
    const timer = window.setTimeout(() => setCanStart(true), 0)
    return () => window.clearTimeout(timer)
  }, [query.data, query.isPlaceholderData, tiles.length, initialQueriesSettled, stageReady])

  useEffect(() => {
    if (!canStart || dismissed || runningRef.current) return
    if (!tasksRef.current) tasksRef.current = initialAssetTasks({ tiles, buildings, allBuildings, monsters })
    const tasks = tasksRef.current
    let active = true
    runningRef.current = true
    setFinished(false)
    void loadInitialAssetTasks(tasks, completedRef.current, (next) => {
      if (active) setProgress(next)
    }).then((result) => {
      if (!active) return
      if (attempt > 0 && result.failed === 0) window.dispatchEvent(new Event('real-city:retry-map-assets'))
      setProgress((previous) => ({ ...previous, ...result }))
      setFinished(true)
    }).finally(() => { runningRef.current = false })
    return () => { active = false }
  }, [canStart, attempt, dismissed])

  useEffect(() => {
    if (!finished || progress.failed || !rendererReady || dismissed) return
    let secondFrame = 0
    const firstFrame = requestAnimationFrame(() => {
      secondFrame = requestAnimationFrame(() => setDismissed(true))
    })
    return () => { cancelAnimationFrame(firstFrame); cancelAnimationFrame(secondFrame) }
  }, [finished, progress.failed, rendererReady, dismissed])

  useEffect(() => {
    if (dismissed) return
    const shell = document.querySelector<HTMLElement>('.game-shell')
    if (shell) {
      shell.inert = true
      shell.setAttribute('aria-busy', 'true')
    }
    return () => {
      if (shell) {
        shell.inert = false
        shell.removeAttribute('aria-busy')
      }
    }
  }, [dismissed])

  useEffect(() => {
    if (dismissed) return
    const timer = window.setTimeout(() => setSlow(true), 8000)
    return () => window.clearTimeout(timer)
  }, [dismissed])

  if (dismissed) return null

  const failed = finished && progress.failed > 0
  const worldFailed = (query.isError && !query.data) || (Boolean(query.data) && !query.isPlaceholderData && tiles.length === 0)
  const message = worldFailed ? 'Не удалось загрузить мир.'
    : rendererFailed ? 'Не удалось открыть карту.'
      : failed ? 'Не удалось загрузить часть графики.'
        : !canStart ? 'Подготавливаем мир…'
          : finished ? 'Открываем мир…'
            : groupLabels[progress.group]

  return createPortal(
    <LoadingScreenView loaded={progress.loaded} total={progress.total} message={message} busy={!failed && !worldFailed && !rendererFailed} hint={slow && !failed && !worldFailed && !rendererFailed ? 'Загрузка занимает больше времени. Можно подождать.' : undefined}>
        {worldFailed ? <button type="button" disabled={query.isFetching} onClick={() => { setSlow(false); void query.refetch() }}>Повторить загрузку</button> : null}
        {rendererFailed && !worldFailed ? <button type="button" onClick={retryRenderer}>Повторить запуск карты</button> : null}
        {failed && !worldFailed && !rendererFailed ? <div className="initial-loading-actions">
          <button type="button" onClick={() => { setSlow(false); setAttempt((value) => value + 1) }}>Повторить загрузку</button>
          {rendererReady ? <button type="button" onClick={() => setDismissed(true)}>Продолжить с упрощённой графикой</button> : null}
        </div> : null}
    </LoadingScreenView>, document.body,
  )
}

function initialWorldQueriesSettled(queryClient: ReturnType<typeof useQueryClient>) {
  const active = (queryKey: string[], exact = false) => queryClient.getQueryCache()
    .findAll({ queryKey, exact })
    .filter((query) => query.isActive())
  const groups = [
    active(['buildings'], true),
    active(['buildings', 'visible']),
    active(['resources', 'nodes'], true),
    active(['monsters']),
  ]
  return groups.every((queries) => queries.length > 0 && queries.every((query) => query.state.status !== 'pending' && query.state.fetchStatus === 'idle'))
}
