import type { SoundId } from '../../audio/soundEvents'
import { playUiSound } from '../../audio/playUiSound'
import type { BuildingResponse } from '../../shared/api/buildings'
import type { PlacedBuilding } from '../../game/state/useGameStore'

const recentlyPlayed = new Map<string, number>()
let lastRoadSoundAt = -Infinity

export function placementSound(type: string, state: string): SoundId {
  if (type.endsWith('_wall')) return 'build.wall.placed'
  if (type === 'road' || type.endsWith('_road')) return 'build.road.placed'
  return state === 'building' ? 'build.started' : 'build.placed'
}

export function placementMaterialVariant(type: string): number | undefined {
  if (type === 'road' || type === 'wooden_wall') return 0
  if (type === 'standard_road' || type === 'paved_road' || type === 'stone_wall') return 1
  if (type === 'concrete_wall' || type === 'modern_wall') return 2
  return undefined
}

export function damageSound(previous: Pick<PlacedBuilding, 'health' | 'maxHealth' | 'state'> | undefined, next: Pick<BuildingResponse, 'health' | 'max_health' | 'state'>): SoundId | null {
  if (!previous || next.health >= previous.health) return null
  if (next.state === 'ruined' || next.health <= 0) return 'build.damaged.ruined'
  const maximum = next.max_health ?? previous.maxHealth ?? Math.max(previous.health, 1)
  return (previous.health - next.health) / maximum >= 0.25 ? 'build.damaged.heavy' : 'build.damaged.light'
}

export function playBuildingSound(id: SoundId, buildingId: string, action: string, interval = 1200, variantIndex?: number, volumeScale = 1): void {
  const key = `${buildingId}:${action}`
  const now = Date.now()
  if (now - (recentlyPlayed.get(key) ?? -Infinity) < interval) return
  recentlyPlayed.set(key, now)
  if (id === 'build.road.placed') {
    if (now - lastRoadSoundAt < 300) return
    lastRoadSoundAt = now
  }
  if (recentlyPlayed.size > 300) {
    for (const [oldKey, timestamp] of recentlyPlayed) if (now - timestamp > 30_000) recentlyPlayed.delete(oldKey)
  }
  playUiSound(id, variantIndex, volumeScale)
}
