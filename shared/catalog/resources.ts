export type ResourceCategory = 'basic' | 'raw' | 'crafted' | 'rare' | 'fuel'

export type ResourceCatalogItem = {
  id: string
  name: string
  category: ResourceCategory
  hasLimit: boolean
  source: string
}

export const resourceCatalog: ResourceCatalogItem[] = [
  { id: 'coins', name: 'Монеты', category: 'basic', hasLimit: true, source: 'поля, грядки, задания, рынки' },
  { id: 'population', name: 'Жители', category: 'basic', hasLimit: false, source: 'жилые дома' },
  { id: 'aeolian-crystal', name: 'Эолийские кристаллы', category: 'basic', hasLimit: false, source: 'события, премиум' },
  { id: 'wood', name: 'Древесина', category: 'raw', hasLimit: false, source: 'лесопильный двор, лесные узлы' },
  { id: 'stone', name: 'Камень', category: 'raw', hasLimit: false, source: 'каменотесы, горные тайлы' },
  { id: 'clay', name: 'Глина', category: 'raw', hasLimit: false, source: 'глинистые участки' },
  { id: 'sand', name: 'Песок', category: 'raw', hasLimit: false, source: 'песчаная почва' },
  { id: 'coal', name: 'Уголь', category: 'raw', hasLimit: false, source: 'угольные залежи' },
  { id: 'iron_ore', name: 'Железная руда', category: 'raw', hasLimit: false, source: 'рудные жилы' },
  { id: 'copper', name: 'Медь', category: 'raw', hasLimit: false, source: 'рудные жилы' },
  { id: 'resin', name: 'Смола', category: 'raw', hasLimit: false, source: 'лесные участки' },
  { id: 'windleaf', name: 'Ветролист', category: 'raw', hasLimit: false, source: 'грядки ветролиста' },
  { id: 'herbs', name: 'Травы', category: 'raw', hasLimit: false, source: 'поля и грядки' },
  { id: 'mushrooms', name: 'Грибы', category: 'raw', hasLimit: false, source: 'грибные грядки' },
  { id: 'seeds', name: 'Семена', category: 'raw', hasLimit: false, source: 'урожай' },
  { id: 'brick', name: 'Кирпич', category: 'crafted', hasLimit: false, source: 'кирпичный двор' },
  { id: 'stone_block', name: 'Каменный блок', category: 'crafted', hasLimit: false, source: 'каменотесы' },
  { id: 'metal', name: 'Металл', category: 'crafted', hasLimit: false, source: 'литейная' },
  { id: 'iron', name: 'Железо', category: 'crafted', hasLimit: false, source: 'литейная' },
  { id: 'steel', name: 'Сталь', category: 'crafted', hasLimit: false, source: 'сталеплавильный завод' },
  { id: 'glass', name: 'Стекло', category: 'crafted', hasLimit: false, source: 'стекольная мастерская' },
  { id: 'planks', name: 'Доски', category: 'crafted', hasLimit: false, source: 'лесопилка' },
  { id: 'cement', name: 'Цемент', category: 'crafted', hasLimit: false, source: 'цементный цех' },
  { id: 'concrete', name: 'Бетон', category: 'crafted', hasLimit: false, source: 'бетонный узел' },
  { id: 'fabric', name: 'Ткань', category: 'crafted', hasLimit: false, source: 'ткацкая мастерская' },
  { id: 'electronics', name: 'Электроника', category: 'crafted', hasLimit: false, source: 'электронная мастерская' },
  { id: 'sulfur', name: 'Сера', category: 'crafted', hasLimit: false, source: 'химическая мастерская' },
  { id: 'explosives', name: 'Взрывчатка', category: 'crafted', hasLimit: false, source: 'военный завод' },
  { id: 'oil', name: 'Нефть', category: 'fuel', hasLimit: false, source: 'нефтяные скважины' },
  { id: 'fuel', name: 'Бензин', category: 'fuel', hasLimit: false, source: 'Нефтеперерабатывающий завод' },
  { id: 'super-seeds', name: 'Супер-семена', category: 'rare', hasLimit: false, source: 'супер-урожай' },
  { id: 'super-fiber', name: 'Супер-волокно', category: 'rare', hasLimit: false, source: 'супер-урожай' },
  { id: 'super-mushrooms', name: 'Супер-грибы', category: 'rare', hasLimit: false, source: 'супер-урожай' },
]

