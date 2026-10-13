import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type TownHallModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function townHallModelLevel(level: number) {
  return Math.max(1, Math.min(10, Math.round(level || 1)))
}

export function townHallModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): TownHallModelState {
  if (building.state === 'ruined' || building.health <= 0) {
    return 'ruined'
  }
  if (building.status === 'construction' || building.state === 'building' || building.state === 'planned') {
    return 'construction'
  }
  if (isCriticallyDamaged(building)) {
    return 'damaged'
  }
  return 'active'
}

export function townHallModelClassName(building: Pick<PlacedBuilding, 'level' | 'status' | 'state' | 'health' | 'maxHealth'>) {
  return `town-hall-model town-hall-model-l${String(townHallModelLevel(building.level)).padStart(2, '0')} town-hall-model-${townHallModelState(building)}`
}
