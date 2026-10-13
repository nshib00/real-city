import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type GlassWorkshopModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function glassWorkshopModelLevel(level: number) {
  return Math.max(1, Math.min(12, level || 1))
}

export function glassWorkshopModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): GlassWorkshopModelState {
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
