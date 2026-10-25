import { buildingCatalog } from '../../../shared/catalog/buildings'
import type { PlacedBuilding } from './state/useGameStore'

export function healthRatio(health: number, maxHealth: number): number {
  if (!Number.isFinite(health) || !Number.isFinite(maxHealth) || maxHealth <= 0) return 0
  return Math.max(0, Math.min(1, health / maxHealth))
}

export function healthBarColor(ratio: number): number {
  if (ratio >= 0.85) return 0xa8f0a0 // светло-зеленый, светлее следующего диапазона
  if (ratio >= 0.65) return 0x66d17a // светло-зеленый
  if (ratio >= 0.45) return 0xf2d64b // желтый
  if (ratio >= 0.25) return 0xf29338 // оранжевый
  if (ratio >= 0.05) return 0xe44848 // красный
  return 0x751b32 // темно-багровый
}

export function maxHealthForBuilding(building: PlacedBuilding): number {
  if (building.maxHealth && building.maxHealth > 0) return building.maxHealth
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  return spec?.upgradeLevels?.find((level) => level.level === building.level)?.health ?? spec?.health ?? 100
}
