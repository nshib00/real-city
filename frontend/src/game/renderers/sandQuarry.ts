import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type SandQuarryModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function sandQuarryModelLevel(level: number) {
  return Math.max(1, Math.min(11, level || 1))
}

export function sandQuarryModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): SandQuarryModelState {
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
