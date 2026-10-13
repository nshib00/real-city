import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type LumberYardModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function lumberYardModelLevel(level: number) {
  return Math.max(1, Math.min(13, level || 1))
}

export function lumberYardModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): LumberYardModelState {
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
