import { Building2, HandCoins, UsersRound } from 'lucide-react'

import { buildingCatalog } from '../../../../shared/catalog/buildings'
import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { useGameStore } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { inventoryAmount, useInventory } from '../economy/useInventory'
import { ResourceIcon } from '../resources/ResourceIcon'

type ResourceBarItem = {
  id: string
  label: string
  fallback: number
  limitFallback?: number
  note: string
}

const resources = [
  { id: 'population', label: 'Жители', fallback: 18, limitFallback: 24, note: 'рабочая сила' },
  { id: 'coins', label: 'Монеты', fallback: 1240, limitFallback: 2000, note: 'лимит от хранилищ монет' },
  { id: 'aeolian-crystal', label: 'Эолийские кристаллы', fallback: 18, note: '' },
  { id: 'wood', label: 'Древесина', fallback: 420, note: '' },
  { id: 'stone', label: 'Камень', fallback: 260, note: '' },
  { id: 'brick', label: 'Кирпич', fallback: 74, note: '' },
  { id: 'oil', label: 'Нефть', fallback: 36, note: '' },
  { id: 'fuel', label: 'Бензин', fallback: 12, note: '' },
] satisfies ResourceBarItem[]

export function ResourceBar() {
  const toggleResourceRegistry = useGameStore((state) => state.toggleResourceRegistry)
  const setAlliancePanelOpen = useGameStore((state) => state.setAlliancePanelOpen)
  const buildings = useGameStore((state) => state.buildings)
  const inventoryQuery = useInventory()
  const items = inventoryQuery.data?.inventory.items
  const coinCapacity = inventoryQuery.data?.inventory.coin_capacity
  const populationCapacity = populationLimit(buildings)
  const buildingCapacity = buildingLimit(buildings)
  const usedBuildingCapacity = usedBuildingLimit(buildings)

  return (
    <header className="resource-bar" aria-label="Ресурсы">
      {resources.map(({ id, label, fallback, limitFallback, note }) => {
        const amount = inventoryAmount(items, id) || fallback
        const limit = id === 'population' ? populationCapacity || limitFallback : id === 'coins' ? coinCapacity || limitFallback : undefined
        const value = limit ? `${amount}/${limit}` : amount
        const warning = id === 'coins' && coinCapacity && amount >= coinCapacity * 0.9
        const title = note ? `${label}: ${value}, ${note}` : `${label}: ${value}`
        return (
        <div className="resource-chip" key={id} title={title} aria-label={`${label}: ${value}`}>
          <ResourceIcon id={id} label={label} />
          {warning ? <span className="resource-warning" aria-label="Лимит монет почти заполнен" /> : null}
          <strong>{value}</strong>
        </div>
        )
      })}
      <div className="resource-chip" title={`Постройки: ${usedBuildingCapacity}/${buildingCapacity}`} aria-label={`Постройки: ${usedBuildingCapacity}/${buildingCapacity}`}>
        <Building2 size={18} aria-hidden="true" />
        <strong>{usedBuildingCapacity}/{buildingCapacity}</strong>
      </div>
      <IconButton label="Реестр ресурсов" icon={HandCoins} onClick={toggleResourceRegistry} />
      <IconButton label="Союз" icon={UsersRound} onClick={() => setAlliancePanelOpen(true)} />
    </header>
  )
}

const catalogByKind = new Map(buildingCatalog.map((item) => [item.type, item]))

function populationLimit(buildings: PlacedBuilding[]) {
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

function populationForLevel(kind: BuildingKind, level: number) {
  const spec = catalogByKind.get(kind)
  const levelSpec = spec?.upgradeLevels?.find((item) => item.level === level)
  return levelSpec?.population ?? spec?.population ?? 0
}

function buildingLimit(buildings: PlacedBuilding[]) {
  const townHallLevel = buildings.reduce((level, building) => (building.kind === 'town_hall' ? Math.max(level, building.level) : level), 0)
  return 8 + Math.max(0, townHallLevel - 1) * 5
}

function usedBuildingLimit(buildings: PlacedBuilding[]) {
  return buildings.filter((building) => building.kind !== 'road').length
}
