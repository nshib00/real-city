import { playUiSound } from '../../audio/playUiSound'
import type { SoundId } from '../../audio/soundEvents'
import type { InventoryResponse } from '../../shared/api/economy'
import { resourceCatalog } from '../../../../shared/catalog/resources'

const rareResources = new Set(resourceCatalog.filter((item) => item.category === 'rare').map((item) => item.id))

/** Используется только для ответа конкретной mutation, не для фонового обновления инвентаря. */
export function playConfirmedCoinChange(before: InventoryResponse | undefined, after: InventoryResponse | undefined): void {
  if (!before || !after) return
  const amount = (items: InventoryResponse['items']) => items.find((item) => item.resource === 'coins')?.amount ?? 0
  const delta = amount(after.items) - amount(before.items)
  if (delta > 0) playUiSound('economy.coin.earned')
  if (delta < 0) playUiSound('economy.coin.spent')
}

export function playConfirmedRareReward(before: InventoryResponse | undefined, after: InventoryResponse | undefined): void {
  if (!before || !after) return
  const previous = new Map(before.items.map((item) => [item.resource, item.amount]))
  if (after.items.some((item) => rareResources.has(item.resource) && item.amount > (previous.get(item.resource) ?? 0))) playUiSound('economy.reward.rare')
}

export function fieldHarvestSound(buildingType: string): SoundId {
  if (buildingType === 'mushroom_grove') return 'economy.harvest.mushroom'
  if (buildingType === 'sugar_bed') return 'economy.harvest.cane'
  if (buildingType === 'crystal_greenhouse') return 'economy.harvest.crystal'
  return 'economy.harvest.field'
}

export function resourceGatherSound(resource: string): SoundId {
  const sounds: Record<string, SoundId> = {
    wood: 'economy.gather.wood', stone: 'economy.gather.stone', iron_ore: 'economy.gather.ore', copper: 'economy.gather.ore', coal: 'economy.gather.ore',
    clay: 'economy.gather.clay', sand: 'economy.gather.sand', oil: 'economy.gather.oil', resin: 'economy.gather.resin',
    'aeolian-crystal': 'economy.gather.crystal', light_crystal: 'economy.gather.crystal', crystal: 'economy.gather.crystal',
  }
  return sounds[resource] ?? 'economy.gather.rare'
}

/** Порядок вариантов в production.json: дерево, камень, металл, ткань, химия. */
export function productionMaterialVariant(buildingType: string | undefined): number {
  if (!buildingType) return 0
  if (['stone_cutters', 'brick_kiln', 'glass_workshop', 'sand_quarry', 'clay_quarry'].includes(buildingType)) return 1
  if (['forge', 'mint', 'iron_mine', 'mine', 'precision_workshop', 'optical_workshop'].includes(buildingType)) return 2
  if (['rope_yard', 'dye_works', 'weaving_yard', 'paper_workshop'].includes(buildingType)) return 3
  if (['chemical_workshop', 'oil_well', 'refinery'].includes(buildingType)) return 4
  return 0
}
