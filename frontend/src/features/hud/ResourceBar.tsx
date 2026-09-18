import { Building2, HandCoins, UsersRound } from 'lucide-react'

import { useGameStore } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { useInventory } from '../economy/useInventory'
import { resourceIconUrl } from '../resources/ResourceIcon'
import { buildingCapacityValue, resourceAmount, resourceLimit } from '../resources/resourceAmounts'

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
  const buildingValue = buildingCapacityValue(buildings)

  return (
    <header className="resource-bar" aria-label="Ресурсы">
      <div className="resource-chip" title={`Постройки: ${buildingValue}`} aria-label={`Постройки: ${buildingValue}`}>
        <Building2 size={18} aria-hidden="true" />
        <strong>{buildingValue}</strong>
      </div>
      {resources.map(({ id, label, fallback, limitFallback, note }) => {
        const amount = resourceAmount(items, id, fallback)
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
      <IconButton label="Реестр ресурсов" icon={HandCoins} onClick={toggleResourceRegistry} />
      <IconButton label="Союз" icon={UsersRound} onClick={() => setAlliancePanelOpen(true)} />
    </header>
  )
}
