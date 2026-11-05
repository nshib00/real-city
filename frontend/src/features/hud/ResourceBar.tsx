import { Building2, HandCoins, UsersRound } from '../../shared/ui/icons'

import { resourceCatalog } from '../../../../shared/catalog/resources'
import type { ResourceCatalogItem } from '../../../../shared/catalog/resources'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { IconButton } from '../../shared/ui'
import { availablePopulation, useInventory } from '../economy/useInventory'
import { ResourceIcon } from '../resources/ResourceIcon'
import { buildingCapacityValue, resourceAmount, resourceLimit } from '../resources/resourceAmounts'
import { formatAmount, formatFullAmount } from './formatAmount'

type ResourceBarItem = {
  id: string
  label: string
  fallback: number
  limitFallback?: number
}

const pinnedResourceIds = new Set(['population', 'coins', 'aeolian-crystal'])

const pinnedResources = [
  { id: 'population', label: 'Жители', fallback: 0 },
  { id: 'coins', label: 'Монеты', fallback: 50, limitFallback: 2000 },
  { id: 'aeolian-crystal', label: 'Эолийские кристаллы', fallback: 0 },
] satisfies ResourceBarItem[]

const orderedPanelResources = resourceCatalog
  .filter((resource): resource is ResourceCatalogItem & { displayOrder: number } => !pinnedResourceIds.has(resource.id) && resource.category !== 'weapons' && typeof resource.displayOrder === 'number' && Number.isInteger(resource.displayOrder) && resource.displayOrder >= 0)
  .slice()
  .sort((left, right) => left.displayOrder - right.displayOrder)

const weaponResources = resourceCatalog.filter((resource) => resource.category === 'weapons')

export function ResourceBar() {
  const toggleResourceRegistry = useGameStore((state) => state.toggleResourceRegistry)
  const setAlliancePanelOpen = useGameStore((state) => state.setAlliancePanelOpen)
  const buildings = useGameStore((state) => state.buildings)
  const player = useAuthStore((state) => state.player)
  const ownerBuildings = buildings.filter((building) => building.owner === player?.id)
  const inventoryQuery = useInventory()
  const items = inventoryQuery.data?.inventory.items
  const coinCapacity = inventoryQuery.data?.inventory.coin_capacity
  const buildingValue = buildingCapacityValue(ownerBuildings)
  const visiblePanelResources = orderedPanelResources
    .map((resource) => ({
      id: resource.id,
      label: resource.name,
      fallback: 0,
      amount: resourceAmount(items, resource.id, 0),
    }))
    .filter((resource) => resource.amount > 0)
  const visibleWeapons = weaponResources
    .map((resource) => ({ ...resource, amount: resourceAmount(items, resource.id, 0) }))
    .filter((resource) => resource.amount > 0)

  return (
    <header className="resource-bar" aria-label="Ресурсы">
      <div className="resource-chip" title={`Постройки: ${buildingValue}`} aria-label={`Постройки: ${buildingValue}`}>
        <Building2 size={18} aria-hidden="true" />
        <strong>{buildingValue}</strong>
      </div>
      {pinnedResources.map(({ id, label, fallback, limitFallback }) => {
        const amount = id === 'population' ? availablePopulation(items) : resourceAmount(items, id, fallback)
        const limit = resourceLimit({ id, limitFallback, coinCapacity, buildings: ownerBuildings })
        const warning = id === 'coins' && coinCapacity && amount >= coinCapacity * 0.9
        const title = `${label}: ${formatFullAmount(amount)}`
        return (
          <div className={`resource-chip resource-${id}`} key={id} title={title} aria-label={title}>
            <ResourceIcon id={id} label={label} className="resource-icon-topbar" iconVariant="asset" decorative />
            {warning ? <span className="resource-warning" aria-label="Лимит монет почти заполнен" /> : null}
            <strong aria-hidden="true">{limit ? `${formatAmount(amount)}/${formatAmount(limit)}` : formatAmount(amount)}</strong>
          </div>
        )
      })}
      <div className="resource-material-group" role="group" aria-label="Материалы">
      {visiblePanelResources.map(({ id, label, amount }) => (
          <div className="resource-chip" key={id} title={`${label}: ${formatFullAmount(amount)}`} aria-label={`${label}: ${formatFullAmount(amount)}`}>
            <ResourceIcon id={id} label={label} className="resource-icon-topbar" decorative />
            <strong aria-hidden="true">{formatAmount(amount)}</strong>
          </div>
      ))}
      </div>
      {visibleWeapons.length > 0 && <div className="resource-weapon-group" role="group" aria-label="Оружие и бомбы">
        {visibleWeapons.map(({ id, name, amount }) => (
          <div className="resource-chip" key={id} title={`${name}: ${formatFullAmount(amount)}`} aria-label={`${name}: ${formatFullAmount(amount)}`}>
            <ResourceIcon id={id} label={name} className="resource-icon-topbar" />
            <strong aria-hidden="true">{formatAmount(amount)}</strong>
          </div>
        ))}
      </div>}
      <IconButton label="Реестр ресурсов" icon={HandCoins} onClick={toggleResourceRegistry} />
      <IconButton label="Союз" icon={UsersRound} onClick={() => setAlliancePanelOpen(true)} />
    </header>
  )
}
