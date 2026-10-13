export type MonsterType =
  | 'roaming_melee'
  | 'resource_guardian'
  | 'ruins_guardian'
  | 'forest_stalker'
  | 'spore_beast'
  | 'ironback_brute'
  | 'ember_wisp'
  | 'ancient_colossus'

export type MonsterSpec = {
  type: MonsterType
  name: string
  maxHealth: number
  damage: number
  speedTiles: number
  aggroRadius: number
  attackRange: number
  lootCoins: number
  spawnWeight: number
}

export const monsterCatalog: MonsterSpec[] = [
  { type: 'roaming_melee', name: 'Бродячий налетчик', maxHealth: 180, damage: 18, speedTiles: 1, aggroRadius: 5, attackRange: 1, lootCoins: 65, spawnWeight: 24 },
  { type: 'resource_guardian', name: 'Страж залежи', maxHealth: 280, damage: 26, speedTiles: 1, aggroRadius: 4, attackRange: 1, lootCoins: 120, spawnWeight: 18 },
  { type: 'ruins_guardian', name: 'Сторож руин', maxHealth: 420, damage: 38, speedTiles: 1, aggroRadius: 6, attackRange: 1, lootCoins: 220, spawnWeight: 10 },
  { type: 'forest_stalker', name: 'Лесной следопыт', maxHealth: 150, damage: 14, speedTiles: 2, aggroRadius: 6, attackRange: 1, lootCoins: 55, spawnWeight: 28 },
  { type: 'spore_beast', name: 'Споровый зверь', maxHealth: 320, damage: 22, speedTiles: 1, aggroRadius: 4, attackRange: 1, lootCoins: 130, spawnWeight: 20 },
  { type: 'ironback_brute', name: 'Железоспин', maxHealth: 620, damage: 44, speedTiles: 1, aggroRadius: 5, attackRange: 1, lootCoins: 320, spawnWeight: 8 },
  { type: 'ember_wisp', name: 'Тлеющий огонек', maxHealth: 240, damage: 16, speedTiles: 1, aggroRadius: 7, attackRange: 3, lootCoins: 180, spawnWeight: 12 },
  { type: 'ancient_colossus', name: 'Древний колосс', maxHealth: 2400, damage: 120, speedTiles: 1, aggroRadius: 8, attackRange: 1, lootCoins: 2200, spawnWeight: 1 },
]
