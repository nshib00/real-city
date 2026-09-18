import { buildingCatalog } from '../../../../shared/catalog/buildings'
import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'

type InventoryItem = {
  resource: string
  amount: number
}

export function resourceAmount(items: InventoryItem[] | undefined, resource: string, fallback: number) {
  return items?.find((item) => item.resource === resource)?.amount ?? fallback
}

export function resourceValue(input: {
  id: string
  fallback: number
  limitFallback?: number
  items: InventoryItem[] | undefined
  coinCapacity: number | undefined
  buildings: PlacedBuilding[]
}) {
  const amount = resourceAmount(input.items, input.id, input.fallback)
  const limit = resourceLimit({
    id: input.id,
    limitFallback: input.limitFallback,
    coinCapacity: input.coinCapacity,
    buildings: input.buildings,
  })
  return limit ? `${amount}/${limit}` : String(amount)
}

export function resourceLimit(input: {
  id: string
  limitFallback?: number
  coinCapacity: number | undefined
  buildings: PlacedBuilding[]
}) {
  if (input.id === 'population') {
    return populationLimit(input.buildings) || input.limitFallback
  }
  if (input.id === 'coins') {
    return input.coinCapacity ?? input.limitFallback
  }
  return undefined
}

export function buildingCapacityValue(buildings: PlacedBuilding[]) {
  return `${usedBuildingLimit(buildings)}/${buildingLimit(buildings)}`
}

const catalogByKind = new Map(buildingCatalog.map((item) => [item.type, item]))

export function populationLimit(buildings: PlacedBuilding[]) {
  return buildings.reduce((total, building) => {
    if (building.status !== 'active') {
      return total
    }
    const spec = catalogByKind.get(building.kind)
    if (spec?.category !== 'housing') {
      return total
    }
    return total + populationForLevel(building.kind, building.level)
  }, 0)
}

export function populationForLevel(kind: BuildingKind, level: number) {
  const spec = catalogByKind.get(kind)
  const levelSpec = spec?.upgradeLevels?.find((item) => item.level === level)
  return levelSpec?.population ?? spec?.population ?? 0
}

export function buildingLimit(buildings: PlacedBuilding[]) {
  const townHallLevel = buildings.reduce((level, building) => (building.kind === 'town_hall' ? Math.max(level, building.level) : level), 0)
  return 8 + Math.max(0, townHallLevel - 1) * 3
}

export function usedBuildingLimit(buildings: PlacedBuilding[]) {
  return buildings.filter((building) => building.kind !== 'road').length
}
