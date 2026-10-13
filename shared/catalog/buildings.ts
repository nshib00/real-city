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
  | 'brick_kiln'
  | 'glass_workshop'
  | 'forge'
  | 'weaving_yard'
  | 'dye_works'
  | 'mechanical_workshop'
  | 'optical_workshop'
  | 'mint'
  | 'warehouse'
  | 'coin_storage'
  | 'market'
  | 'tower'
  | 'wooden_wall'
  | 'stone_wall'
  | 'concrete_wall'
  | 'modern_wall'
  | 'road'
  | 'standard_road'
  | 'paved_road'
  | 'alliance_house'
  | 'field_bed'
  | 'seed_garden'
  | 'herb_bed'
  | 'mushroom_grove'
  | 'flax_field'
  | 'reed_bed'
  | 'dye_garden'
  | 'oilseed_field'
  | 'sugar_bed'
  | 'crystal_greenhouse'
  | 'lumber_yard'
  | 'sand_quarry'
  | 'mine'
  | 'clay_quarry'
  | 'iron_mine'
  | 'copper_mine'
  | 'resin_kiln'
  | 'sulfur_spring'
  | 'oil_well'
  | 'stone_cutters'
  | 'tile_factory'
  | 'cement_workshop'
  | 'concrete_plant'
  | 'rope_yard'
  | 'paper_workshop'
  | 'paint_workshop'
  | 'oil_press'
  | 'foundry'
  | 'steelworks'
  | 'electronics_workshop'
  | 'oil_refinery'
  | 'chemical_workshop'
  | 'military_factory'
  | 'precision_workshop'

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
    population: 3,
    health: 100,
    cost: [],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 0, population: 3, health: 100, cost: [] },
      { level: 2, buildSeconds: 90, population: 3, health: 220, cost: [{ resource: 'coins', amount: 1500 }, { resource: 'wood', amount: 40 }, { resource: 'windleaf', amount: 2 }] },
      { level: 3, buildSeconds: 260, population: 3, health: 480, cost: [{ resource: 'coins', amount: 5300 }, { resource: 'wood', amount: 92 }, { resource: 'windleaf', amount: 6 }, { resource: 'glass', amount: 1 }] },
      { level: 4, buildSeconds: 1025, population: 3, health: 910, cost: [{ resource: 'coins', amount: 12000 }, { resource: 'wood', amount: 213 }, { resource: 'mushrooms', amount: 3 }, { resource: 'planks', amount: 17 }, { resource: 'glass', amount: 4 }] },
      { level: 5, buildSeconds: 2170, population: 3, health: 1230, cost: [{ resource: 'coins', amount: 34000 }, { resource: 'wood', amount: 567 }, { resource: 'mushrooms', amount: 10 }, { resource: 'planks', amount: 48 }, { resource: 'glass', amount: 12 }] },
      { level: 6, buildSeconds: 3750, population: 3, health: 1520, cost: [{ resource: 'coins', amount: 78000 }, { resource: 'wood', amount: 1200 }, { resource: 'mushrooms', amount: 27 }, { resource: 'planks', amount: 81 }, { resource: 'stone', amount: 34 }] },
      { level: 7, buildSeconds: 8580, population: 3, health: 1890, cost: [{ resource: 'coins', amount: 145000 }, { resource: 'planks', amount: 195 }, { resource: 'stone', amount: 78 }, { resource: 'stone_block', amount: 25 }] },
      { level: 8, buildSeconds: 13500, population: 3, health: 2360, cost: [{ resource: 'coins', amount: 286000 }, { resource: 'planks', amount: 425 }, { resource: 'stone_block', amount: 52 }, { resource: 'brick', amount: 16 }] },
      { level: 9, buildSeconds: 18840, population: 3, health: 2910, cost: [{ resource: 'coins', amount: 527000 }, { resource: 'stone_block', amount: 121 }, { resource: 'brick', amount: 45 }, { resource: 'glass', amount: 47 }] },
      { level: 10, buildSeconds: 27360, population: 3, health: 3530, cost: [{ resource: 'coins', amount: 875000 }, { resource: 'brick', amount: 109 }, { resource: 'premium_planks', amount: 4 }, { resource: 'super-mushrooms', amount: 2 }, { resource: 'glass', amount: 78 }] },
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
  { type: 'brick_kiln', category: 'industry', name: 'Кирпичная печь', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 210, population: 3, cost: [{ resource: 'coins', amount: 260 }, { resource: 'clay', amount: 70 }, { resource: 'coal', amount: 20 }], firstLevel: true, upgradeTo: [] },
  {
    type: 'glass_workshop',
    category: 'industry',
    name: 'Стекольная мастерская',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 1200,
    population: 6,
    health: 436,
    cost: [{ resource: 'coins', amount: 7000 }, { resource: 'planks', amount: 35 }, { resource: 'stone', amount: 17 }, { resource: 'sand', amount: 60 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 1200, population: 6, health: 436, cost: [{ resource: 'coins', amount: 7000 }, { resource: 'planks', amount: 35 }, { resource: 'stone', amount: 17 }, { resource: 'sand', amount: 60 }] },
      { level: 2, buildSeconds: 2900, population: 8, health: 703, cost: [{ resource: 'coins', amount: 38300 }, { resource: 'stone', amount: 36 }, { resource: 'clay', amount: 20 }, { resource: 'rope', amount: 7 }] },
      { level: 3, buildSeconds: 6050, population: 9, health: 977, cost: [{ resource: 'coins', amount: 87500 }, { resource: 'clay', amount: 53 }, { resource: 'stone_block', amount: 15 }, { resource: 'rope', amount: 18 }, { resource: 'tools', amount: 3 }] },
      { level: 4, buildSeconds: 11400, population: 11, health: 1198, cost: [{ resource: 'coins', amount: 203500 }, { resource: 'stone_block', amount: 30 }, { resource: 'tools', amount: 6 }, { resource: 'brick', amount: 18 }] },
      { level: 5, buildSeconds: 18860, population: 13, health: 1412, cost: [{ resource: 'coins', amount: 415600 }, { resource: 'brick', amount: 37 }, { resource: 'copper_parts', amount: 3 }, { resource: 'glass', amount: 10 }] },
      { level: 6, buildSeconds: 26040, population: 16, health: 1768, cost: [{ resource: 'coins', amount: 674000 }, { resource: 'copper_parts', amount: 7 }, { resource: 'mechanism', amount: 2 }, { resource: 'iron_ingot', amount: 3 }, { resource: 'glass', amount: 21 }] },
      { level: 7, buildSeconds: 32070, population: 19, health: 2037, cost: [{ resource: 'coins', amount: 974000 }, { resource: 'mechanism', amount: 4 }, { resource: 'iron_ingot', amount: 6 }, { resource: 'glass', amount: 33 }] },
      { level: 8, buildSeconds: 40380, population: 22, health: 2448, cost: [{ resource: 'coins', amount: 1228000 }, { resource: 'reinforced_concrete', amount: 8 }, { resource: 'mechanism', amount: 7 }, { resource: 'iron_ingot', amount: 10 }, { resource: 'star_glass', amount: 1 }] },
      { level: 9, buildSeconds: 55830, population: 24, health: 2810, cost: [{ resource: 'coins', amount: 1869000 }, { resource: 'reinforced_concrete', amount: 14 }, { resource: 'reinforced_beams', amount: 2 }, { resource: 'mechanism', amount: 11 }, { resource: 'star_glass', amount: 1 }] },
    ],
  },
  { type: 'forge', category: 'industry', name: 'Кузница', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 4, cost: [{ resource: 'coins', amount: 520 }, { resource: 'stone', amount: 80 }, { resource: 'iron_ore', amount: 35 }, { resource: 'coal', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'weaving_yard', category: 'industry', name: 'Ткацкий двор', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 210, population: 3, cost: [{ resource: 'coins', amount: 300 }, { resource: 'wood', amount: 50 }, { resource: 'flax', amount: 3 }], firstLevel: true, upgradeTo: [] },
  { type: 'dye_works', category: 'industry', name: 'Красильня', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 260, population: 3, cost: [{ resource: 'coins', amount: 420 }, { resource: 'brick', amount: 40 }, { resource: 'fabric', amount: 18 }, { resource: 'herbs', amount: 16 }], firstLevel: true, upgradeTo: [] },
  { type: 'mechanical_workshop', category: 'industry', name: 'Механическая мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 420, population: 5, cost: [{ resource: 'coins', amount: 900 }, { resource: 'iron_ore', amount: 20 }, { resource: 'copper', amount: 20 }, { resource: 'planks', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'optical_workshop', category: 'industry', name: 'Оптическая мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 480, population: 4, cost: [{ resource: 'coins', amount: 1100 }, { resource: 'glass', amount: 28 }, { resource: 'copper', amount: 18 }], firstLevel: true, upgradeTo: [] },
  { type: 'mint', category: 'industry', name: 'Монетный двор', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 600, population: 6, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'brick', amount: 120 }, { resource: 'metal', amount: 45 }], firstLevel: true, upgradeTo: [] },
  { type: 'warehouse', category: 'storage', name: 'Склад материалов', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 2, cost: [{ resource: 'wood', amount: 80 }, { resource: 'stone', amount: 30 }], firstLevel: true, upgradeTo: [] },
  {
    type: 'coin_storage',
    category: 'storage',
    name: 'Хранилище монет',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 420,
    population: 5,
    health: 400,
    cost: [{ resource: 'coins', amount: 1500 }, { resource: 'wood', amount: 70 }, { resource: 'stone', amount: 40 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 420, population: 5, health: 400, cost: [{ resource: 'coins', amount: 1500 }, { resource: 'wood', amount: 70 }, { resource: 'stone', amount: 40 }] },
      { level: 2, buildSeconds: 1590, population: 8, health: 700, cost: [{ resource: 'coins', amount: 3200 }, { resource: 'wood', amount: 120 }, { resource: 'stone', amount: 55 }] },
      { level: 3, buildSeconds: 4320, population: 12, health: 1200, cost: [{ resource: 'coins', amount: 9200 }, { resource: 'planks', amount: 90 }, { resource: 'stone', amount: 120 }, { resource: 'iron_ingot', amount: 4 }] },
      { level: 4, buildSeconds: 8280, population: 17, health: 1900, cost: [{ resource: 'coins', amount: 22500 }, { resource: 'planks', amount: 145 }, { resource: 'stone_block', amount: 18 }, { resource: 'iron_ingot', amount: 8 }] },
      { level: 5, buildSeconds: 14700, population: 23, health: 2700, cost: [{ resource: 'coins', amount: 54000 }, { resource: 'brick', amount: 32 }, { resource: 'glass', amount: 12 }, { resource: 'iron_ingot', amount: 22 }] },
      { level: 6, buildSeconds: 24000, population: 30, health: 3800, cost: [{ resource: 'coins', amount: 128000 }, { resource: 'brick', amount: 62 }, { resource: 'glass', amount: 18 }, { resource: 'copper_parts', amount: 9 }] },
      { level: 7, buildSeconds: 35400, population: 38, health: 5000, cost: [{ resource: 'coins', amount: 300000 }, { resource: 'steel', amount: 9 }, { resource: 'mechanism', amount: 4 }, { resource: 'reinforced_beams', amount: 6 }] },
      { level: 8, buildSeconds: 48600, population: 47, health: 6500, cost: [{ resource: 'coins', amount: 690000 }, { resource: 'reinforced_concrete', amount: 10 }, { resource: 'steel', amount: 16 }, { resource: 'mechanism', amount: 7 }] },
      { level: 9, buildSeconds: 63900, population: 57, health: 8000, cost: [{ resource: 'coins', amount: 1550000 }, { resource: 'reinforced_concrete', amount: 18 }, { resource: 'armor_plates', amount: 4 }, { resource: 'mechanism', amount: 10 }, { resource: 'glass', amount: 24 }] },
      { level: 10, buildSeconds: 80400, population: 68, health: 10000, cost: [{ resource: 'coins', amount: 3400000 }, { resource: 'armor_plates', amount: 8 }, { resource: 'mechanism', amount: 14 }, { resource: 'reinforced_beams', amount: 10 }, { resource: 'gold_ingot', amount: 2 }] },
      { level: 11, buildSeconds: 103200, population: 80, health: 12500, cost: [{ resource: 'coins', amount: 7400000 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'armor_plates', amount: 12 }, { resource: 'reinforced_beams', amount: 16 }, { resource: 'light_crystal', amount: 1 }] },
      { level: 12, buildSeconds: 138600, population: 93, health: 15500, cost: [{ resource: 'coins', amount: 15500000 }, { resource: 'super_mechanism', amount: 2 }, { resource: 'gold_ingot', amount: 6 }, { resource: 'light_crystal', amount: 2 }, { resource: 'reinforced_beams', amount: 22 }] },
    ],
  },
  { type: 'market', category: 'trade', name: 'Рынок', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 4, cost: [{ resource: 'coins', amount: 400 }, { resource: 'wood', amount: 80 }], firstLevel: true, upgradeTo: [] },
  { type: 'tower', category: 'defense', name: 'Сторожевая башня', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 240, population: 2, cost: [{ resource: 'wood', amount: 120 }, { resource: 'stone', amount: 80 }], firstLevel: true, upgradeTo: [] },
  { type: 'wooden_wall', category: 'defense', name: 'Деревянная стена', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 60, population: 1, health: 120, cost: [{ resource: 'wood', amount: 50 }], firstLevel: true, upgradeTo: ['stone_wall'], upgradeLevels: [{ level: 1, buildSeconds: 60, population: 1, health: 120, cost: [{ resource: 'wood', amount: 50 }] }, { level: 2, buildSeconds: 180, population: 1, health: 200, cost: [{ resource: 'coins', amount: 300 }, { resource: 'wood', amount: 90 }] }, { level: 3, buildSeconds: 420, population: 1, health: 320, cost: [{ resource: 'coins', amount: 900 }, { resource: 'wood', amount: 160 }, { resource: 'stone', amount: 20 }], nextType: 'stone_wall' }] },
  { type: 'stone_wall', category: 'defense', name: 'Каменная стена', level: 4, footprint: { width: 1, height: 1 }, buildSeconds: 720, population: 2, health: 600, cost: [{ resource: 'stone', amount: 120 }, { resource: 'brick', amount: 40 }], firstLevel: false, upgradeTo: ['concrete_wall'], upgradeLevels: [{ level: 4, buildSeconds: 720, population: 2, health: 600, cost: [{ resource: 'stone', amount: 120 }, { resource: 'brick', amount: 40 }] }, { level: 5, buildSeconds: 1500, population: 2, health: 850, cost: [{ resource: 'coins', amount: 4500 }, { resource: 'stone', amount: 220 }, { resource: 'brick', amount: 85 }] }, { level: 6, buildSeconds: 3000, population: 3, health: 1150, cost: [{ resource: 'coins', amount: 12000 }, { resource: 'stone_block', amount: 45 }, { resource: 'brick', amount: 160 }] }, { level: 7, buildSeconds: 5400, population: 3, health: 1550, cost: [{ resource: 'coins', amount: 28000 }, { resource: 'stone_block', amount: 90 }, { resource: 'steel', amount: 8 }], nextType: 'concrete_wall' }] },
  { type: 'concrete_wall', category: 'defense', name: 'Бетонная стена', level: 8, footprint: { width: 1, height: 1 }, buildSeconds: 7200, population: 4, health: 2300, cost: [{ resource: 'concrete', amount: 120 }, { resource: 'steel', amount: 30 }], firstLevel: false, upgradeTo: ['modern_wall'], upgradeLevels: [{ level: 8, buildSeconds: 7200, population: 4, health: 2300, cost: [{ resource: 'concrete', amount: 120 }, { resource: 'steel', amount: 30 }] }, { level: 9, buildSeconds: 10800, population: 5, health: 3100, cost: [{ resource: 'coins', amount: 86000 }, { resource: 'reinforced_concrete', amount: 55 }, { resource: 'steel', amount: 65 }] }, { level: 10, buildSeconds: 16200, population: 6, health: 4200, cost: [{ resource: 'coins', amount: 170000 }, { resource: 'reinforced_concrete', amount: 95 }, { resource: 'reinforced_beams', amount: 8 }], nextType: 'modern_wall' }] },
  { type: 'modern_wall', category: 'defense', name: 'Современная стена', level: 11, footprint: { width: 1, height: 1 }, buildSeconds: 21600, population: 7, health: 6200, cost: [{ resource: 'steel', amount: 120 }, { resource: 'electronics', amount: 20 }], firstLevel: false, upgradeTo: [], upgradeLevels: [{ level: 11, buildSeconds: 21600, population: 7, health: 6200, cost: [{ resource: 'steel', amount: 120 }, { resource: 'electronics', amount: 20 }] }, { level: 12, buildSeconds: 32400, population: 8, health: 7600, cost: [{ resource: 'coins', amount: 420000 }, { resource: 'electronics', amount: 45 }, { resource: 'armor_plates', amount: 6 }] }, { level: 13, buildSeconds: 43200, population: 10, health: 9200, cost: [{ resource: 'coins', amount: 760000 }, { resource: 'armor_plates', amount: 10 }, { resource: 'light_crystal', amount: 1 }, { resource: 'super_mechanism', amount: 1 }] }] },
  { type: 'road', category: 'roads', name: 'Грунтовая дорога', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 30, population: 0, health: 40, cost: [{ resource: 'coins', amount: 150 }, { resource: 'clay', amount: 3 }], firstLevel: true, upgradeTo: ['standard_road'], upgradeLevels: [{ level: 1, buildSeconds: 30, population: 0, health: 40, cost: [{ resource: 'coins', amount: 150 }, { resource: 'clay', amount: 3 }], nextType: 'standard_road' }] },
  { type: 'standard_road', category: 'roads', name: 'Обычная дорога', level: 2, footprint: { width: 1, height: 1 }, buildSeconds: 60, population: 0, health: 80, cost: [{ resource: 'coins', amount: 350 }, { resource: 'stone', amount: 8 }], firstLevel: true, upgradeTo: ['paved_road'], upgradeLevels: [{ level: 2, buildSeconds: 60, population: 0, health: 80, cost: [{ resource: 'coins', amount: 350 }, { resource: 'stone', amount: 8 }], nextType: 'paved_road' }] },
  { type: 'paved_road', category: 'roads', name: 'Мостовая', level: 3, footprint: { width: 1, height: 1 }, buildSeconds: 120, population: 0, health: 140, cost: [{ resource: 'coins', amount: 800 }, { resource: 'brick', amount: 12 }, { resource: 'stone_block', amount: 4 }], firstLevel: true, upgradeTo: [] },
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
  {
    type: 'seed_garden',
    category: 'fields',
    name: 'Семенной огород',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 120,
    population: 2,
    health: 65,
    cost: [{ resource: 'coins', amount: 850 }, { resource: 'wood', amount: 35 }, { resource: 'windleaf', amount: 4 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 120, population: 2, health: 65, cost: [{ resource: 'coins', amount: 850 }, { resource: 'wood', amount: 35 }, { resource: 'windleaf', amount: 4 }] },
      { level: 2, buildSeconds: 520, population: 3, health: 184, cost: [{ resource: 'coins', amount: 5000 }, { resource: 'wood', amount: 79 }, { resource: 'windleaf', amount: 10 }] },
      { level: 3, buildSeconds: 1570, population: 4, health: 305, cost: [{ resource: 'coins', amount: 28700 }, { resource: 'wood', amount: 135 }, { resource: 'windleaf', amount: 14 }, { resource: 'rope', amount: 6 }] },
      { level: 4, buildSeconds: 3300, population: 5, health: 430, cost: [{ resource: 'coins', amount: 64000 }, { resource: 'wood', amount: 210 }, { resource: 'windleaf', amount: 20 }, { resource: 'rope', amount: 14 }, { resource: 'planks', amount: 18 }] },
      { level: 5, buildSeconds: 5700, population: 6, health: 560, cost: [{ resource: 'coins', amount: 118000 }, { resource: 'wood', amount: 280 }, { resource: 'windleaf', amount: 28 }, { resource: 'rope', amount: 30 }, { resource: 'planks', amount: 40 }] },
      { level: 6, buildSeconds: 8400, population: 7, health: 700, cost: [{ resource: 'coins', amount: 208000 }, { resource: 'planks', amount: 60 }, { resource: 'stone', amount: 35 }, { resource: 'rope', amount: 42 }, { resource: 'fabric', amount: 8 }, { resource: 'windleaf', amount: 36 }] },
      { level: 7, buildSeconds: 12600, population: 8, health: 860, cost: [{ resource: 'coins', amount: 356000 }, { resource: 'planks', amount: 110 }, { resource: 'stone', amount: 80 }, { resource: 'stone_block', amount: 24 }, { resource: 'fabric', amount: 20 }, { resource: 'windleaf', amount: 56 }] },
      { level: 8, buildSeconds: 18000, population: 9, health: 1040, cost: [{ resource: 'coins', amount: 590000 }, { resource: 'premium_planks', amount: 2 }, { resource: 'stone_block', amount: 48 }, { resource: 'fabric', amount: 36 }, { resource: 'iron_ingot', amount: 4 }, { resource: 'windleaf', amount: 75 }] },
      { level: 9, buildSeconds: 27000, population: 10, health: 1240, cost: [{ resource: 'coins', amount: 920000 }, { resource: 'premium_planks', amount: 4 }, { resource: 'stone_block', amount: 72 }, { resource: 'iron_ingot', amount: 7 }, { resource: 'gold_ingot', amount: 2 }, { resource: 'emerald_dust', amount: 1 }] },
      { level: 10, buildSeconds: 36000, population: 12, health: 1480, cost: [{ resource: 'coins', amount: 1370000 }, { resource: 'premium_planks', amount: 7 }, { resource: 'stone_block', amount: 110 }, { resource: 'iron_ingot', amount: 12 }, { resource: 'gold_ingot', amount: 3 }, { resource: 'emerald_dust', amount: 2 }, { resource: 'super-seeds', amount: 1 }] }
    ],
  },
  {
    type: 'herb_bed',
    category: 'fields',
    name: 'Травяная грядка',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 120,
    population: 1,
    health: 70,
    cost: [{ resource: 'coins', amount: 75000 }, { resource: 'seeds', amount: 45 }, { resource: 'planks', amount: 45 }, { resource: 'fabric', amount: 18 }, { resource: 'rope', amount: 8 }, { resource: 'windleaf', amount: 6 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 75000 }, { resource: 'seeds', amount: 45 }, { resource: 'planks', amount: 45 }, { resource: 'fabric', amount: 18 }, { resource: 'rope', amount: 8 }, { resource: 'windleaf', amount: 6 }] },
      { level: 2, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 120000 }, { resource: 'seeds', amount: 65 }, { resource: 'planks', amount: 60 }, { resource: 'fabric', amount: 26 }, { resource: 'rope', amount: 14 }, { resource: 'windleaf', amount: 10 }, { resource: 'brick', amount: 12 }] },
      { level: 3, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 185000 }, { resource: 'seeds', amount: 90 }, { resource: 'planks', amount: 85 }, { resource: 'fabric', amount: 36 }, { resource: 'rope', amount: 20 }, { resource: 'windleaf', amount: 18 }, { resource: 'stone_block', amount: 20 }] },
      { level: 4, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 280000 }, { resource: 'seeds', amount: 120 }, { resource: 'planks', amount: 110 }, { resource: 'fabric', amount: 50 }, { resource: 'rope', amount: 30 }, { resource: 'stone_block', amount: 28 }, { resource: 'iron_ingot', amount: 2 }] },
      { level: 5, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 410000 }, { resource: 'seeds', amount: 155 }, { resource: 'premium_planks', amount: 1 }, { resource: 'fabric', amount: 70 }, { resource: 'stone_block', amount: 44 }, { resource: 'iron_ingot', amount: 4 }, { resource: 'blue_salt', amount: 1 }] },
      { level: 6, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 590000 }, { resource: 'seeds', amount: 200 }, { resource: 'premium_planks', amount: 2 }, { resource: 'fabric', amount: 95 }, { resource: 'stone_block', amount: 60 }, { resource: 'iron_ingot', amount: 6 }, { resource: 'blue_salt', amount: 2 }] },
      { level: 7, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 820000 }, { resource: 'seeds', amount: 260 }, { resource: 'premium_planks', amount: 3 }, { resource: 'fabric', amount: 125 }, { resource: 'stone_block', amount: 82 }, { resource: 'iron_ingot', amount: 9 }, { resource: 'emerald_dust', amount: 1 }] },
      { level: 8, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 1100000 }, { resource: 'seeds', amount: 330 }, { resource: 'premium_planks', amount: 4 }, { resource: 'fabric', amount: 160 }, { resource: 'stone_block', amount: 110 }, { resource: 'iron_ingot', amount: 12 }, { resource: 'emerald_dust', amount: 2 }, { resource: 'rare_flowers', amount: 1 }] },
      { level: 9, buildSeconds: 120, population: 1, health: 70, cost: [{ resource: 'coins', amount: 1450000 }, { resource: 'seeds', amount: 420 }, { resource: 'premium_planks', amount: 6 }, { resource: 'fabric', amount: 210 }, { resource: 'stone_block', amount: 145 }, { resource: 'iron_ingot', amount: 16 }, { resource: 'emerald_dust', amount: 3 }, { resource: 'super-seeds', amount: 1 }] }
    ],
  },
  {
    type: 'mushroom_grove',
    category: 'fields',
    name: 'Грибница',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 150,
    population: 1,
    health: 80,
    cost: [{ resource: 'coins', amount: 25000 }, { resource: 'planks', amount: 40 }, { resource: 'stone', amount: 18 }, { resource: 'resin', amount: 8 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 25000 }, { resource: 'planks', amount: 40 }, { resource: 'stone', amount: 18 }, { resource: 'resin', amount: 8 }] },
      { level: 2, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 55000 }, { resource: 'planks', amount: 65 }, { resource: 'stone', amount: 30 }, { resource: 'resin', amount: 14 }, { resource: 'brick', amount: 8 }] },
      { level: 3, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 105000 }, { resource: 'planks', amount: 90 }, { resource: 'stone', amount: 50 }, { resource: 'resin', amount: 22 }, { resource: 'brick', amount: 18 }, { resource: 'windleaf', amount: 8 }] },
      { level: 4, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 180000 }, { resource: 'planks', amount: 120 }, { resource: 'stone', amount: 70 }, { resource: 'resin', amount: 34 }, { resource: 'brick', amount: 30 }, { resource: 'fabric', amount: 14 }] },
      { level: 5, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 300000 }, { resource: 'premium_planks', amount: 1 }, { resource: 'stone', amount: 95 }, { resource: 'resin', amount: 48 }, { resource: 'stone_block', amount: 28 }, { resource: 'fabric', amount: 24 }] },
      { level: 6, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 470000 }, { resource: 'premium_planks', amount: 2 }, { resource: 'stone', amount: 130 }, { resource: 'resin', amount: 64 }, { resource: 'stone_block', amount: 45 }, { resource: 'iron_ingot', amount: 2 }, { resource: 'blue_salt', amount: 1 }] },
      { level: 7, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 700000 }, { resource: 'premium_planks', amount: 3 }, { resource: 'resin', amount: 80 }, { resource: 'stone_block', amount: 70 }, { resource: 'iron_ingot', amount: 4 }, { resource: 'blue_salt', amount: 2 }] },
      { level: 8, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 1000000 }, { resource: 'premium_planks', amount: 4 }, { resource: 'resin', amount: 105 }, { resource: 'stone_block', amount: 95 }, { resource: 'iron_ingot', amount: 7 }, { resource: 'blue_salt', amount: 3 }, { resource: 'emerald_dust', amount: 1 }] },
      { level: 9, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 1380000 }, { resource: 'premium_planks', amount: 6 }, { resource: 'resin', amount: 135 }, { resource: 'stone_block', amount: 130 }, { resource: 'iron_ingot', amount: 10 }, { resource: 'emerald_dust', amount: 2 }, { resource: 'super-mushrooms', amount: 1 }] },
      { level: 10, buildSeconds: 150, population: 1, health: 80, cost: [{ resource: 'coins', amount: 1850000 }, { resource: 'premium_planks', amount: 8 }, { resource: 'resin', amount: 170 }, { resource: 'stone_block', amount: 170 }, { resource: 'iron_ingot', amount: 14 }, { resource: 'emerald_dust', amount: 3 }, { resource: 'super-mushrooms', amount: 2 }, { resource: 'super-seeds', amount: 1 }] }
    ],
  },
  {
    type: 'flax_field',
    category: 'fields',
    name: 'Льняное поле',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 1080,
    population: 2,
    health: 80,
    cost: [{ resource: 'coins', amount: 2500 }, { resource: 'wood', amount: 87 }, { resource: 'seeds', amount: 12 }, { resource: 'windleaf', amount: 10 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 1080, population: 2, health: 80, cost: [{ resource: 'coins', amount: 2500 }, { resource: 'wood', amount: 87 }, { resource: 'seeds', amount: 12 }, { resource: 'windleaf', amount: 10 }] },
      { level: 2, buildSeconds: 2430, population: 3, health: 180, cost: [{ resource: 'coins', amount: 19000 }, { resource: 'wood', amount: 160 }, { resource: 'windleaf', amount: 12 }, { resource: 'rope', amount: 5 }] },
      { level: 3, buildSeconds: 3900, population: 3, health: 220, cost: [{ resource: 'coins', amount: 46400 }, { resource: 'windleaf', amount: 17 }, { resource: 'rope', amount: 8 }, { resource: 'planks', amount: 29 }] },
      { level: 4, buildSeconds: 3480, population: 3, health: 340, cost: [{ resource: 'coins', amount: 75000 }, { resource: 'planks', amount: 42 }, { resource: 'rope', amount: 12 }, { resource: 'windleaf', amount: 20 }] },
      { level: 5, buildSeconds: 6300, population: 4, health: 480, cost: [{ resource: 'coins', amount: 106000 }, { resource: 'seeds', amount: 36 }, { resource: 'planks', amount: 34 }, { resource: 'rope', amount: 18 }, { resource: 'windleaf', amount: 6 }, { resource: 'stone', amount: 20 }] },
      { level: 6, buildSeconds: 9900, population: 5, health: 640, cost: [{ resource: 'coins', amount: 148000 }, { resource: 'planks', amount: 55 }, { resource: 'rope', amount: 30 }, { resource: 'fabric', amount: 12 }, { resource: 'stone', amount: 15 }, { resource: 'brick', amount: 24 }, { resource: 'stone_block', amount: 10 }] },
      { level: 7, buildSeconds: 14400, population: 6, health: 830, cost: [{ resource: 'coins', amount: 260000 }, { resource: 'planks', amount: 90 }, { resource: 'rope', amount: 48 }, { resource: 'fabric', amount: 26 }, { resource: 'brick', amount: 36 }, { resource: 'stone_block', amount: 20 }] },
      { level: 8, buildSeconds: 20400, population: 7, health: 1050, cost: [{ resource: 'coins', amount: 430000 }, { resource: 'premium_planks', amount: 1 }, { resource: 'brick', amount: 54 }, { resource: 'stone_block', amount: 42 }, { resource: 'fabric', amount: 55 }, { resource: 'iron_ingot', amount: 3 }] },
      { level: 9, buildSeconds: 28800, population: 8, health: 1320, cost: [{ resource: 'coins', amount: 690000 }, { resource: 'premium_planks', amount: 3 }, { resource: 'stone_block', amount: 64 }, { resource: 'fabric', amount: 85 }, { resource: 'iron_ingot', amount: 6 }, { resource: 'gold_ingot', amount: 1 }] },
      { level: 10, buildSeconds: 39600, population: 10, health: 1640, cost: [{ resource: 'coins', amount: 1040000 }, { resource: 'premium_planks', amount: 5 }, { resource: 'stone_block', amount: 96 }, { resource: 'fabric', amount: 120 }, { resource: 'iron_ingot', amount: 10 }, { resource: 'gold_ingot', amount: 2 }, { resource: 'super-seeds', amount: 1 }] }
    ],
  },
  {
    type: 'reed_bed',
    category: 'fields',
    name: 'Тростниковая грядка',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 180,
    population: 1,
    health: 85,
    cost: [{ resource: 'coins', amount: 16000 }, { resource: 'planks', amount: 24 }, { resource: 'clay', amount: 16 }, { resource: 'rope', amount: 6 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 16000 }, { resource: 'planks', amount: 24 }, { resource: 'clay', amount: 16 }, { resource: 'rope', amount: 6 }] },
      { level: 2, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 36000 }, { resource: 'planks', amount: 40 }, { resource: 'clay', amount: 28 }, { resource: 'rope', amount: 12 }, { resource: 'brick', amount: 10 }] },
      { level: 3, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 78000 }, { resource: 'planks', amount: 60 }, { resource: 'clay', amount: 42 }, { resource: 'rope', amount: 20 }, { resource: 'brick', amount: 22 }, { resource: 'fabric', amount: 8 }] },
      { level: 4, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 145000 }, { resource: 'planks', amount: 85 }, { resource: 'clay', amount: 60 }, { resource: 'rope', amount: 34 }, { resource: 'brick', amount: 36 }, { resource: 'stone_block', amount: 14 }] },
      { level: 5, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 250000 }, { resource: 'planks', amount: 115 }, { resource: 'clay', amount: 80 }, { resource: 'rope', amount: 50 }, { resource: 'brick', amount: 56 }, { resource: 'stone_block', amount: 28 }] },
      { level: 6, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 400000 }, { resource: 'premium_planks', amount: 1 }, { resource: 'clay', amount: 105 }, { resource: 'rope', amount: 70 }, { resource: 'brick', amount: 80 }, { resource: 'stone_block', amount: 45 }, { resource: 'blue_salt', amount: 1 }] },
      { level: 7, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 610000 }, { resource: 'premium_planks', amount: 2 }, { resource: 'clay', amount: 135 }, { resource: 'rope', amount: 95 }, { resource: 'stone_block', amount: 65 }, { resource: 'iron_ingot', amount: 3 }, { resource: 'blue_salt', amount: 2 }] },
      { level: 8, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 880000 }, { resource: 'premium_planks', amount: 3 }, { resource: 'clay', amount: 170 }, { resource: 'rope', amount: 125 }, { resource: 'stone_block', amount: 90 }, { resource: 'iron_ingot', amount: 5 }, { resource: 'light_crystal', amount: 1 }] },
      { level: 9, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 1220000 }, { resource: 'premium_planks', amount: 5 }, { resource: 'clay', amount: 215 }, { resource: 'rope', amount: 160 }, { resource: 'stone_block', amount: 120 }, { resource: 'iron_ingot', amount: 8 }, { resource: 'light_crystal', amount: 2 }] },
      { level: 10, buildSeconds: 180, population: 1, health: 85, cost: [{ resource: 'coins', amount: 1650000 }, { resource: 'premium_planks', amount: 7 }, { resource: 'clay', amount: 270 }, { resource: 'rope', amount: 210 }, { resource: 'stone_block', amount: 155 }, { resource: 'iron_ingot', amount: 12 }, { resource: 'blue_salt', amount: 3 }, { resource: 'light_crystal', amount: 3 }] }
    ],
  },
  {
    type: 'dye_garden',
    category: 'fields',
    name: 'Красильный сад',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 220,
    population: 1,
    health: 90,
    cost: [{ resource: 'coins', amount: 780000 }, { resource: 'herbs', amount: 140 }, { resource: 'dyes', amount: 90 }, { resource: 'fabric', amount: 120 }, { resource: 'stone_block', amount: 65 }, { resource: 'gold_ingot', amount: 3 }, { resource: 'rare_flowers', amount: 1 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 220, population: 1, health: 90, cost: [{ resource: 'coins', amount: 780000 }, { resource: 'herbs', amount: 140 }, { resource: 'dyes', amount: 90 }, { resource: 'fabric', amount: 120 }, { resource: 'stone_block', amount: 65 }, { resource: 'gold_ingot', amount: 3 }, { resource: 'rare_flowers', amount: 1 }] },
      { level: 2, buildSeconds: 220, population: 1, health: 90, cost: [{ resource: 'coins', amount: 1250000 }, { resource: 'herbs', amount: 190 }, { resource: 'dyes', amount: 140 }, { resource: 'fabric', amount: 170 }, { resource: 'stone_block', amount: 95 }, { resource: 'gold_ingot', amount: 5 }, { resource: 'rare_flowers', amount: 2 }, { resource: 'premium_planks', amount: 2 }] },
      { level: 3, buildSeconds: 220, population: 1, health: 90, cost: [{ resource: 'coins', amount: 1900000 }, { resource: 'herbs', amount: 260 }, { resource: 'dyes', amount: 210 }, { resource: 'fabric', amount: 235 }, { resource: 'stone_block', amount: 135 }, { resource: 'gold_ingot', amount: 8 }, { resource: 'rare_flowers', amount: 3 }, { resource: 'emerald_dust', amount: 1 }] },
      { level: 4, buildSeconds: 220, population: 1, health: 90, cost: [{ resource: 'coins', amount: 2750000 }, { resource: 'herbs', amount: 350 }, { resource: 'dyes', amount: 300 }, { resource: 'fabric', amount: 320 }, { resource: 'stone_block', amount: 185 }, { resource: 'gold_ingot', amount: 12 }, { resource: 'rare_flowers', amount: 5 }, { resource: 'emerald_dust', amount: 2 }, { resource: 'mechanism', amount: 1 }] },
      { level: 5, buildSeconds: 220, population: 1, health: 90, cost: [{ resource: 'coins', amount: 3850000 }, { resource: 'herbs', amount: 470 }, { resource: 'dyes', amount: 420 }, { resource: 'fabric', amount: 430 }, { resource: 'stone_block', amount: 250 }, { resource: 'gold_ingot', amount: 18 }, { resource: 'rare_flowers', amount: 8 }, { resource: 'emerald_dust', amount: 3 }, { resource: 'mechanism', amount: 2 }, { resource: 'star_glass', amount: 1 }] },
      { level: 6, buildSeconds: 220, population: 1, health: 90, cost: [{ resource: 'coins', amount: 5250000 }, { resource: 'herbs', amount: 620 }, { resource: 'dyes', amount: 580 }, { resource: 'fabric', amount: 580 }, { resource: 'stone_block', amount: 330 }, { resource: 'gold_ingot', amount: 26 }, { resource: 'rare_flowers', amount: 12 }, { resource: 'emerald_dust', amount: 5 }, { resource: 'mechanism', amount: 3 }, { resource: 'star_glass', amount: 2 }] }
    ],
  },
  {
    type: 'oilseed_field',
    category: 'fields',
    name: 'Масличное поле',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 240,
    population: 1,
    health: 90,
    cost: [{ resource: 'coins', amount: 260000 }, { resource: 'seeds', amount: 130 }, { resource: 'planks', amount: 90 }, { resource: 'fabric', amount: 42 }, { resource: 'stone_block', amount: 30 }, { resource: 'iron_ingot', amount: 3 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 260000 }, { resource: 'seeds', amount: 130 }, { resource: 'planks', amount: 90 }, { resource: 'fabric', amount: 42 }, { resource: 'stone_block', amount: 30 }, { resource: 'iron_ingot', amount: 3 }] },
      { level: 2, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 430000 }, { resource: 'seeds', amount: 180 }, { resource: 'planks', amount: 125 }, { resource: 'fabric', amount: 60 }, { resource: 'stone_block', amount: 48 }, { resource: 'iron_ingot', amount: 5 }, { resource: 'premium_planks', amount: 1 }] },
      { level: 3, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 680000 }, { resource: 'seeds', amount: 240 }, { resource: 'planks', amount: 170 }, { resource: 'fabric', amount: 85 }, { resource: 'stone_block', amount: 72 }, { resource: 'iron_ingot', amount: 8 }, { resource: 'premium_planks', amount: 2 }] },
      { level: 4, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 1020000 }, { resource: 'seeds', amount: 320 }, { resource: 'premium_planks', amount: 3 }, { resource: 'fabric', amount: 115 }, { resource: 'stone_block', amount: 100 }, { resource: 'iron_ingot', amount: 12 }, { resource: 'mechanism', amount: 1 }] },
      { level: 5, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 1470000 }, { resource: 'seeds', amount: 420 }, { resource: 'premium_planks', amount: 4 }, { resource: 'fabric', amount: 155 }, { resource: 'stone_block', amount: 135 }, { resource: 'iron_ingot', amount: 16 }, { resource: 'mechanism', amount: 2 }, { resource: 'gold_ingot', amount: 1 }] },
      { level: 6, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 2050000 }, { resource: 'seeds', amount: 540 }, { resource: 'premium_planks', amount: 6 }, { resource: 'fabric', amount: 200 }, { resource: 'stone_block', amount: 180 }, { resource: 'iron_ingot', amount: 22 }, { resource: 'mechanism', amount: 3 }, { resource: 'gold_ingot', amount: 2 }] },
      { level: 7, buildSeconds: 240, population: 1, health: 90, cost: [{ resource: 'coins', amount: 2780000 }, { resource: 'seeds', amount: 700 }, { resource: 'premium_planks', amount: 8 }, { resource: 'fabric', amount: 260 }, { resource: 'stone_block', amount: 240 }, { resource: 'iron_ingot', amount: 30 }, { resource: 'mechanism', amount: 4 }, { resource: 'gold_ingot', amount: 3 }, { resource: 'super-seeds', amount: 1 }] }
    ],
  },
  {
    type: 'sugar_bed',
    category: 'fields',
    name: 'Сахарная грядка',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 260,
    population: 1,
    health: 95,
    cost: [{ resource: 'coins', amount: 125000 }, { resource: 'seeds', amount: 80 }, { resource: 'planks', amount: 55 }, { resource: 'reed', amount: 30 }, { resource: 'fabric', amount: 24 }, { resource: 'clay', amount: 18 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 125000 }, { resource: 'seeds', amount: 80 }, { resource: 'planks', amount: 55 }, { resource: 'reed', amount: 30 }, { resource: 'fabric', amount: 24 }, { resource: 'clay', amount: 18 }] },
      { level: 2, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 210000 }, { resource: 'seeds', amount: 110 }, { resource: 'planks', amount: 80 }, { resource: 'reed', amount: 45 }, { resource: 'fabric', amount: 36 }, { resource: 'clay', amount: 30 }, { resource: 'brick', amount: 14 }] },
      { level: 3, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 340000 }, { resource: 'seeds', amount: 150 }, { resource: 'planks', amount: 110 }, { resource: 'reed', amount: 65 }, { resource: 'fabric', amount: 52 }, { resource: 'brick', amount: 48 }, { resource: 'stone_block', amount: 22 }] },
      { level: 4, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 520000 }, { resource: 'seeds', amount: 200 }, { resource: 'planks', amount: 150 }, { resource: 'reed', amount: 90 }, { resource: 'fabric', amount: 75 }, { resource: 'brick', amount: 70 }, { resource: 'stone_block', amount: 35 }] },
      { level: 5, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 760000 }, { resource: 'seeds', amount: 260 }, { resource: 'premium_planks', amount: 1 }, { resource: 'reed', amount: 120 }, { resource: 'fabric', amount: 105 }, { resource: 'stone_block', amount: 55 }, { resource: 'iron_ingot', amount: 3 }] },
      { level: 6, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 1070000 }, { resource: 'seeds', amount: 340 }, { resource: 'premium_planks', amount: 2 }, { resource: 'reed', amount: 155 }, { resource: 'fabric', amount: 140 }, { resource: 'stone_block', amount: 80 }, { resource: 'iron_ingot', amount: 5 }, { resource: 'blue_salt', amount: 1 }] },
      { level: 7, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 1470000 }, { resource: 'seeds', amount: 430 }, { resource: 'premium_planks', amount: 4 }, { resource: 'reed', amount: 200 }, { resource: 'fabric', amount: 180 }, { resource: 'stone_block', amount: 110 }, { resource: 'iron_ingot', amount: 8 }, { resource: 'blue_salt', amount: 2 }] },
      { level: 8, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 1980000 }, { resource: 'seeds', amount: 540 }, { resource: 'premium_planks', amount: 6 }, { resource: 'reed', amount: 255 }, { resource: 'fabric', amount: 230 }, { resource: 'stone_block', amount: 150 }, { resource: 'iron_ingot', amount: 12 }, { resource: 'gold_ingot', amount: 2 }] },
      { level: 9, buildSeconds: 260, population: 1, health: 95, cost: [{ resource: 'coins', amount: 2600000 }, { resource: 'seeds', amount: 680 }, { resource: 'premium_planks', amount: 8 }, { resource: 'reed', amount: 330 }, { resource: 'fabric', amount: 300 }, { resource: 'stone_block', amount: 200 }, { resource: 'iron_ingot', amount: 18 }, { resource: 'gold_ingot', amount: 3 }, { resource: 'super-seeds', amount: 1 }] }
    ],
  },
  {
    type: 'crystal_greenhouse',
    category: 'fields',
    name: 'Кристальная оранжерея',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 900,
    population: 4,
    health: 260,
    cost: [{ resource: 'coins', amount: 2300000 }, { resource: 'glass', amount: 260 }, { resource: 'star_glass', amount: 1 }, { resource: 'copper_parts', amount: 90 }, { resource: 'stone_block', amount: 90 }, { resource: 'light_crystal', amount: 8 }, { resource: 'mechanism', amount: 1 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 900, population: 4, health: 260, cost: [{ resource: 'coins', amount: 2300000 }, { resource: 'glass', amount: 260 }, { resource: 'star_glass', amount: 1 }, { resource: 'copper_parts', amount: 90 }, { resource: 'stone_block', amount: 90 }, { resource: 'light_crystal', amount: 8 }, { resource: 'mechanism', amount: 1 }] },
      { level: 2, buildSeconds: 900, population: 4, health: 260, cost: [{ resource: 'coins', amount: 3700000 }, { resource: 'glass', amount: 380 }, { resource: 'star_glass', amount: 2 }, { resource: 'copper_parts', amount: 130 }, { resource: 'stone_block', amount: 135 }, { resource: 'light_crystal', amount: 12 }, { resource: 'mechanism', amount: 2 }, { resource: 'emerald_dust', amount: 1 }] },
      { level: 3, buildSeconds: 900, population: 4, health: 260, cost: [{ resource: 'coins', amount: 5500000 }, { resource: 'glass', amount: 540 }, { resource: 'star_glass', amount: 4 }, { resource: 'copper_parts', amount: 190 }, { resource: 'stone_block', amount: 200 }, { resource: 'light_crystal', amount: 18 }, { resource: 'mechanism', amount: 3 }, { resource: 'emerald_dust', amount: 3 }] },
      { level: 4, buildSeconds: 900, population: 4, health: 260, cost: [{ resource: 'coins', amount: 7800000 }, { resource: 'glass', amount: 760 }, { resource: 'star_glass', amount: 7 }, { resource: 'copper_parts', amount: 270 }, { resource: 'stone_block', amount: 290 }, { resource: 'light_crystal', amount: 28 }, { resource: 'mechanism', amount: 5 }, { resource: 'emerald_dust', amount: 5 }, { resource: 'aeolian-crystal', amount: 1 }] }
    ],
  },
  {
    type: 'lumber_yard',
    category: 'industry',
    name: 'Лесопильный двор',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 270,
    population: 3,
    health: 120,
    cost: [{ resource: 'coins', amount: 1200 }, { resource: 'wood', amount: 30 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 270, population: 3, health: 120, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'wood', amount: 30 }] },
      { level: 2, buildSeconds: 920, population: 3, health: 180, cost: [{ resource: 'coins', amount: 15600 }, { resource: 'wood', amount: 145 }, { resource: 'planks', amount: 15 }] },
      { level: 3, buildSeconds: 2470, population: 4, health: 260, cost: [{ resource: 'coins', amount: 42000 }, { resource: 'planks', amount: 38 }, { resource: 'stone', amount: 19 }] },
      { level: 4, buildSeconds: 6600, population: 4, health: 370, cost: [{ resource: 'coins', amount: 98300 }, { resource: 'planks', amount: 97 }, { resource: 'brick', amount: 15 }, { resource: 'stone', amount: 57 }] },
      { level: 5, buildSeconds: 13680, population: 5, health: 520, cost: [{ resource: 'coins', amount: 203000 }, { resource: 'planks', amount: 180 }, { resource: 'brick', amount: 38 }, { resource: 'copper_parts', amount: 7 }] },
      { level: 6, buildSeconds: 19920, population: 5, health: 720, cost: [{ resource: 'coins', amount: 356000 }, { resource: 'brick', amount: 63 }, { resource: 'copper_parts', amount: 19 }, { resource: 'iron_ingot', amount: 2 }] },
      { level: 7, buildSeconds: 25380, population: 6, health: 980, cost: [{ resource: 'coins', amount: 567500 }, { resource: 'brick', amount: 112 }, { resource: 'copper_parts', amount: 36 }, { resource: 'iron_ingot', amount: 5 }] },
      { level: 8, buildSeconds: 35400, population: 6, health: 1310, cost: [{ resource: 'coins', amount: 742000 }, { resource: 'iron_ingot', amount: 8 }, { resource: 'copper_parts', amount: 54 }, { resource: 'reinforced_concrete', amount: 6 }, { resource: 'premium_planks', amount: 2 }] },
      { level: 9, buildSeconds: 43500, population: 7, health: 1720, cost: [{ resource: 'coins', amount: 981000 }, { resource: 'iron_ingot', amount: 12 }, { resource: 'mechanism', amount: 2 }, { resource: 'reinforced_concrete', amount: 9 }, { resource: 'premium_planks', amount: 3 }] },
      { level: 10, buildSeconds: 54000, population: 7, health: 2210, cost: [{ resource: 'coins', amount: 1254000 }, { resource: 'iron_ingot', amount: 15 }, { resource: 'mechanism', amount: 4 }, { resource: 'reinforced_concrete', amount: 12 }, { resource: 'premium_planks', amount: 4 }] },
      { level: 11, buildSeconds: 61200, population: 8, health: 2790, cost: [{ resource: 'coins', amount: 1570000 }, { resource: 'rune_tile', amount: 1 }, { resource: 'mechanism', amount: 6 }, { resource: 'reinforced_concrete', amount: 16 }, { resource: 'premium_planks', amount: 5 }] },
      { level: 12, buildSeconds: 72000, population: 8, health: 3460, cost: [{ resource: 'coins', amount: 1890000 }, { resource: 'rune_tile', amount: 1 }, { resource: 'gold_ingot', amount: 3 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'premium_planks', amount: 7 }] },
      { level: 13, buildSeconds: 86400, population: 9, health: 4220, cost: [{ resource: 'coins', amount: 2400000 }, { resource: 'rune_tile', amount: 2 }, { resource: 'gold_ingot', amount: 5 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'premium_planks', amount: 9 }] },
    ],
  },
  {
    type: 'sand_quarry',
    category: 'industry',
    name: 'Песчаный карьер',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 390,
    population: 4,
    health: 84,
    cost: [{ resource: 'coins', amount: 1800 }, { resource: 'stone', amount: 13 }, { resource: 'planks', amount: 7 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 390, population: 4, health: 84, cost: [{ resource: 'coins', amount: 1800 }, { resource: 'stone', amount: 13 }, { resource: 'planks', amount: 7 }] },
      { level: 2, buildSeconds: 1010, population: 5, health: 212, cost: [{ resource: 'coins', amount: 13900 }, { resource: 'stone', amount: 46 }, { resource: 'planks', amount: 25 }, { resource: 'rope', amount: 5 }] },
      { level: 3, buildSeconds: 2420, population: 7, health: 324, cost: [{ resource: 'coins', amount: 38400 }, { resource: 'stone_block', amount: 8 }, { resource: 'planks', amount: 68 }, { resource: 'rope', amount: 13 }] },
      { level: 4, buildSeconds: 5645, population: 8, health: 501, cost: [{ resource: 'coins', amount: 94100 }, { resource: 'stone_block', amount: 20 }, { resource: 'rope', amount: 25 }, { resource: 'brick', amount: 16 }] },
      { level: 5, buildSeconds: 10680, population: 10, health: 654, cost: [{ resource: 'coins', amount: 168000 }, { resource: 'brick', amount: 25 }, { resource: 'rope', amount: 32 }, { resource: 'copper_parts', amount: 9 }, { resource: 'iron_ingot', amount: 2 }] },
      { level: 6, buildSeconds: 17010, population: 12, health: 874, cost: [{ resource: 'coins', amount: 324000 }, { resource: 'rope', amount: 48 }, { resource: 'copper_parts', amount: 20 }, { resource: 'iron_ingot', amount: 4 }, { resource: 'steel', amount: 1 }] },
      { level: 7, buildSeconds: 23640, population: 15, health: 1132, cost: [{ resource: 'coins', amount: 556000 }, { resource: 'copper_parts', amount: 36 }, { resource: 'iron_ingot', amount: 7 }, { resource: 'steel', amount: 3 }, { resource: 'premium_planks', amount: 1 }] },
      { level: 8, buildSeconds: 37440, population: 17, health: 1390, cost: [{ resource: 'coins', amount: 796500 }, { resource: 'mechanism', amount: 3 }, { resource: 'iron_ingot', amount: 13 }, { resource: 'steel', amount: 7 }, { resource: 'premium_planks', amount: 2 }] },
      { level: 9, buildSeconds: 46920, population: 19, health: 1685, cost: [{ resource: 'coins', amount: 1057500 }, { resource: 'mechanism', amount: 5 }, { resource: 'steel', amount: 12 }, { resource: 'blue_salt', amount: 2 }, { resource: 'premium_planks', amount: 4 }] },
      { level: 10, buildSeconds: 0, population: 21, health: 1877, cost: [{ resource: 'coins', amount: 1402000 }, { resource: 'mechanism', amount: 8 }, { resource: 'rune_tile', amount: 1 }, { resource: 'blue_salt', amount: 3 }, { resource: 'steel', amount: 19 }, { resource: 'premium_planks', amount: 6 }] },
      { level: 11, buildSeconds: 0, population: 23, health: 2055, cost: [{ resource: 'coins', amount: 1987000 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'mechanism', amount: 13 }, { resource: 'blue_salt', amount: 5 }, { resource: 'gold_ingot', amount: 4 }, { resource: 'premium_planks', amount: 8 }] },
    ],
  },
  {
    type: 'mine',
    category: 'industry',
    name: 'Шахта',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 720,
    population: 5,
    health: 176,
    cost: [{ resource: 'coins', amount: 4000 }, { resource: 'wood', amount: 78 }, { resource: 'planks', amount: 15 }, { resource: 'rope', amount: 8 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 720, population: 5, health: 176, cost: [{ resource: 'coins', amount: 4000 }, { resource: 'wood', amount: 78 }, { resource: 'planks', amount: 15 }, { resource: 'rope', amount: 8 }] },
      { level: 2, buildSeconds: 2010, population: 6, health: 297, cost: [{ resource: 'coins', amount: 20300 }, { resource: 'wood', amount: 138 }, { resource: 'planks', amount: 34 }, { resource: 'rope', amount: 15 }] },
      { level: 3, buildSeconds: 3760, population: 7, health: 435, cost: [{ resource: 'coins', amount: 55400 }, { resource: 'planks', amount: 56 }, { resource: 'stone', amount: 24 }, { resource: 'rope', amount: 23 }] },
      { level: 4, buildSeconds: 6990, population: 9, health: 685, cost: [{ resource: 'coins', amount: 98100 }, { resource: 'planks', amount: 80 }, { resource: 'stone', amount: 46 }, { resource: 'stone_block', amount: 10 }, { resource: 'tools', amount: 3 }] },
      { level: 5, buildSeconds: 11670, population: 11, health: 910, cost: [{ resource: 'coins', amount: 160000 }, { resource: 'stone_block', amount: 21 }, { resource: 'brick', amount: 6 }, { resource: 'iron_ingot', amount: 2 }, { resource: 'tools', amount: 5 }] },
      { level: 6, buildSeconds: 16440, population: 13, health: 1136, cost: [{ resource: 'coins', amount: 314300 }, { resource: 'brick', amount: 16 }, { resource: 'iron_ingot', amount: 4 }, { resource: 'mechanism', amount: 3 }, { resource: 'tools', amount: 7 }] },
      { level: 7, buildSeconds: 22800, population: 15, health: 1403, cost: [{ resource: 'coins', amount: 498600 }, { resource: 'iron_ingot', amount: 6 }, { resource: 'copper', amount: 10 }, { resource: 'mechanism', amount: 4 }, { resource: 'premium_planks', amount: 1 }] },
      { level: 8, buildSeconds: 30840, population: 18, health: 1678, cost: [{ resource: 'coins', amount: 675000 }, { resource: 'concrete', amount: 15 }, { resource: 'iron_ingot', amount: 9 }, { resource: 'copper_parts', amount: 4 }, { resource: 'mechanism', amount: 6 }, { resource: 'premium_planks', amount: 1 }] },
      { level: 9, buildSeconds: 38100, population: 20, health: 2003, cost: [{ resource: 'coins', amount: 893200 }, { resource: 'reinforced_concrete', amount: 12 }, { resource: 'copper_parts', amount: 7 }, { resource: 'explosives', amount: 11 }, { resource: 'mechanism', amount: 10 }, { resource: 'premium_planks', amount: 2 }] },
      { level: 10, buildSeconds: 46920, population: 22, health: 2287, cost: [{ resource: 'coins', amount: 1025000 }, { resource: 'reinforced_concrete', amount: 20 }, { resource: 'reinforced_beams', amount: 4 }, { resource: 'explosives', amount: 15 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'premium_planks', amount: 3 }] },
      { level: 11, buildSeconds: 61980, population: 25, health: 2562, cost: [{ resource: 'coins', amount: 1276000 }, { resource: 'reinforced_concrete', amount: 29 }, { resource: 'reinforced_beams', amount: 8 }, { resource: 'explosives', amount: 27 }, { resource: 'super_mechanism', amount: 2 }, { resource: 'light_crystal', amount: 1 }] },
      { level: 12, buildSeconds: 80640, population: 28, health: 3005, cost: [{ resource: 'coins', amount: 1570000 }, { resource: 'armor_plates', amount: 2 }, { resource: 'reinforced_beams', amount: 8 }, { resource: 'explosives', amount: 27 }, { resource: 'super_mechanism', amount: 2 }, { resource: 'light_crystal', amount: 1 }] },
    ],
  },
  {
    type: 'clay_quarry',
    category: 'industry',
    name: 'Глиняный карьер',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 420,
    population: 3,
    health: 95,
    cost: [{ resource: 'coins', amount: 2700 }, { resource: 'wood', amount: 18 }, { resource: 'planks', amount: 10 }, { resource: 'rope', amount: 6 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 420, population: 3, health: 95, cost: [{ resource: 'coins', amount: 2700 }, { resource: 'wood', amount: 18 }, { resource: 'planks', amount: 10 }, { resource: 'rope', amount: 6 }] },
      { level: 2, buildSeconds: 1110, population: 4, health: 220, cost: [{ resource: 'coins', amount: 16500 }, { resource: 'wood', amount: 42 }, { resource: 'planks', amount: 24 }, { resource: 'rope', amount: 8 }] },
      { level: 3, buildSeconds: 2600, population: 5, health: 360, cost: [{ resource: 'coins', amount: 43000 }, { resource: 'planks', amount: 64 }, { resource: 'stone', amount: 18 }, { resource: 'stone_block', amount: 6 }] },
      { level: 4, buildSeconds: 5880, population: 7, health: 530, cost: [{ resource: 'coins', amount: 96500 }, { resource: 'planks', amount: 92 }, { resource: 'stone_block', amount: 22 }, { resource: 'brick', amount: 16 }, { resource: 'rope', amount: 14 }] },
      { level: 5, buildSeconds: 11100, population: 9, health: 710, cost: [{ resource: 'coins', amount: 177000 }, { resource: 'brick', amount: 38 }, { resource: 'copper_parts', amount: 14 }, { resource: 'iron_ingot', amount: 4 }, { resource: 'planks', amount: 28 }] },
      { level: 6, buildSeconds: 17400, population: 11, health: 930, cost: [{ resource: 'coins', amount: 308000 }, { resource: 'brick', amount: 61 }, { resource: 'copper_parts', amount: 27 }, { resource: 'iron_ingot', amount: 8 }, { resource: 'mechanism', amount: 2 }] },
      { level: 7, buildSeconds: 24300, population: 13, health: 1190, cost: [{ resource: 'coins', amount: 514000 }, { resource: 'copper_parts', amount: 44 }, { resource: 'iron_ingot', amount: 13 }, { resource: 'mechanism', amount: 4 }, { resource: 'steel', amount: 2 }] },
      { level: 8, buildSeconds: 34500, population: 15, health: 1460, cost: [{ resource: 'coins', amount: 735000 }, { resource: 'mechanism', amount: 7 }, { resource: 'steel', amount: 8 }, { resource: 'reinforced_concrete', amount: 6 }, { resource: 'premium_planks', amount: 3 }] },
      { level: 9, buildSeconds: 46200, population: 17, health: 1740, cost: [{ resource: 'coins', amount: 982000 }, { resource: 'mechanism', amount: 10 }, { resource: 'steel', amount: 14 }, { resource: 'reinforced_concrete', amount: 10 }, { resource: 'blue_salt', amount: 4 }] },
      { level: 10, buildSeconds: 58800, population: 19, health: 2040, cost: [{ resource: 'coins', amount: 1280000 }, { resource: 'mechanism', amount: 16 }, { resource: 'reinforced_concrete', amount: 18 }, { resource: 'rune_tile', amount: 1 }, { resource: 'premium_planks', amount: 5 }] },
      { level: 11, buildSeconds: 76200, population: 21, health: 2380, cost: [{ resource: 'coins', amount: 1675000 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'reinforced_concrete', amount: 24 }, { resource: 'blue_salt', amount: 6 }, { resource: 'rune_tile', amount: 2 }] },
      { level: 12, buildSeconds: 100800, population: 24, health: 2780, cost: [{ resource: 'coins', amount: 2180000 }, { resource: 'super_mechanism', amount: 1 }, { resource: 'reinforced_concrete', amount: 32 }, { resource: 'gold_ingot', amount: 5 }, { resource: 'premium_planks', amount: 9 }] },
    ],
  },
  { type: 'iron_mine', category: 'industry', name: 'Железный рудник', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 420, population: 4, health: 160, cost: [{ resource: 'coins', amount: 900 }, { resource: 'planks', amount: 18 }, { resource: 'stone', amount: 20 }], firstLevel: true, upgradeTo: [] },
  { type: 'copper_mine', category: 'industry', name: 'Медный рудник', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 420, population: 4, health: 160, cost: [{ resource: 'coins', amount: 900 }, { resource: 'planks', amount: 18 }, { resource: 'stone', amount: 20 }], firstLevel: true, upgradeTo: [] },
  { type: 'resin_kiln', category: 'industry', name: 'Смолокурня', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 240, population: 3, health: 110, cost: [{ resource: 'coins', amount: 620 }, { resource: 'wood', amount: 45 }, { resource: 'stone', amount: 8 }], firstLevel: true, upgradeTo: [] },
  { type: 'sulfur_spring', category: 'industry', name: 'Серный источник', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 360, population: 3, health: 130, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'stone', amount: 35 }], firstLevel: true, upgradeTo: [] },
  { type: 'oil_well', category: 'industry', name: 'Нефтяная вышка', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 600, population: 5, health: 220, cost: [{ resource: 'coins', amount: 1100 }, { resource: 'metal', amount: 20 }, { resource: 'planks', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'stone_cutters', category: 'industry', name: 'Каменотесы', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 160, population: 3, cost: [{ resource: 'coins', amount: 140 }, { resource: 'wood', amount: 60 }], firstLevel: true, upgradeTo: [] },
  { type: 'tile_factory', category: 'industry', name: 'Черепичный завод', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 360, population: 4, cost: [{ resource: 'coins', amount: 900 }, { resource: 'clay', amount: 80 }, { resource: 'coal', amount: 25 }], firstLevel: true, upgradeTo: [] },
  { type: 'cement_workshop', category: 'industry', name: 'Цементный цех', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 420, population: 4, cost: [{ resource: 'coins', amount: 1100 }, { resource: 'stone', amount: 70 }, { resource: 'clay', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'concrete_plant', category: 'industry', name: 'Бетонный завод', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 540, population: 5, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'cement', amount: 20 }, { resource: 'sand', amount: 50 }], firstLevel: true, upgradeTo: [] },
  {
    type: 'rope_yard',
    category: 'industry',
    name: 'Канатный двор',
    level: 1,
    footprint: { width: 1, height: 1 },
    buildSeconds: 720,
    population: 3,
    health: 170,
    cost: [{ resource: 'coins', amount: 7000 }, { resource: 'wood', amount: 75 }, { resource: 'planks', amount: 30 }, { resource: 'windleaf', amount: 15 }],
    firstLevel: true,
    upgradeTo: [],
    upgradeLevels: [
      { level: 1, buildSeconds: 720, population: 3, health: 170, cost: [{ resource: 'coins', amount: 7000 }, { resource: 'wood', amount: 75 }, { resource: 'planks', amount: 30 }, { resource: 'windleaf', amount: 15 }] },
      { level: 2, buildSeconds: 2040, population: 4, health: 285, cost: [{ resource: 'coins', amount: 24500 }, { resource: 'wood', amount: 120 }, { resource: 'planks', amount: 48 }, { resource: 'flax', amount: 30 }] },
      { level: 3, buildSeconds: 4680, population: 5, health: 430, cost: [{ resource: 'coins', amount: 69000 }, { resource: 'planks', amount: 84 }, { resource: 'flax', amount: 65 }, { resource: 'stone', amount: 18 }, { resource: 'rope', amount: 6 }] },
      { level: 4, buildSeconds: 9300, population: 6, health: 610, cost: [{ resource: 'coins', amount: 148000 }, { resource: 'planks', amount: 120 }, { resource: 'flax', amount: 120 }, { resource: 'stone_block', amount: 30 }, { resource: 'rope', amount: 18 }] },
      { level: 5, buildSeconds: 17100, population: 7, health: 850, cost: [{ resource: 'coins', amount: 295000 }, { resource: 'stone_block', amount: 60 }, { resource: 'rope', amount: 42 }, { resource: 'fabric', amount: 30 }, { resource: 'iron_ingot', amount: 4 }] },
      { level: 6, buildSeconds: 25800, population: 9, health: 1130, cost: [{ resource: 'coins', amount: 520000 }, { resource: 'premium_planks', amount: 2 }, { resource: 'stone_block', amount: 88 }, { resource: 'fabric', amount: 68 }, { resource: 'iron_ingot', amount: 8 }, { resource: 'mechanism', amount: 3 }] },
      { level: 7, buildSeconds: 37200, population: 11, health: 1480, cost: [{ resource: 'coins', amount: 820000 }, { resource: 'premium_planks', amount: 4 }, { resource: 'stone_block', amount: 120 }, { resource: 'fabric', amount: 105 }, { resource: 'iron_ingot', amount: 14 }, { resource: 'mechanism', amount: 6 }, { resource: 'copper_parts', amount: 2 }] },
      { level: 8, buildSeconds: 50400, population: 13, health: 1880, cost: [{ resource: 'coins', amount: 1200000 }, { resource: 'premium_planks', amount: 7 }, { resource: 'stone_block', amount: 160 }, { resource: 'fabric', amount: 150 }, { resource: 'iron_ingot', amount: 22 }, { resource: 'mechanism', amount: 10 }, { resource: 'copper_parts', amount: 5 }, { resource: 'gold_ingot', amount: 1 }] }
    ],
  },
  { type: 'paper_workshop', category: 'industry', name: 'Бумажная мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 300, population: 3, cost: [{ resource: 'coins', amount: 680 }, { resource: 'wood', amount: 35 }, { resource: 'stone', amount: 8 }], firstLevel: true, upgradeTo: [] },
  { type: 'paint_workshop', category: 'industry', name: 'Красильная мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 360, population: 3, cost: [{ resource: 'coins', amount: 820 }, { resource: 'herbs', amount: 12 }, { resource: 'oil', amount: 4 }], firstLevel: true, upgradeTo: [] },
  { type: 'oil_press', category: 'industry', name: 'Маслобойня', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 360, population: 3, cost: [{ resource: 'coins', amount: 780 }, { resource: 'wood', amount: 30 }, { resource: 'stone', amount: 20 }], firstLevel: true, upgradeTo: [] },
  { type: 'foundry', category: 'industry', name: 'Литейная', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 540, population: 5, cost: [{ resource: 'coins', amount: 1000 }, { resource: 'iron_ore', amount: 30 }, { resource: 'coal', amount: 25 }], firstLevel: true, upgradeTo: [] },
  { type: 'steelworks', category: 'industry', name: 'Сталеплавильный завод', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 720, population: 6, cost: [{ resource: 'coins', amount: 1150 }, { resource: 'iron', amount: 25 }, { resource: 'coal', amount: 35 }], firstLevel: true, upgradeTo: [] },
  { type: 'electronics_workshop', category: 'industry', name: 'Электронная мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 840, population: 5, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'electronics', amount: 1 }, { resource: 'glass', amount: 24 }], firstLevel: true, upgradeTo: [] },
  { type: 'oil_refinery', category: 'industry', name: 'Нефтеперерабатывающий завод', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 270, population: 4, cost: [{ resource: 'brick', amount: 80 }, { resource: 'metal', amount: 30 }], firstLevel: true, upgradeTo: [] },
  { type: 'chemical_workshop', category: 'industry', name: 'Химическая мастерская', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 600, population: 5, cost: [{ resource: 'coins', amount: 1000 }, { resource: 'sulfur', amount: 6 }, { resource: 'glass', amount: 12 }], firstLevel: true, upgradeTo: [] },
  { type: 'military_factory', category: 'industry', name: 'Военный завод', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 900, population: 7, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'steel', amount: 10 }, { resource: 'fuel', amount: 8 }], firstLevel: true, upgradeTo: [] },
  { type: 'precision_workshop', category: 'industry', name: 'Завод точной механики', level: 1, footprint: { width: 1, height: 1 }, buildSeconds: 960, population: 7, cost: [{ resource: 'coins', amount: 1200 }, { resource: 'electronics', amount: 2 }, { resource: 'glass', amount: 12 }], firstLevel: true, upgradeTo: [] },
]
