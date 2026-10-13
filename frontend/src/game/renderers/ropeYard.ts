import type { PlacedBuilding } from '../state/useGameStore'
import { isCriticallyDamaged } from './buildingDamage'

export type RopeYardModelState =
  | 'active'
  | 'ready'
  | 'idle_no_input'
  | 'idle_no_workers'
  | 'construction'
  | 'damaged'
  | 'ruined'

type RopeYardRuntimeFields = {
  productionState?: string
  workState?: string
  jobState?: string
  ready?: boolean
  productionReady?: boolean
  hasReadyOutput?: boolean
  missingInput?: boolean
  noInput?: boolean
  inputBlocked?: boolean
  noWorkers?: boolean
  missingWorkers?: boolean
  workersBlocked?: boolean
}

export function ropeYardModelLevel(level: number) {
  return Math.max(1, Math.min(8, Math.round(level || 1)))
}

export function ropeYardModelState(building: Pick<PlacedBuilding, 'status' | 'state' | 'health' | 'maxHealth'>): RopeYardModelState {
  if (building.state === 'ruined' || building.health <= 0) {
    return 'ruined'
  }
  if (building.status === 'construction' || building.state === 'building' || building.state === 'planned') {
    return 'construction'
  }
  if (isCriticallyDamaged(building)) {
    return 'damaged'
  }

  const runtime = building as typeof building & RopeYardRuntimeFields
  const productionState = runtime.productionState ?? runtime.workState ?? runtime.jobState

  if (productionState === 'ready' || runtime.ready || runtime.productionReady || runtime.hasReadyOutput) {
    return 'ready'
  }
  if (productionState === 'idle_no_input' || productionState === 'no_input' || runtime.missingInput || runtime.noInput || runtime.inputBlocked) {
    return 'idle_no_input'
  }
  if (productionState === 'idle_no_workers' || productionState === 'no_workers' || runtime.noWorkers || runtime.missingWorkers || runtime.workersBlocked) {
    return 'idle_no_workers'
  }

  return 'active'
}
