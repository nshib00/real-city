export type FieldGrowthStage = {
  index: number
  label: string
  ready: boolean
}

export const windleafGrowthStages: FieldGrowthStage[] = [
  { index: 1, label: 'посадка', ready: false },
  { index: 2, label: 'ранний рост', ready: false },
  { index: 3, label: 'средний рост', ready: false },
  { index: 4, label: 'поздний рост', ready: false },
  { index: 5, label: 'готовый урожай', ready: true },
]

export function isSuperCropRoll(roll: number, chance = 0.0075) {
  return roll >= 0 && roll < chance
}

