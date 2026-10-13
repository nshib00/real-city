import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type MineModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function mineModelLevel(level: number) {
  return Math.max(1, Math.min(12, level || 1))
}

export function mineModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): MineModelState {
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
