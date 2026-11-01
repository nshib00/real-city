import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { listBuildings } from '../../shared/api/buildings'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { buildCatalog } from './catalog'

export function FirstCityHelp() {
  const playerId = useAuthStore(state => state.player?.id)
  const buildings = useGameStore(state => state.buildings)
  const open = useGameStore(state => state.uiPreferences.buildMenuOpen)
  const setOpen = useGameStore(state => state.setBuildMenuOpen)
  const preview = useGameStore(state => state.setPlacementPreviewKind)
  const key = `real-city.first-city-help.${playerId}`
  const [dismissed, setDismissed] = useState(() => { try { return localStorage.getItem(key) === 'dismissed' } catch { return false } })
  const query = useQuery({ queryKey: ['buildings'], queryFn: listBuildings, retry: false })
  const center = buildCatalog.find(item => item.kind === 'town_hall')!
  if (!playerId || dismissed || open || !query.data || query.data.buildings.some(item => item.owner_id === playerId && item.type === 'town_hall') || buildings.some(item => item.owner === playerId && item.kind === 'town_hall')) return null
  return <aside className="first-city-help" aria-label="Первый город">
    <h2>Выберите место для центра</h2>
    <button type="button" onClick={() => { setDismissed(true); try { localStorage.setItem(key, 'dismissed') } catch { /* Помощь закрыта до перезагрузки. */ } }}>Закрыть помощь</button>
    <p>Нажмите свободную клетку на карте и откройте строительство. Центр открывает остальные постройки.</p>
    <p>{center.name}: {center.free ? 'бесплатно' : center.cost.map(item => `${item.amount} ${item.label}`).join(', ')}. Размер: {center.footprint.width} × {center.footprint.height}. Лес нужно срубить; реки, горы и руины не подходят. Окончательные правила проверяет сервер.</p>
    <button type="button" onClick={() => { preview('town_hall'); setOpen(true) }}>Выбрать место на карте</button>
  </aside>
}
