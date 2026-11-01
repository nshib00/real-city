import { useState } from 'react'

import { resourceCatalog } from '../../../../shared/catalog/resources'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { Drawer, SegmentedControl } from '../../shared/ui'
import { useInventory } from '../economy/useInventory'
import { ResourceIcon } from './ResourceIcon'
import { resourceValue } from './resourceAmounts'
import { RarityMark } from '../../shared/ui/ObjectMarks'

type ResourceCategory = 'basic' | 'raw' | 'crafted' | 'rare' | 'fuel' | 'weapons'

const categories = [
  { id: 'basic', label: 'База' },
  { id: 'raw', label: 'Сырье' },
  { id: 'crafted', label: 'Производство' },
  { id: 'rare', label: 'Редкие' },
  { id: 'fuel', label: 'Топливо' },
  { id: 'weapons', label: 'Оружие и бомбы' },
] as const

const fallbackAmounts: Record<string, number> = {
  coins: 50,
  throwing_knives: 50,
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
  const player = useAuthStore((state) => state.player)
  const ownerBuildings = buildings.filter((building) => building.owner === player?.id)
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
            {resource.category === 'rare' ? <RarityMark /> : null}
            <span>{resourceValue({ id: resource.id, fallback: resource.fallback, limitFallback: resource.limitFallback, items, coinCapacity, buildings: ownerBuildings })}</span>
            <small>{resource.limit}</small>
            <em>{resource.source}</em>
          </article>
        ))}
      </div>
    </Drawer>
  )
}
