import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type SeedGardenModelState =
  | 'active'
  | 'construction'
  | 'damaged'
  | 'ruined'
  | `stage${RegularStageId}`
  | `super_stage${SuperStageId}`

type RegularStageId = '01' | '02' | '03'
type SuperStageId = RegularStageId | '04' | '05' | '06'

export function seedGardenModelLevel(level: number) {
  return Math.max(1, Math.min(10, Math.round(level || 1)))
}

export function seedGardenModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth' | 'fieldStage' | 'growthStage' | 'cropStage' | 'superStage' | 'isSuperCrop' | 'superCrop'>): SeedGardenModelState {
  if (building.state === 'ruined' || building.health <= 0) {
    return 'ruined'
  }
  if (building.status === 'construction' || building.state === 'building' || building.state === 'planned') {
    return 'construction'
  }
  if (isCriticallyDamaged(building)) {
    return 'damaged'
  }

  const regularStage = readStage(building.fieldStage, building.growthStage, building.cropStage)
  const superStage = readStage(building.superStage)
  if (superStage) {
    return `super_stage${padSuperStage(superStage)}`
  }
  if ((building.isSuperCrop || building.superCrop) && regularStage) {
    return `super_stage${padSuperStage(regularStage)}`
  }
  if (regularStage) {
    return `stage${padRegularStage(regularStage)}`
  }

  return 'active'
}

function readStage(...values: (number | null | undefined)[]) {
  for (const value of values) {
    if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
      return Math.round(value)
    }
  }
  return null
}

function padRegularStage(stage: number): RegularStageId {
  return String(Math.max(1, Math.min(3, stage))).padStart(2, '0') as RegularStageId
}

function padSuperStage(stage: number): SuperStageId {
  return String(Math.max(1, Math.min(6, stage))).padStart(2, '0') as SuperStageId
}
