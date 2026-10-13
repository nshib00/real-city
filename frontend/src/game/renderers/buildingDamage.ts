import type { PlacedBuilding } from '../state/useGameStore'

export type DamageStateInput = Pick<PlacedBuilding, 'health' | 'maxHealth'>

export function isCriticallyDamaged(building: DamageStateInput) {
  const maxHealth = Math.max(1, building.maxHealth ?? 100)
  return building.health > 0 && building.health <= maxHealth * 0.2
}
