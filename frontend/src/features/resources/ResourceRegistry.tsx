import { useState } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { Drawer, SegmentedControl } from '../../shared/ui'
import { ResourceIcon } from './ResourceIcon'

type ResourceCategory = 'basic' | 'raw' | 'crafted' | 'rare' | 'fuel'

const categories = [
  { id: 'basic', label: 'База' },
  { id: 'raw', label: 'Сырье' },
  { id: 'crafted', label: 'Производство' },
  { id: 'rare', label: 'Редкие' },
  { id: 'fuel', label: 'Топливо' },
] as const

const resources = [
  { id: 'coins', category: 'basic', name: 'Монеты', amount: '1 240/2 000', limit: 'лимит от хранилищ монет', source: 'поля, грядки, задания' },
  { id: 'population', category: 'basic', name: 'Жители', amount: '18/24', limit: 'лимит от жилья', source: 'жилые дома' },
  { id: 'aeolian-crystal', category: 'basic', name: 'Эолийские кристаллы', amount: '18', limit: 'без лимита', source: 'события, премиум' },
  { id: 'wood', category: 'raw', name: 'Древесина', amount: '420', limit: 'без лимита', source: 'лесопилка, руины' },
  { id: 'stone', category: 'raw', name: 'Камень', amount: '260', limit: 'без лимита', source: 'каменоломня, горные тайлы' },
  { id: 'clay', category: 'raw', name: 'Глина', amount: '120', limit: 'без лимита', source: 'глинистые участки' },
  { id: 'sand', category: 'raw', name: 'Песок', amount: '90', limit: 'без лимита', source: 'песчаная почва' },
  { id: 'coal', category: 'raw', name: 'Уголь', amount: '44', limit: 'без лимита', source: 'залежи угля' },
  { id: 'iron_ore', category: 'raw', name: 'Железная руда', amount: '38', limit: 'без лимита', source: 'рудные жилы' },
  { id: 'copper', category: 'raw', name: 'Медь', amount: '22', limit: 'без лимита', source: 'рудные жилы' },
  { id: 'resin', category: 'raw', name: 'Смола', amount: '16', limit: 'без лимита', source: 'лесные участки' },
  { id: 'windleaf', category: 'raw', name: 'Ветролист', amount: '27', limit: 'без лимита', source: 'грядки ветролиста' },
  { id: 'herbs', category: 'raw', name: 'Травы', amount: '31', limit: 'без лимита', source: 'грядки и поля' },
  { id: 'mushrooms', category: 'raw', name: 'Грибы', amount: '9', limit: 'без лимита', source: 'грибные грядки' },
  { id: 'seeds', category: 'raw', name: 'Семена', amount: '64', limit: 'без лимита', source: 'урожай' },
  { id: 'brick', category: 'crafted', name: 'Кирпич', amount: '74', limit: 'без лимита', source: 'кирпичный двор' },
  { id: 'stone_block', category: 'crafted', name: 'Каменный блок', amount: '11', limit: 'без лимита', source: 'каменотесы' },
  { id: 'metal', category: 'crafted', name: 'Металл', amount: '58', limit: 'без лимита', source: 'литейная' },
  { id: 'iron', category: 'crafted', name: 'Железо', amount: '34', limit: 'без лимита', source: 'литейная' },
  { id: 'steel', category: 'crafted', name: 'Сталь', amount: '12', limit: 'без лимита', source: 'сталеплавильный завод' },
  { id: 'glass', category: 'crafted', name: 'Стекло', amount: '32', limit: 'без лимита', source: 'стекольная мастерская' },
  { id: 'planks', category: 'crafted', name: 'Доски', amount: '88', limit: 'без лимита', source: 'лесопилка' },
  { id: 'cement', category: 'crafted', name: 'Цемент', amount: '26', limit: 'без лимита', source: 'цементный цех' },
  { id: 'concrete', category: 'crafted', name: 'Бетон', amount: '14', limit: 'без лимита', source: 'бетонный узел' },
  { id: 'fabric', category: 'crafted', name: 'Ткань', amount: '18', limit: 'без лимита', source: 'ткацкая мастерская' },
  { id: 'electronics', category: 'crafted', name: 'Электроника', amount: '3', limit: 'без лимита', source: 'электронная мастерская' },
  { id: 'sulfur', category: 'crafted', name: 'Сера', amount: '7', limit: 'без лимита', source: 'химическая мастерская' },
  { id: 'explosives', category: 'crafted', name: 'Взрывчатка', amount: '0', limit: 'без лимита', source: 'военный завод' },
  { id: 'super-seeds', category: 'rare', name: 'Супер-семена', amount: '3', limit: 'без лимита', source: 'супер-урожай' },
  { id: 'super-fiber', category: 'rare', name: 'Супер-волокно', amount: '0', limit: 'без лимита', source: 'супер-урожай' },
  { id: 'super-mushrooms', category: 'rare', name: 'Супер-грибы', amount: '1', limit: 'без лимита', source: 'супер-урожай' },
  { id: 'oil', category: 'fuel', name: 'Нефть', amount: '36', limit: 'без лимита', source: 'нефтяные скважины' },
  { id: 'fuel', category: 'fuel', name: 'Бензин', amount: '12', limit: 'без лимита', source: 'Нефтеперерабатывающий завод' },
] satisfies { id: string; category: ResourceCategory; name: string; amount: string; limit: string; source: string }[]

export function ResourceRegistry() {
  const [category, setCategory] = useState<ResourceCategory>('basic')
  const open = useGameStore((state) => state.uiPreferences.resourceRegistryOpen)
  const toggleResourceRegistry = useGameStore((state) => state.toggleResourceRegistry)
  const visibleResources = resources.filter((resource) => resource.category === category)

  return (
    <Drawer title="Реестр ресурсов" open={open} onClose={toggleResourceRegistry}>
      <SegmentedControl items={categories} value={category} label="Категории ресурсов" onChange={setCategory} />
      <div className="resource-registry-list">
        {visibleResources.map((resource) => (
          <article className="resource-registry-row" key={resource.name}>
            <ResourceIcon id={resource.id} label={resource.name} />
            <strong>{resource.name}</strong>
            <span>{resource.amount}</span>
            <small>{resource.limit}</small>
            <em>{resource.source}</em>
          </article>
        ))}
      </div>
    </Drawer>
  )
}
