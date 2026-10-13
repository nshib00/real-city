import { useState } from 'react'

import { resourceCatalog } from '../../../../shared/catalog/resources'
import { useGameStore } from '../../game/state/useGameStore'
import { Drawer, SegmentedControl } from '../../shared/ui'
import { useInventory } from '../economy/useInventory'
import { ResourceIcon } from './ResourceIcon'
import { resourceValue } from './resourceAmounts'

type ResourceCategory = 'basic' | 'raw' | 'crafted' | 'rare' | 'fuel'

const categories = [
  { id: 'basic', label: 'База' },
  { id: 'raw', label: 'Сырье' },
  { id: 'crafted', label: 'Производство' },
  { id: 'rare', label: 'Редкие' },
  { id: 'fuel', label: 'Топливо' },
] as const

const fallbackAmounts: Record<string, number> = {
  coins: 50,
}

const limitFallbacks: Record<string, number> = {
  coins: 2000,
}

const resources = resourceCatalog.map((resource) => ({
  ...resource,
  fallback: fallbackAmounts[resource.id] ?? 0,
  limitFallback: limitFallbacks[resource.id],
  limit: resource.hasLimit ? 'лимит от хранилищ' : 'без лимита',
})) satisfies { id: string; category: ResourceCategory; name: string; fallback: number; limitFallback?: number; limit: string; source: string }[]

export function ResourceRegistry() {
  const [category, setCategory] = useState<ResourceCategory>('basic')
  const open = useGameStore((state) => state.uiPreferences.resourceRegistryOpen)
  const toggleResourceRegistry = useGameStore((state) => state.toggleResourceRegistry)
  const buildings = useGameStore((state) => state.buildings)
  const inventoryQuery = useInventory()
  const items = inventoryQuery.data?.inventory.items
  const coinCapacity = inventoryQuery.data?.inventory.coin_capacity
  const visibleResources = resources.filter((resource) => resource.category === category)

  return (
    <Drawer title="Реестр ресурсов" open={open} onClose={toggleResourceRegistry}>
      <SegmentedControl items={categories} value={category} label="Категории ресурсов" onChange={setCategory} />
      <div className="resource-registry-list">
        {visibleResources.map((resource) => (
          <article className="resource-registry-row" key={resource.name}>
            <ResourceIcon id={resource.id} label={resource.name} />
            <strong>{resource.name}</strong>
            <span>{resourceValue({ id: resource.id, fallback: resource.fallback, limitFallback: resource.limitFallback, items, coinCapacity, buildings })}</span>
            <small>{resource.limit}</small>
            <em>{resource.source}</em>
          </article>
        ))}
      </div>
    </Drawer>
  )
}
