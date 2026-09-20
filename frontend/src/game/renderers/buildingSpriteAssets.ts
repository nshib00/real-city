import type { PlacedBuilding } from '../state/useGameStore'
import { dugoutModelLevel, dugoutModelState } from './dugout'
import { lumberYardModelLevel, lumberYardModelState } from './lumberYard'
import { townHallModelLevel, townHallModelState } from './townHall'
import { windleafBedModelLevel, windleafBedModelState } from './windleafBed'
import { woodHouseModelLevel, woodHouseModelState } from './woodHouse'

type SpriteState = 'active' | 'construction' | 'damaged' | 'ruined' | `stage${'01' | '02' | '03' | '04'}` | `super_stage${'01' | '02' | '03' | '04' | '05' | '06'}`

export function buildingSpriteAsset(building: PlacedBuilding) {
  if (building.kind === 'town_hall') {
    return spriteUrl('center/town_hall', 'town_hall', townHallModelLevel(building.level), townHallModelState(building))
  }
  if (building.kind === 'dugout') {
    return spriteUrl('housing/dugout', 'dugout', dugoutModelLevel(building.level), dugoutModelState(building))
  }
  if (building.kind === 'wood_house') {
    return spriteUrl('housing/wood_house', 'wood_house', woodHouseModelLevel(building.level), woodHouseModelState(building))
  }
  if (building.kind === 'lumber_yard') {
    return spriteUrl('industry/lumber_yard', 'lumber_yard', lumberYardModelLevel(building.level), lumberYardModelState(building))
  }
  if (building.kind === 'field_bed') {
    return spriteUrl('fields/windleaf_bed', 'windleaf_bed', windleafBedModelLevel(building.level), windleafBedModelState(building))
  }
  return null
}

function spriteUrl(folder: string, name: string, level: number, state: SpriteState) {
  const spriteState = state === 'ruined' ? 'damaged' : state
  return `/assets/buildings/${folder}/${name}_l${String(level).padStart(2, '0')}_${spriteState}.png`
}
