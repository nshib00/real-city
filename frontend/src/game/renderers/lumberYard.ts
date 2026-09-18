import type { PlacedBuilding } from '../state/useGameStore'

export type LumberYardModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function lumberYardModelLevel(level: number) {
  return Math.max(1, Math.min(13, level || 1))
}

export function lumberYardModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health'>): LumberYardModelState {
  if (building.status === 'construction') {
    return 'construction'
  }
  if (building.state === 'ruined') {
    return 'ruined'
  }
  if (building.state === 'damaged' || building.health < 55) {
    return 'damaged'
  }
  return 'active'
}
