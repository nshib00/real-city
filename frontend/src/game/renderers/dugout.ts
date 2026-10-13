import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type DugoutModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function dugoutModelLevel(level: number) {
  return Math.max(1, Math.min(5, Math.round(level || 1)))
}

export function dugoutModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): DugoutModelState {
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

export function dugoutModelClassName(building: Pick<PlacedBuilding, 'level' | 'status' | 'state' | 'health' | 'maxHealth'>) {
  return `dugout-model dugout-model-l${String(dugoutModelLevel(building.level)).padStart(2, '0')} dugout-model-${dugoutModelState(building)}`
}
