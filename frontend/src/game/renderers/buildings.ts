import type { PlacedBuilding } from '../state/useGameStore'

export function buildingSortKey(building: PlacedBuilding) {
  return building.tile.x + building.tile.y
}

export function buildingRenderState(building: PlacedBuilding) {
  if (building.health <= 0) {
    return 'ruined'
  }
  if (building.health < 50) {
    return 'damaged'
  }
  return building.status
}
