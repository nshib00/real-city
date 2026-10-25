import { useGameStore, type PlacedBuilding } from '../game/state/useGameStore'
import { isUiSoundMuted } from './playUiSound'
import { audioManager } from './AudioManager'
import type { SoundId } from './soundEvents'

type AmbienceId = Extract<SoundId, `ambience.${string}`>
const settingKey = 'real-city.audio.ambience-enabled'
const activeIds = new Set<AmbienceId>()
let enabledFallback = false

export function isAmbienceEnabled(): boolean {
  try { return localStorage.getItem(settingKey) === 'true' } catch { return enabledFallback }
}

export function setAmbienceEnabled(enabled: boolean): void {
  enabledFallback = enabled
  try { localStorage.setItem(settingKey, String(enabled)) } catch { /* Настройка действует до перезагрузки. */ }
  if (!enabled) stopAmbience()
}

function localBuildingSound(building: PlacedBuilding): AmbienceId | null {
  if (building.status !== 'active' || building.state === 'ruined') return null
  if (building.kind === 'oil_well') return 'ambience.oil_well'
  if (building.kind.includes('field') || building.kind.includes('garden') || building.kind.includes('bed')) return 'ambience.field'
  if (building.kind.includes('workshop') || building.kind === 'forge' || building.kind === 'foundry') return 'ambience.workshop'
  return null
}

export function selectAmbience(): Map<AmbienceId, number> {
  const state = useGameStore.getState()
  const center = state.viewport.center
  const radius = Math.max(10, state.viewport.radius * 16)
  const counts = new Map<AmbienceId, number>()
  for (const tile of state.worldTiles) {
    const distance = Math.hypot(tile.x - center.x, tile.y - center.y)
    if (distance > radius) continue
    const id: AmbienceId = tile.terrain === 'water' ? 'ambience.river'
      : tile.terrain === 'mountain' ? 'ambience.mountain'
        : tile.terrain === 'ruins' ? 'ambience.ruins'
          : tile.terrain === 'forest' ? 'ambience.forest' : 'ambience.grass'
    counts.set(id, (counts.get(id) ?? 0) + 1 / (1 + distance * 0.1))
  }
  const nearbyBuildings = state.buildings.filter((building) => building.status === 'active' && building.state !== 'ruined' && Math.hypot(building.tile.x - center.x, building.tile.y - center.y) < radius)
  if (nearbyBuildings.length >= 5) counts.set('ambience.town', (counts.get('ambience.town') ?? 0) + nearbyBuildings.length * 0.8)
  const result = new Map<AmbienceId, number>()
  const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 2)
  const total = top.reduce((sum, item) => sum + item[1], 0)
  for (const [id, weight] of top) result.set(id, Math.min(0.12, 0.12 * weight / Math.max(1, total)) * state.camera.zoom)

  const local = nearbyBuildings
    .map((building) => ({ id: localBuildingSound(building), distance: Math.hypot(building.tile.x - center.x, building.tile.y - center.y) }))
    .filter((item): item is { id: AmbienceId; distance: number } => item.id !== null)
    .sort((a, b) => a.distance - b.distance)
  for (const item of local) {
    if (result.size >= 4) break
    if (!result.has(item.id)) result.set(item.id, 0.055 * Math.max(0.25, 1 - item.distance / radius))
  }
  return result
}

function updateTargets(): void {
  const targets = isAmbienceEnabled() && !isUiSoundMuted() && !document.hidden ? selectAmbience() : new Map<AmbienceId, number>()
  for (const id of activeIds) if (!targets.has(id)) { audioManager.setLoop(id, 0); activeIds.delete(id) }
  for (const [id, volume] of targets) { audioManager.setLoop(id, volume); activeIds.add(id) }
}

export function stopAmbience(): void {
  for (const id of activeIds) audioManager.setLoop(id, 0)
  activeIds.clear()
}

export function startAmbience(): () => void {
  if (typeof document === 'undefined' || import.meta.env.MODE === 'test') return () => undefined
  updateTargets()
  const update = window.setInterval(updateTargets, 1200)
  const visibility = () => updateTargets()
  document.addEventListener('visibilitychange', visibility)
  return () => {
    window.clearInterval(update)
    document.removeEventListener('visibilitychange', visibility)
    stopAmbience()
  }
}
