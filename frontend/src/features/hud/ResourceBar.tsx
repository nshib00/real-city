import { Building2, HandCoins, UsersRound } from 'lucide-react'

import { resourceCatalog } from '../../../../shared/catalog/resources'
import type { ResourceCatalogItem } from '../../../../shared/catalog/resources'
import { useGameStore } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { availablePopulation, useInventory } from '../economy/useInventory'
import { resourceIconUrl } from '../resources/ResourceIcon'
import { buildingCapacityValue, resourceAmount, resourceLimit } from '../resources/resourceAmounts'

type ResourceBarItem = {
  id: string
  label: string
  fallback: number
  limitFallback?: number
  note: string
}

const pinnedResourceIds = new Set(['population', 'coins', 'aeolian-crystal'])

const pinnedResources = [
  { id: 'population', label: 'Жители', fallback: 0, note: 'рабочая сила' },
  { id: 'coins', label: 'Монеты', fallback: 50, limitFallback: 2000, note: 'лимит от хранилищ монет' },
  { id: 'aeolian-crystal', label: 'Эолийские кристаллы', fallback: 0, note: '' },
] satisfies ResourceBarItem[]

const orderedPanelResources = resourceCatalog
  .filter((resource): resource is ResourceCatalogItem & { displayOrder: number } => !pinnedResourceIds.has(resource.id) && typeof resource.displayOrder === 'number' && Number.isInteger(resource.displayOrder) && resource.displayOrder >= 0)
  .slice()
  .sort((left, right) => left.displayOrder - right.displayOrder)

export function ResourceBar() {
  const toggleResourceRegistry = useGameStore((state) => state.toggleResourceRegistry)
  const setAlliancePanelOpen = useGameStore((state) => state.setAlliancePanelOpen)
  const buildings = useGameStore((state) => state.buildings)
  const inventoryQuery = useInventory()
  const items = inventoryQuery.data?.inventory.items
  const coinCapacity = inventoryQuery.data?.inventory.coin_capacity
  const buildingValue = buildingCapacityValue(buildings)
  const visiblePanelResources = orderedPanelResources
    .map((resource) => ({
      id: resource.id,
      label: resource.name,
      fallback: 0,
      note: '',
      amount: resourceAmount(items, resource.id, 0),
    }))
    .filter((resource) => resource.amount > 0)

  return (
    <header className="resource-bar" aria-label="Ресурсы">
      <div className="resource-chip" title={`Постройки: ${buildingValue}`} aria-label={`Постройки: ${buildingValue}`}>
        <Building2 size={18} aria-hidden="true" />
        <strong>{buildingValue}</strong>
      </div>
      {pinnedResources.map(({ id, label, fallback, limitFallback, note }) => {
        const amount = id === 'population' ? availablePopulation(items, buildings) : resourceAmount(items, id, fallback)
        const limit = resourceLimit({ id, limitFallback, coinCapacity, buildings })
        const value = limit ? `${amount}/${limit}` : amount
        const warning = id === 'coins' && coinCapacity && amount >= coinCapacity * 0.9
        const title = note ? `${label}: ${value}, ${note}` : `${label}: ${value}`
        return (
          <div className="resource-chip" key={id} title={title} aria-label={`${label}: ${value}`}>
            <span className="resource-icon resource-icon-topbar" title={label} aria-hidden="true">
              <img src={resourceIconUrl(id)} alt="" className="resource-icon-render" />
            </span>
            {warning ? <span className="resource-warning" aria-label="Лимит монет почти заполнен" /> : null}
            <strong>{value}</strong>
          </div>
        )
      })}
      {visiblePanelResources.map(({ id, label, note, amount }) => {
        const title = note ? `${label}: ${amount}, ${note}` : `${label}: ${amount}`
        return (
          <div className="resource-chip" key={id} title={title} aria-label={`${label}: ${amount}`}>
            <span className="resource-icon resource-icon-topbar" title={label} aria-hidden="true">
              <img src={resourceIconUrl(id)} alt="" className="resource-icon-render" />
            </span>
            <strong>{amount}</strong>
          </div>
        )
      })}
      <IconButton label="Реестр ресурсов" icon={HandCoins} onClick={toggleResourceRegistry} />
      <IconButton label="Союз" icon={UsersRound} onClick={() => setAlliancePanelOpen(true)} />
    </header>
  )
}
