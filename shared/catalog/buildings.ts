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
  {
    type: 'town_hall',
    category: 'center',
    name: 'Ратуша',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 0,
    population: 0,
    health: 100,
    cost: [],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 0, population: 0, health: 100, cost: [] },
      { level: 2, buildSeconds: 90, population: 0, health: 220, cost: [{ resource: 'coins', amount: 1500 }, { resource: 'wood', amount: 40 }, { resource: 'windleaf', amount: 2 }] },
      { level: 3, buildSeconds: 260, population: 0, health: 480, cost: [{ resource: 'coins', amount: 5300 }, { resource: 'wood', amount: 92 }, { resource: 'windleaf', amount: 6 }, { resource: 'glass', amount: 1 }] },
      { level: 4, buildSeconds: 1025, population: 0, health: 910, cost: [{ resource: 'coins', amount: 12000 }, { resource: 'wood', amount: 213 }, { resource: 'mushrooms', amount: 3 }, { resource: 'planks', amount: 17 }, { resource: 'glass', amount: 4 }] },
      { level: 5, buildSeconds: 2170, population: 0, health: 1230, cost: [{ resource: 'coins', amount: 34000 }, { resource: 'wood', amount: 567 }, { resource: 'mushrooms', amount: 10 }, { resource: 'planks', amount: 48 }, { resource: 'glass', amount: 12 }] },
      { level: 6, buildSeconds: 3750, population: 0, health: 1520, cost: [{ resource: 'coins', amount: 78000 }, { resource: 'wood', amount: 1200 }, { resource: 'mushrooms', amount: 27 }, { resource: 'planks', amount: 81 }, { resource: 'stone', amount: 34 }] },
      { level: 7, buildSeconds: 8580, population: 0, health: 1890, cost: [{ resource: 'coins', amount: 145000 }, { resource: 'planks', amount: 195 }, { resource: 'stone', amount: 78 }, { resource: 'stone_block', amount: 25 }] },
      { level: 8, buildSeconds: 13500, population: 0, health: 2360, cost: [{ resource: 'coins', amount: 286000 }, { resource: 'planks', amount: 425 }, { resource: 'stone_block', amount: 52 }, { resource: 'brick', amount: 16 }] },
      { level: 9, buildSeconds: 18840, population: 0, health: 2910, cost: [{ resource: 'coins', amount: 527000 }, { resource: 'stone_block', amount: 121 }, { resource: 'brick', amount: 45 }, { resource: 'glass', amount: 47 }] },
      { level: 10, buildSeconds: 27360, population: 0, health: 3530, cost: [{ resource: 'coins', amount: 875000 }, { resource: 'brick', amount: 109 }, { resource: 'premium_planks', amount: 4 }, { resource: 'super-mushrooms', amount: 2 }, { resource: 'glass', amount: 78 }] },
    ],
  },
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
  { type: 'apartment_house', category: 'housing', name: 'Многоквартирный дом', level: 4, footprint: { width: 1, height: 1 }, buildSeconds: 900, population: 8, cost: [{ resource: 'brick', amount: 240 }], firstLevel: false, upgradeTo: ['residential_skyscraper'] },
  { type: 'villa', category: 'housing', name: 'Вилла', level: 4, footprint: { width: 1, height: 1 }, buildSeconds: 1080, population: 6, cost: [{ resource: 'stone', amount: 260 }, { resource: 'glass', amount: 80 }], firstLevel: false, upgradeTo: ['palace'] },
  { type: 'residential_skyscraper', category: 'housing', name: 'Жилой небоскреб', level: 5, footprint: { width: 1, height: 1 }, buildSeconds: 1800, population: 14, cost: [{ resource: 'metal', amount: 220 }, { resource: 'glass', amount: 160 }], firstLevel: false, upgradeTo: [] },
  { type: 'palace', category: 'housing', name: 'Дворец', level: 5, footprint: { width: 1, height: 1 }, buildSeconds: 2400, population: 10, cost: [{ resource: 'brick', amount: 520 }, { resource: 'glass', amount: 240 }], firstLevel: false, upgradeTo: [] },
  { type: 'workshop', category: 'industry', name: 'Мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 180, population: 3, cost: [{ resource: 'wood', amount: 90 }, { resource: 'stone', amount: 40 }], firstLevel: true, upgradeTo: [] },
  { type: 'warehouse', category: 'storage', name: 'Склад материалов', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 2, cost: [{ resource: 'wood', amount: 80 }, { resource: 'stone', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'coin_storage', category: 'storage', name: 'Хранилище монет', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 1, cost: [{ resource: 'wood', amount: 70 }, { resource: 'stone', amount: 40 }], firstLevel: true, upgradeTo: [] },
  { type: 'market', category: 'trade', name: 'Рынок', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 4, cost: [{ resource: 'coins', amount: 400 }, { resource: 'wood', amount: 80 }], firstLevel: true, upgradeTo: [] },
  { type: 'tower', category: 'defense', name: 'Сторожевая башня', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 240, population: 2, cost: [{ resource: 'wood', amount: 120 }, { resource: 'stone', amount: 80 }], firstLevel: true, upgradeTo: [] },
  { type: 'wooden_wall', category: 'defense', name: 'Деревянная стена', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 60, population: 1, cost: [{ resource: 'wood', amount: 50 }], firstLevel: true, upgradeTo: ['stone_wall'] },
  { type: 'stone_wall', category: 'defense', name: 'Каменная стена', level: 4, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 1, cost: [{ resource: 'stone', amount: 120 }, { resource: 'brick', amount: 40 }], firstLevel: false, upgradeTo: ['concrete_wall'] },
  { type: 'concrete_wall', category: 'defense', name: 'Бетонная стена', level: 8, footprint: { width: 1, height: 1 }, buildSeconds: 180, population: 1, cost: [{ resource: 'concrete', amount: 120 }, { resource: 'steel', amount: 30 }], firstLevel: false, upgradeTo: ['modern_wall'] },
  { type: 'modern_wall', category: 'defense', name: 'Современная стена', level: 11, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 2, cost: [{ resource: 'steel', amount: 120 }, { resource: 'electronics', amount: 20 }], firstLevel: false, upgradeTo: [] },
  { type: 'road', category: 'roads', name: 'Грунтовая дорога', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 30, population: 0, cost: [{ resource: 'coins', amount: 10 }], firstLevel: true, upgradeTo: [] },
  { type: 'alliance_house', category: 'social', name: 'Союзный дом', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 4, cost: [{ resource: 'coins', amount: 500 }, { resource: 'brick', amount: 120 }], firstLevel: true, upgradeTo: [] },
  {
    type: 'field_bed',
    category: 'fields',
    name: 'Грядка ветролиста',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 40,
    population: 1,
    health: 70,
    cost: [{ resource: 'coins', amount: 300 }, { resource: 'wood', amount: 4 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 40, population: 1, health: 70, cost: [{ resource: 'coins', amount: 300 }, { resource: 'wood', amount: 4 }] },
      { level: 2, buildSeconds: 210, population: 1, health: 110, cost: [{ resource: 'coins', amount: 1800 }, { resource: 'wood', amount: 16 }, { resource: 'flax', amount: 3 }] },
      { level: 3, buildSeconds: 1205, population: 1, health: 170, cost: [{ resource: 'coins', amount: 6950 }, { resource: 'wood', amount: 40 }, { resource: 'flax', amount: 10 }, { resource: 'planks', amount: 5 }] },
      { level: 4, buildSeconds: 2810, population: 1, health: 250, cost: [{ resource: 'coins', amount: 31000 }, { resource: 'flax', amount: 20 }, { resource: 'windleaf', amount: 3 }, { resource: 'planks', amount: 13 }] },
      { level: 5, buildSeconds: 5660, population: 1, health: 360, cost: [{ resource: 'coins', amount: 92400 }, { resource: 'windleaf', amount: 7 }, { resource: 'planks', amount: 34 }, { resource: 'rope', amount: 5 }] },
      { level: 6, buildSeconds: 8760, population: 1, health: 500, cost: [{ resource: 'coins', amount: 143200 }, { resource: 'planks', amount: 67 }, { resource: 'stone', amount: 19 }, { resource: 'rope', amount: 14 }, { resource: 'windleaf', amount: 9 }] },
      { level: 7, buildSeconds: 8760, population: 1, health: 680, cost: [{ resource: 'coins', amount: 230500 }, { resource: 'planks', amount: 130 }, { resource: 'stone', amount: 40 }, { resource: 'rope', amount: 26 }, { resource: 'fabric', amount: 15 }] },
      { level: 8, buildSeconds: 12660, population: 1, health: 900, cost: [{ resource: 'coins', amount: 361000 }, { resource: 'premium_planks', amount: 1 }, { resource: 'stone_block', amount: 18 }, { resource: 'rope', amount: 49 }, { resource: 'fabric', amount: 32 }] },
      { level: 9, buildSeconds: 18780, population: 1, health: 1150, cost: [{ resource: 'coins', amount: 565000 }, { resource: 'premium_planks', amount: 2 }, { resource: 'stone_block', amount: 30 }, { resource: 'fabric', amount: 57 }, { resource: 'iron_ingot', amount: 2 }] },
      { level: 10, buildSeconds: 28260, population: 1, health: 1450, cost: [{ resource: 'coins', amount: 817400 }, { resource: 'premium_planks', amount: 4 }, { resource: 'stone_block', amount: 61 }, { resource: 'iron_ingot', amount: 5 }] },
      { level: 11, buildSeconds: 37500, population: 1, health: 1800, cost: [{ resource: 'coins', amount: 1185000 }, { resource: 'premium_planks', amount: 7 }, { resource: 'iron_ingot', amount: 9 }, { resource: 'gold_ingot', amount: 2 }, { resource: 'emerald_dust', amount: 1 }] },
    ],
  },
  { type: 'lumber_yard', category: 'industry', name: 'Лесопильный двор', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 140, population: 3, cost: [{ resource: 'coins', amount: 120 }], firstLevel: true, upgradeTo: [] },
  { type: 'stone_cutters', category: 'industry', name: 'Каменотесы', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 160, population: 3, cost: [{ resource: 'coins', amount: 140 }, { resource: 'wood', amount: 60 }], firstLevel: true, upgradeTo: [] },
  { type: 'oil_refinery', category: 'industry', name: 'Нефтеперерабатывающий завод', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 270, population: 4, cost: [{ resource: 'brick', amount: 80 }, { resource: 'metal', amount: 30 }], firstLevel: true, upgradeTo: [] },
]
