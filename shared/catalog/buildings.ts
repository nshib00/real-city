export type BuildingTypeId =
  | 'town_hall'
  | 'dugout'
  | 'wood_house'
  | 'stone_house'
  | 'apartment_house'
  | 'villa'
  | 'palace'
  | 'residential_skyscraper'
  | 'workshop'
  | 'warehouse'
  | 'coin_storage'
  | 'market'
  | 'tower'
  | 'wooden_wall'
  | 'stone_wall'
  | 'concrete_wall'
  | 'modern_wall'
  | 'road'
  | 'alliance_house'
  | 'field_bed'
  | 'lumber_yard'
  | 'stone_cutters'
  | 'oil_refinery'

export type BuildingCatalogItem = {
  type: BuildingTypeId
  category: 'housing' | 'fields' | 'industry' | 'defense' | 'roads' | 'storage' | 'social' | 'trade' | 'center'
  name: string
  level: number
  footprint: { width: number; height: number }
  buildSeconds: number
  population: number
  health?: number
  cost: { resource: string; amount: number }[]
  firstLevel: boolean
  upgradeTo: BuildingTypeId[]
  upgradeLevels?: {
    level: number
    buildSeconds: number
    population: number
    health: number
    cost: { resource: string; amount: number }[]
    nextType?: BuildingTypeId
  }[]
}

export const buildingCatalog: BuildingCatalogItem[] = [
  { type: 'town_hall', category: 'center', name: 'Ратуша', level: 1, footprint: { width: 2, height: 2 }, buildSeconds: 0, population: 0, cost: [], firstLevel: true, upgradeTo: [] },
  {
    type: 'dugout',
    category: 'housing',
    name: 'Землянка',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 10,
    population: 1,
    health: 35,
    cost: [{ resource: 'coins', amount: 50 }, { resource: 'wood', amount: 3 }],
    firstLevel: true,
    upgradeTo: ['wood_house'],
    upgradeLevels: [
      { level: 1, buildSeconds: 10, population: 1, health: 35, cost: [{ resource: 'coins', amount: 50 }, { resource: 'wood', amount: 3 }] },
      { level: 2, buildSeconds: 45, population: 2, health: 140, cost: [{ resource: 'coins', amount: 400 }, { resource: 'wood', amount: 10 }] },
      { level: 3, buildSeconds: 170, population: 3, health: 270, cost: [{ resource: 'coins', amount: 950 }, { resource: 'wood', amount: 23 }, { resource: 'windleaf', amount: 2 }] },
      { level: 4, buildSeconds: 515, population: 4, health: 435, cost: [{ resource: 'coins', amount: 2800 }, { resource: 'wood', amount: 40 }, { resource: 'windleaf', amount: 5 }, { resource: 'planks', amount: 2 }] },
      { level: 5, buildSeconds: 1090, population: 6, health: 760, cost: [{ resource: 'coins', amount: 6500 }, { resource: 'wood', amount: 82 }, { resource: 'windleaf', amount: 11 }, { resource: 'planks', amount: 4 }], nextType: 'wood_house' },
    ],
  },
  {
    type: 'wood_house',
    category: 'housing',
    name: 'Деревянный дом',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 2070,
    population: 8,
    health: 1200,
    cost: [{ resource: 'coins', amount: 10000 }, { resource: 'planks', amount: 20 }, { resource: 'stone', amount: 4 }, { resource: 'glass', amount: 1 }],
    firstLevel: false,
    upgradeTo: ['stone_house'],
    upgradeLevels: [
      { level: 1, buildSeconds: 2070, population: 8, health: 1200, cost: [{ resource: 'coins', amount: 10000 }, { resource: 'planks', amount: 20 }, { resource: 'stone', amount: 4 }, { resource: 'glass', amount: 1 }] },
      { level: 2, buildSeconds: 3920, population: 10, health: 1750, cost: [{ resource: 'coins', amount: 16400 }, { resource: 'planks', amount: 36 }, { resource: 'stone', amount: 7 }, { resource: 'glass', amount: 2 }] },
      { level: 3, buildSeconds: 6090, population: 12, health: 2100, cost: [{ resource: 'coins', amount: 24200 }, { resource: 'planks', amount: 56 }, { resource: 'stone', amount: 10 }, { resource: 'glass', amount: 4 }] },
      { level: 4, buildSeconds: 8400, population: 14, health: 2550, cost: [{ resource: 'coins', amount: 33300 }, { resource: 'planks', amount: 70 }, { resource: 'stone', amount: 14 }, { resource: 'glass', amount: 7 }] },
      { level: 5, buildSeconds: 11700, population: 17, health: 2930, cost: [{ resource: 'coins', amount: 43000 }, { resource: 'planks', amount: 95 }, { resource: 'stone', amount: 20 }, { resource: 'glass', amount: 10 }] },
      { level: 6, buildSeconds: 14400, population: 20, health: 3310, cost: [{ resource: 'coins', amount: 52500 }, { resource: 'planks', amount: 120 }, { resource: 'stone', amount: 25 }, { resource: 'glass', amount: 13 }, { resource: 'stone_block', amount: 4 }], nextType: 'stone_house' },
    ],
  },
  { type: 'stone_house', category: 'housing', name: 'Каменный дом', level: 3, footprint: { width: 1, height: 1 }, buildSeconds: 480, population: 4, cost: [{ resource: 'stone', amount: 120 }, { resource: 'brick', amount: 60 }], firstLevel: false, upgradeTo: ['apartment_house', 'villa'] },
  { type: 'apartment_house', category: 'housing', name: 'Многоквартирный дом', level: 4, footprint: { width: 2, height: 2 }, buildSeconds: 900, population: 8, cost: [{ resource: 'brick', amount: 240 }], firstLevel: false, upgradeTo: ['residential_skyscraper'] },
  { type: 'villa', category: 'housing', name: 'Вилла', level: 4, footprint: { width: 2, height: 2 }, buildSeconds: 1080, population: 6, cost: [{ resource: 'stone', amount: 260 }, { resource: 'glass', amount: 80 }], firstLevel: false, upgradeTo: ['palace'] },
  { type: 'residential_skyscraper', category: 'housing', name: 'Жилой небоскреб', level: 5, footprint: { width: 2, height: 2 }, buildSeconds: 1800, population: 14, cost: [{ resource: 'metal', amount: 220 }, { resource: 'glass', amount: 160 }], firstLevel: false, upgradeTo: [] },
  { type: 'palace', category: 'housing', name: 'Дворец', level: 5, footprint: { width: 3, height: 3 }, buildSeconds: 2400, population: 10, cost: [{ resource: 'brick', amount: 520 }, { resource: 'glass', amount: 240 }], firstLevel: false, upgradeTo: [] },
  { type: 'workshop', category: 'industry', name: 'Мастерская', level: 1, footprint: { width: 2, height: 1 }, buildSeconds: 180, population: 3, cost: [{ resource: 'wood', amount: 90 }, { resource: 'stone', amount: 40 }], firstLevel: true, upgradeTo: [] },
  { type: 'warehouse', category: 'storage', name: 'Склад материалов', level: 1, footprint: { width: 2, height: 1 }, buildSeconds: 120, population: 2, cost: [{ resource: 'wood', amount: 80 }, { resource: 'stone', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'coin_storage', category: 'storage', name: 'Хранилище монет', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 1, cost: [{ resource: 'wood', amount: 70 }, { resource: 'stone', amount: 40 }], firstLevel: true, upgradeTo: [] },
  { type: 'market', category: 'trade', name: 'Рынок', level: 1, footprint: { width: 2, height: 2 }, buildSeconds: 300, population: 4, cost: [{ resource: 'coins', amount: 400 }, { resource: 'wood', amount: 80 }], firstLevel: true, upgradeTo: [] },
  { type: 'tower', category: 'defense', name: 'Сторожевая башня', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 240, population: 2, cost: [{ resource: 'wood', amount: 120 }, { resource: 'stone', amount: 80 }], firstLevel: true, upgradeTo: [] },
  { type: 'wooden_wall', category: 'defense', name: 'Деревянная стена', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 60, population: 1, cost: [{ resource: 'wood', amount: 50 }], firstLevel: true, upgradeTo: ['stone_wall'] },
  { type: 'stone_wall', category: 'defense', name: 'Каменная стена', level: 4, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 1, cost: [{ resource: 'stone', amount: 120 }, { resource: 'brick', amount: 40 }], firstLevel: false, upgradeTo: ['concrete_wall'] },
  { type: 'concrete_wall', category: 'defense', name: 'Бетонная стена', level: 8, footprint: { width: 1, height: 1 }, buildSeconds: 180, population: 1, cost: [{ resource: 'concrete', amount: 120 }, { resource: 'steel', amount: 30 }], firstLevel: false, upgradeTo: ['modern_wall'] },
  { type: 'modern_wall', category: 'defense', name: 'Современная стена', level: 11, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 2, cost: [{ resource: 'steel', amount: 120 }, { resource: 'electronics', amount: 20 }], firstLevel: false, upgradeTo: [] },
  { type: 'road', category: 'roads', name: 'Грунтовая дорога', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 30, population: 0, cost: [{ resource: 'coins', amount: 10 }], firstLevel: true, upgradeTo: [] },
  { type: 'alliance_house', category: 'social', name: 'Союзный дом', level: 1, footprint: { width: 2, height: 2 }, buildSeconds: 300, population: 4, cost: [{ resource: 'coins', amount: 500 }, { resource: 'brick', amount: 120 }], firstLevel: true, upgradeTo: [] },
  { type: 'field_bed', category: 'fields', name: 'Грядка ветролиста', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 45, population: 1, cost: [{ resource: 'coins', amount: 60 }], firstLevel: true, upgradeTo: [] },
  { type: 'lumber_yard', category: 'industry', name: 'Лесопильный двор', level: 1, footprint: { width: 2, height: 1 }, buildSeconds: 140, population: 3, cost: [{ resource: 'coins', amount: 120 }], firstLevel: true, upgradeTo: [] },
  { type: 'stone_cutters', category: 'industry', name: 'Каменотесы', level: 1, footprint: { width: 2, height: 1 }, buildSeconds: 160, population: 3, cost: [{ resource: 'coins', amount: 140 }, { resource: 'wood', amount: 60 }], firstLevel: true, upgradeTo: [] },
  { type: 'oil_refinery', category: 'industry', name: 'Нефтеперерабатывающий завод', level: 1, footprint: { width: 2, height: 2 }, buildSeconds: 270, population: 4, cost: [{ resource: 'brick', amount: 80 }, { resource: 'metal', amount: 30 }], firstLevel: true, upgradeTo: [] },
]
