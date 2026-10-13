import type { PlacedBuilding } from '../state/useGameStore'
import { resolveBuildingModelAsset } from './buildingRegistry'

export function buildingModelAsset(building: PlacedBuilding) {
  return resolveBuildingModelAsset(building)
}
