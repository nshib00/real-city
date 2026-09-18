import type { PlacedBuilding } from '../state/useGameStore'

export type TownHallModelState = 'active' | 'construction' | 'damaged' | 'ruined'

export function townHallModelLevel(level: number) {
  return Math.max(1, Math.min(10, Math.round(level || 1)))
}

export function townHallModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health'>): TownHallModelState {
  if (building.state === 'ruined' || building.health <= 0) {
    return 'ruined'
  }
  if (building.status === 'construction' || building.state === 'building' || building.state === 'planned') {
    return 'construction'
  }
  if (building.state === 'damaged' || building.health < 250) {
    return 'damaged'
  }
  return 'active'
}

export function townHallModelClassName(building: Pick<PlacedBuilding, 'level' | 'status' | 'state' | 'health'>) {
  return `town-hall-model town-hall-model-l${String(townHallModelLevel(building.level)).padStart(2, '0')} town-hall-model-${townHallModelState(building)}`
}
