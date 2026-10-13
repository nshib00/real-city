export type FieldGrowthStage = {
  index: number
  label: string
  ready: boolean
}

export const windleafGrowthStages: FieldGrowthStage[] = [
  { index: 1, label: 'маленькие зеленые росточки', ready: false },
  { index: 2, label: 'небольшие листья', ready: false },
  { index: 3, label: 'крупные листья с жилками', ready: false },
  { index: 4, label: 'готовые высокие листья', ready: true },
]

export function isSuperCropRoll(roll: number, chance = 0.0075) {
  return roll >= 0 && roll < chance
}

export type FieldCropRuntimeSpec = {
  type: string
  stages: number
  superStages: number
  workersByLevel: number[]
  rewardsByLevel: { coins: number; rewards: { resource: string; amount: number }[]; superCoins?: number; superRewards?: { resource: string; amount: number }[] }[]
}

function fieldSpec(input: { type: string; stages?: number; superStages?: number; workers: number[]; resource: string; coins: number[]; amounts: number[]; chances?: number[]; superResource?: string; superAmounts?: number[] }): FieldCropRuntimeSpec {
  const chances = input.chances ?? []
  const superAmounts = input.superAmounts ?? []
  return {
    type: input.type,
    stages: input.stages ?? 4,
    superStages: input.superStages ?? 6,
    workersByLevel: input.workers,
    rewardsByLevel: input.coins.map((coins, index) => {
      const reward = { coins, rewards: [{ resource: input.resource, amount: input.amounts[index] }] }
      if ((chances[index] ?? 0) <= 0 || !input.superResource || (superAmounts[index] ?? 0) <= 0) {
        return reward
      }
      return {
        ...reward,
        superCoins: coins * 4,
        superRewards: [
          { resource: input.resource, amount: input.amounts[index] * 3 },
          { resource: input.superResource, amount: superAmounts[index] },
        ],
      }
    }),
  }
}

export const fieldCropRuntimeSpecs: Record<string, FieldCropRuntimeSpec> = {
  field_bed: {
    type: 'field_bed',
    stages: 4,
    superStages: 6,
    workersByLevel: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    rewardsByLevel: [
      { coins: 190, rewards: [{ resource: 'windleaf', amount: 1 }] },
      { coins: 900, rewards: [{ resource: 'windleaf', amount: 1 }] },
      { coins: 2400, rewards: [{ resource: 'windleaf', amount: 2 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 8300, rewards: [{ resource: 'windleaf', amount: 2 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 15000, rewards: [{ resource: 'windleaf', amount: 3 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 23000, rewards: [{ resource: 'windleaf', amount: 4 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 34000, rewards: [{ resource: 'windleaf', amount: 5 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 48500, rewards: [{ resource: 'windleaf', amount: 6 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 59000, rewards: [{ resource: 'windleaf', amount: 7 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 72000, rewards: [{ resource: 'windleaf', amount: 9 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
      { coins: 86000, rewards: [{ resource: 'windleaf', amount: 11 }], superRewards: [{ resource: 'super-windleaf', amount: 1 }] },
    ],
  },
  seed_garden: {
    type: 'seed_garden',
    stages: 3,
    superStages: 6,
    workersByLevel: [2, 3, 4, 5, 6, 7, 8, 9, 10, 12],
    rewardsByLevel: [
      { coins: 50, rewards: [{ resource: 'seeds', amount: 5 }] },
      { coins: 280, rewards: [{ resource: 'seeds', amount: 10 }] },
      { coins: 760, rewards: [{ resource: 'seeds', amount: 14 }], superCoins: 8500, superRewards: [{ resource: 'seeds', amount: 25 }, { resource: 'super-seeds', amount: 1 }] },
      { coins: 1500, rewards: [{ resource: 'seeds', amount: 18 }], superCoins: 16500, superRewards: [{ resource: 'seeds', amount: 36 }, { resource: 'super-seeds', amount: 1 }] },
      { coins: 2600, rewards: [{ resource: 'seeds', amount: 23 }], superCoins: 28600, superRewards: [{ resource: 'seeds', amount: 46 }, { resource: 'super-seeds', amount: 1 }] },
      { coins: 4100, rewards: [{ resource: 'seeds', amount: 29 }], superCoins: 45100, superRewards: [{ resource: 'seeds', amount: 58 }, { resource: 'super-seeds', amount: 1 }] },
      { coins: 6300, rewards: [{ resource: 'seeds', amount: 36 }], superCoins: 69300, superRewards: [{ resource: 'seeds', amount: 72 }, { resource: 'super-seeds', amount: 1 }] },
      { coins: 9300, rewards: [{ resource: 'seeds', amount: 45 }], superCoins: 102300, superRewards: [{ resource: 'seeds', amount: 90 }, { resource: 'super-seeds', amount: 2 }] },
      { coins: 13200, rewards: [{ resource: 'seeds', amount: 56 }], superCoins: 145200, superRewards: [{ resource: 'seeds', amount: 112 }, { resource: 'super-seeds', amount: 2 }] },
      { coins: 18000, rewards: [{ resource: 'seeds', amount: 70 }], superCoins: 198000, superRewards: [{ resource: 'seeds', amount: 140 }, { resource: 'super-seeds', amount: 2 }] },
    ],
  },
  flax_field: {
    type: 'flax_field',
    stages: 3,
    superStages: 6,
    workersByLevel: [2, 3, 3, 3, 4, 5, 6, 7, 8, 10],
    rewardsByLevel: [
      { coins: 100, rewards: [{ resource: 'flax', amount: 7 }] },
      { coins: 340, rewards: [{ resource: 'flax', amount: 12 }] },
      { coins: 860, rewards: [{ resource: 'flax', amount: 18 }], superCoins: 3450, superRewards: [{ resource: 'flax', amount: 42 }, { resource: 'super-fiber', amount: 1 }] },
      { coins: 1450, rewards: [{ resource: 'flax', amount: 26 }], superCoins: 5800, superRewards: [{ resource: 'flax', amount: 62 }, { resource: 'super-fiber', amount: 1 }] },
      { coins: 2250, rewards: [{ resource: 'flax', amount: 36 }], superCoins: 9000, superRewards: [{ resource: 'flax', amount: 84 }, { resource: 'super-fiber', amount: 1 }] },
      { coins: 3350, rewards: [{ resource: 'flax', amount: 49 }], superCoins: 13400, superRewards: [{ resource: 'flax', amount: 115 }, { resource: 'super-fiber', amount: 1 }] },
      { coins: 4900, rewards: [{ resource: 'flax', amount: 65 }], superCoins: 19600, superRewards: [{ resource: 'flax', amount: 152 }, { resource: 'super-fiber', amount: 1 }] },
      { coins: 7000, rewards: [{ resource: 'flax', amount: 84 }], superCoins: 28000, superRewards: [{ resource: 'flax', amount: 196 }, { resource: 'super-fiber', amount: 2 }] },
      { coins: 9600, rewards: [{ resource: 'flax', amount: 106 }], superCoins: 38400, superRewards: [{ resource: 'flax', amount: 248 }, { resource: 'super-fiber', amount: 2 }] },
      { coins: 12800, rewards: [{ resource: 'flax', amount: 132 }], superCoins: 51200, superRewards: [{ resource: 'flax', amount: 310 }, { resource: 'super-fiber', amount: 2 }] },
    ],
  },
  herb_bed: fieldSpec({
    type: 'herb_bed',
    workers: [1, 1, 1, 1, 1, 1, 1, 1, 1],
    resource: 'herbs',
    coins: [1200, 2200, 3600, 5600, 8200, 11600, 15800, 21000, 27500],
    amounts: [8, 12, 17, 23, 30, 38, 48, 60, 75],
    chances: [0, 0, 20, 25, 32, 40, 50, 62, 75],
    superResource: 'rare_flowers',
    superAmounts: [0, 0, 1, 1, 1, 1, 2, 2, 3],
  }),
  mushroom_grove: fieldSpec({
    type: 'mushroom_grove',
    workers: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    resource: 'mushrooms',
    coins: [650, 1300, 2300, 3900, 6200, 9300, 13200, 18500, 25200, 34000],
    amounts: [6, 10, 15, 21, 29, 38, 49, 62, 78, 96],
    chances: [0, 0, 18, 22, 28, 35, 45, 58, 72, 90],
    superResource: 'super-mushrooms',
    superAmounts: [0, 0, 1, 1, 1, 1, 2, 2, 2, 3],
  }),
  reed_bed: fieldSpec({
    type: 'reed_bed',
    workers: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    resource: 'reed',
    coins: [420, 820, 1500, 2600, 4300, 6800, 10200, 14800, 21000, 29200],
    amounts: [7, 11, 16, 23, 31, 41, 53, 67, 84, 104],
    chances: [0, 0, 15, 20, 26, 34, 44, 56, 70, 85],
    superResource: 'super-fiber',
    superAmounts: [0, 0, 1, 1, 1, 1, 1, 2, 2, 2],
  }),
  dye_garden: fieldSpec({
    type: 'dye_garden',
    workers: [1, 1, 1, 1, 1, 1],
    resource: 'dyes',
    coins: [18500, 31000, 49000, 73500, 106000, 150000],
    amounts: [18, 28, 42, 60, 82, 110],
    chances: [35, 45, 58, 72, 88, 105],
    superResource: 'rare_flowers',
    superAmounts: [1, 1, 2, 2, 3, 4],
  }),
  oilseed_field: fieldSpec({
    type: 'oilseed_field',
    workers: [1, 1, 1, 1, 1, 1, 1],
    resource: 'oil_plants',
    coins: [7600, 12200, 18800, 27800, 39800, 55500, 76000],
    amounts: [14, 22, 33, 47, 64, 86, 112],
    chances: [20, 28, 38, 50, 64, 80, 100],
    superResource: 'super-seeds',
    superAmounts: [1, 1, 1, 1, 2, 2, 3],
  }),
  sugar_bed: fieldSpec({
    type: 'sugar_bed',
    workers: [1, 1, 1, 1, 1, 1, 1, 1, 1],
    resource: 'sugar_cane',
    coins: [4200, 7200, 11800, 18000, 26500, 38000, 53000, 72000, 96000],
    amounts: [10, 16, 24, 34, 47, 63, 82, 105, 132],
    chances: [0, 0, 18, 24, 32, 42, 54, 68, 85],
    superResource: 'super-seeds',
    superAmounts: [0, 0, 1, 1, 1, 1, 2, 2, 3],
  }),
  crystal_greenhouse: fieldSpec({
    type: 'crystal_greenhouse',
    workers: [4, 4, 4, 4],
    resource: 'crystal_fruit',
    coins: [85000, 140000, 215000, 320000],
    amounts: [3, 5, 8, 12],
    chances: [45, 65, 85, 110],
    superResource: 'aeolian-crystal',
    superAmounts: [1, 1, 1, 2],
  }),
}

export function fieldCropSpec(type: string) {
  return fieldCropRuntimeSpecs[type] ?? null
}
