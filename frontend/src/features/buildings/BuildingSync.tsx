import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { tileToChunk, wrapGridCoord } from '../../game/coordinates/iso'
import { listBuildings, listVisibleBuildings, toPlacedBuilding } from '../../shared/api/buildings'
import { useAuthStore } from '../auth/useAuthStore'
import { playBuildingSound } from './buildingAudio'
import { showToast } from '../notifications/toast'

export function BuildingSync() {
  const addBuilding = useGameStore((state) => state.addBuilding)
  const focusTile = useGameStore((state) => state.focusTile)
  const player = useAuthStore((state) => state.player)
  const viewport = useGameStore((state) => state.viewport)
  const center = tileToChunk(wrapGridCoord(viewport.center))
  const focusedPlayerIdRef = useRef<string | null>(null)
  const knownStatesRef = useRef<Map<string, { state: string; level: number }> | null>(null)
  const query = useQuery({
    queryKey: ['buildings'],
    queryFn: listBuildings,
    retry: false,
  })
  const visibleQuery = useQuery({
    queryKey: ['buildings', 'visible', center.x, center.y, viewport.radius],
    queryFn: () => listVisibleBuildings(center, viewport.radius),
    retry: false,
    staleTime: 10_000,
  })

  useEffect(() => {
    for (const building of visibleQuery.data?.buildings ?? []) {
      addBuilding(toPlacedBuilding(building))
    }
  }, [addBuilding, visibleQuery.data])

  useEffect(() => {
    if (!query.data) {
      return
    }
    const previous = knownStatesRef.current
    const next = new Map(query.data.buildings.map((building) => [building.id, { state: building.state, level: building.level }]))
    if (!previous && player) {
      try {
        const key = `real-city.audio.construction.${player.id}`
        const saved = JSON.parse(window.localStorage.getItem(key) ?? '[]') as string[]
        const completed = query.data.buildings.filter((building) => building.owner_id === player.id && saved.includes(building.id) && building.state === 'active')
        if (completed.length) showToast('info', completed.length === 1 ? `Строительство завершено: ${completed[0].name}` : `Завершено построек: ${completed.length}`)
      } catch {
        // Без локального хранилища офлайн-уведомление недоступно.
      }
    }
    if (previous && player) {
      for (const building of query.data.buildings) {
        const before = previous.get(building.id)
        if (building.owner_id === player.id && before?.state === 'building' && building.state === 'active') {
          const upgraded = building.created_at ? Date.parse(building.started_at) > Date.parse(building.created_at) : before.level < building.level
          playBuildingSound(upgraded ? 'build.upgrade.completed' : 'build.completed', building.id, 'completion')
        }
      }
    }
    knownStatesRef.current = next
    if (player) {
      try {
        window.localStorage.setItem(`real-city.audio.construction.${player.id}`, JSON.stringify(query.data.buildings.filter((building) => building.owner_id === player.id && building.state === 'building').map((building) => building.id)))
      } catch {
        // Настройка может быть заблокирована браузером.
      }
    }
    for (const building of query.data.buildings) {
      addBuilding(toPlacedBuilding(building))
    }
    if (player && focusedPlayerIdRef.current !== player.id) {
      const townHall = query.data.buildings.find((building) => building.owner_id === player.id && building.type === 'town_hall')
      if (townHall) {
        focusTile({
          tile: { x: townHall.tile_x, y: townHall.tile_y },
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight,
        })
        focusedPlayerIdRef.current = player.id
      }
    }
  }, [addBuilding, focusTile, player, query.data])

  return null
}
