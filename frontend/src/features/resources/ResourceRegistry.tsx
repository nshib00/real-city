import { useState } from 'react'

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

const resources = [
  { id: 'coins', category: 'basic', name: 'Монеты', fallback: 1240, limitFallback: 2000, limit: 'лимит от хранилищ монет', source: 'поля, грядки, задания' },
  { id: 'population', category: 'basic', name: 'Жители', fallback: 18, limitFallback: 24, limit: 'лимит от жилья', source: 'жилые дома' },
  { id: 'aeolian-crystal', category: 'basic', name: 'Эолийские кристаллы', fallback: 18, limit: 'без лимита', source: 'события, премиум' },
  { id: 'wood', category: 'raw', name: 'Древесина', fallback: 420, limit: 'без лимита', source: 'лесопилка, руины' },
  { id: 'stone', category: 'raw', name: 'Камень', fallback: 260, limit: 'без лимита', source: 'каменоломня, горные тайлы' },
  { id: 'clay', category: 'raw', name: 'Глина', fallback: 120, limit: 'без лимита', source: 'глинистые участки' },
  { id: 'sand', category: 'raw', name: 'Песок', fallback: 90, limit: 'без лимита', source: 'песчаная почва' },
  { id: 'coal', category: 'raw', name: 'Уголь', fallback: 44, limit: 'без лимита', source: 'залежи угля' },
  { id: 'iron_ore', category: 'raw', name: 'Железная руда', fallback: 38, limit: 'без лимита', source: 'рудные жилы' },
  { id: 'copper', category: 'raw', name: 'Медь', fallback: 22, limit: 'без лимита', source: 'рудные жилы' },
  { id: 'resin', category: 'raw', name: 'Смола', fallback: 16, limit: 'без лимита', source: 'лесные участки' },
  { id: 'flax', category: 'raw', name: 'Лен', fallback: 3, limit: 'без лимита', source: 'льняные грядки' },
  { id: 'windleaf', category: 'raw', name: 'Ветролист', fallback: 27, limit: 'без лимита', source: 'грядки ветролиста' },
  { id: 'herbs', category: 'raw', name: 'Травы', fallback: 31, limit: 'без лимита', source: 'грядки и поля' },
  { id: 'mushrooms', category: 'raw', name: 'Грибы', fallback: 9, limit: 'без лимита', source: 'грибные грядки' },
  { id: 'seeds', category: 'raw', name: 'Семена', fallback: 64, limit: 'без лимита', source: 'урожай' },
  { id: 'brick', category: 'crafted', name: 'Кирпич', fallback: 74, limit: 'без лимита', source: 'кирпичный двор' },
  { id: 'stone_block', category: 'crafted', name: 'Каменный блок', fallback: 11, limit: 'без лимита', source: 'каменотесы' },
  { id: 'metal', category: 'crafted', name: 'Металл', fallback: 58, limit: 'без лимита', source: 'литейная' },
  { id: 'iron', category: 'crafted', name: 'Железо', fallback: 34, limit: 'без лимита', source: 'литейная' },
  { id: 'steel', category: 'crafted', name: 'Сталь', fallback: 12, limit: 'без лимита', source: 'сталеплавильный завод' },
  { id: 'glass', category: 'crafted', name: 'Стекло', fallback: 32, limit: 'без лимита', source: 'стекольная мастерская' },
  { id: 'planks', category: 'crafted', name: 'Доски', fallback: 88, limit: 'без лимита', source: 'лесопилка' },
  { id: 'premium_planks', category: 'crafted', name: 'Премиум-доски', fallback: 0, limit: 'без лимита', source: 'поздняя лесопилка' },
  { id: 'rope', category: 'crafted', name: 'Веревка', fallback: 0, limit: 'без лимита', source: 'канатная мастерская' },
  { id: 'iron_ingot', category: 'crafted', name: 'Железный слиток', fallback: 0, limit: 'без лимита', source: 'литейная' },
  { id: 'gold_ingot', category: 'crafted', name: 'Золотой слиток', fallback: 0, limit: 'без лимита', source: 'поздняя литейная' },
  { id: 'cement', category: 'crafted', name: 'Цемент', fallback: 26, limit: 'без лимита', source: 'цементный цех' },
  { id: 'concrete', category: 'crafted', name: 'Бетон', fallback: 14, limit: 'без лимита', source: 'бетонный узел' },
  { id: 'fabric', category: 'crafted', name: 'Ткань', fallback: 18, limit: 'без лимита', source: 'ткацкая мастерская' },
  { id: 'electronics', category: 'crafted', name: 'Электроника', fallback: 3, limit: 'без лимита', source: 'электронная мастерская' },
  { id: 'sulfur', category: 'crafted', name: 'Сера', fallback: 7, limit: 'без лимита', source: 'химическая мастерская' },
  { id: 'explosives', category: 'crafted', name: 'Взрывчатка', fallback: 0, limit: 'без лимита', source: 'военный завод' },
  { id: 'super-seeds', category: 'rare', name: 'Супер-семена', fallback: 3, limit: 'без лимита', source: 'супер-урожай' },
  { id: 'super-fiber', category: 'rare', name: 'Супер-волокно', fallback: 0, limit: 'без лимита', source: 'супер-урожай' },
  { id: 'super-mushrooms', category: 'rare', name: 'Супер-грибы', fallback: 1, limit: 'без лимита', source: 'супер-урожай' },
  { id: 'super-windleaf', category: 'rare', name: 'Супер-ветролист', fallback: 0, limit: 'без лимита', source: 'супер-урожай грядки ветролиста' },
  { id: 'emerald_dust', category: 'rare', name: 'Изумрудная пыль', fallback: 0, limit: 'без лимита', source: 'огранка редких кристаллов' },
  { id: 'elderwood-heart', category: 'rare', name: 'Сердцевина древня', fallback: 0, limit: 'без лимита', source: 'редкая находка при рубке леса' },
  { id: 'oil', category: 'fuel', name: 'Нефть', fallback: 36, limit: 'без лимита', source: 'нефтяные скважины' },
  { id: 'fuel', category: 'fuel', name: 'Бензин', fallback: 12, limit: 'без лимита', source: 'Нефтеперерабатывающий завод' },
] satisfies { id: string; category: ResourceCategory; name: string; fallback: number; limitFallback?: number; limit: string; source: string }[]

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
