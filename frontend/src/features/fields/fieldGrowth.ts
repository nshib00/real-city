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
