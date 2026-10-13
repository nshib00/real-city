import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type WoodHouseModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function woodHouseModelLevel(level: number) {
  return Math.max(1, Math.min(6, Math.round(level || 1)))
}

export function woodHouseModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): WoodHouseModelState {
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

export function woodHouseModelClassName(building: Pick<PlacedBuilding, 'level' | 'status' | 'state' | 'health' | 'maxHealth'>) {
  return `wood-house-model wood-house-model-l${String(woodHouseModelLevel(building.level)).padStart(2, '0')} wood-house-model-${woodHouseModelState(building)}`
}
