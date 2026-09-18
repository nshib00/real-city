export type MonsterType = 'roaming_melee' | 'resource_guardian' | 'ruins_guardian'

export type MonsterSpec = {
  type: MonsterType
  name: string
  maxHealth: number
  damage: number
  speedTiles: number
  aggroRadius: number
  lootCoins: number
}

export const monsterCatalog: MonsterSpec[] = [
  { type: 'roaming_melee', name: 'Бродячий налетчик', maxHealth: 90, damage: 8, speedTiles: 1, aggroRadius: 5, lootCoins: 18 },
  { type: 'resource_guardian', name: 'Страж залежи', maxHealth: 140, damage: 12, speedTiles: 1, aggroRadius: 4, lootCoins: 34 },
  { type: 'ruins_guardian', name: 'Сторож руин', maxHealth: 210, damage: 18, speedTiles: 1, aggroRadius: 6, lootCoins: 58 },
]
