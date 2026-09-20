import type { PlacedBuilding } from '../state/useGameStore'
import { dugoutModelLevel, dugoutModelState } from './dugout'
import { lumberYardModelLevel, lumberYardModelState } from './lumberYard'
import { townHallModelLevel, townHallModelState } from './townHall'
import { windleafBedModelLevel, windleafBedModelState } from './windleafBed'
import { woodHouseModelLevel, woodHouseModelState } from './woodHouse'

import townHallL01Active from '../../assets/buildings/center/town_hall/town_hall_l01_active.glb?url'
import townHallL01Construction from '../../assets/buildings/center/town_hall/town_hall_l01_construction.glb?url'
import townHallL01Damaged from '../../assets/buildings/center/town_hall/town_hall_l01_damaged.glb?url'
import townHallL02Active from '../../assets/buildings/center/town_hall/town_hall_l02_active.glb?url'
import townHallL02Construction from '../../assets/buildings/center/town_hall/town_hall_l02_construction.glb?url'
import townHallL02Damaged from '../../assets/buildings/center/town_hall/town_hall_l02_damaged.glb?url'
import townHallL03Active from '../../assets/buildings/center/town_hall/town_hall_l03_active.glb?url'
import townHallL03Construction from '../../assets/buildings/center/town_hall/town_hall_l03_construction.glb?url'
import townHallL03Damaged from '../../assets/buildings/center/town_hall/town_hall_l03_damaged.glb?url'
import townHallL04Active from '../../assets/buildings/center/town_hall/town_hall_l04_active.glb?url'
import townHallL04Construction from '../../assets/buildings/center/town_hall/town_hall_l04_construction.glb?url'
import townHallL04Damaged from '../../assets/buildings/center/town_hall/town_hall_l04_damaged.glb?url'
import townHallL05Active from '../../assets/buildings/center/town_hall/town_hall_l05_active.glb?url'
import townHallL05Construction from '../../assets/buildings/center/town_hall/town_hall_l05_construction.glb?url'
import townHallL05Damaged from '../../assets/buildings/center/town_hall/town_hall_l05_damaged.glb?url'
import townHallL06Active from '../../assets/buildings/center/town_hall/town_hall_l06_active.glb?url'
import townHallL06Construction from '../../assets/buildings/center/town_hall/town_hall_l06_construction.glb?url'
import townHallL06Damaged from '../../assets/buildings/center/town_hall/town_hall_l06_damaged.glb?url'
import townHallL07Active from '../../assets/buildings/center/town_hall/town_hall_l07_active.glb?url'
import townHallL07Construction from '../../assets/buildings/center/town_hall/town_hall_l07_construction.glb?url'
import townHallL07Damaged from '../../assets/buildings/center/town_hall/town_hall_l07_damaged.glb?url'
import townHallL08Active from '../../assets/buildings/center/town_hall/town_hall_l08_active.glb?url'
import townHallL08Construction from '../../assets/buildings/center/town_hall/town_hall_l08_construction.glb?url'
import townHallL08Damaged from '../../assets/buildings/center/town_hall/town_hall_l08_damaged.glb?url'
import townHallL09Active from '../../assets/buildings/center/town_hall/town_hall_l09_active.glb?url'
import townHallL09Construction from '../../assets/buildings/center/town_hall/town_hall_l09_construction.glb?url'
import townHallL09Damaged from '../../assets/buildings/center/town_hall/town_hall_l09_damaged.glb?url'
import townHallL10Active from '../../assets/buildings/center/town_hall/town_hall_l10_active.glb?url'
import townHallL10Construction from '../../assets/buildings/center/town_hall/town_hall_l10_construction.glb?url'
import townHallL10Damaged from '../../assets/buildings/center/town_hall/town_hall_l10_damaged.glb?url'
import dugoutL01Active from '../../assets/buildings/housing/dugout/dugout_l01_active.glb?url'
import dugoutL01Construction from '../../assets/buildings/housing/dugout/dugout_l01_construction.glb?url'
import dugoutL01Damaged from '../../assets/buildings/housing/dugout/dugout_l01_damaged.glb?url'
import dugoutL02Active from '../../assets/buildings/housing/dugout/dugout_l02_active.glb?url'
import dugoutL02Construction from '../../assets/buildings/housing/dugout/dugout_l02_construction.glb?url'
import dugoutL02Damaged from '../../assets/buildings/housing/dugout/dugout_l02_damaged.glb?url'
import dugoutL03Active from '../../assets/buildings/housing/dugout/dugout_l03_active.glb?url'
import dugoutL03Construction from '../../assets/buildings/housing/dugout/dugout_l03_construction.glb?url'
import dugoutL03Damaged from '../../assets/buildings/housing/dugout/dugout_l03_damaged.glb?url'
import dugoutL04Active from '../../assets/buildings/housing/dugout/dugout_l04_active.glb?url'
import dugoutL04Construction from '../../assets/buildings/housing/dugout/dugout_l04_construction.glb?url'
import dugoutL04Damaged from '../../assets/buildings/housing/dugout/dugout_l04_damaged.glb?url'
import dugoutL05Active from '../../assets/buildings/housing/dugout/dugout_l05_active.glb?url'
import dugoutL05Construction from '../../assets/buildings/housing/dugout/dugout_l05_construction.glb?url'
import dugoutL05Damaged from '../../assets/buildings/housing/dugout/dugout_l05_damaged.glb?url'
import woodHouseL01Active from '../../assets/buildings/housing/wood_house/wood_house_l01_active.glb?url'
import woodHouseL01Construction from '../../assets/buildings/housing/wood_house/wood_house_l01_construction.glb?url'
import woodHouseL01Damaged from '../../assets/buildings/housing/wood_house/wood_house_l01_damaged.glb?url'
import woodHouseL02Active from '../../assets/buildings/housing/wood_house/wood_house_l02_active.glb?url'
import woodHouseL02Construction from '../../assets/buildings/housing/wood_house/wood_house_l02_construction.glb?url'
import woodHouseL02Damaged from '../../assets/buildings/housing/wood_house/wood_house_l02_damaged.glb?url'
import woodHouseL03Active from '../../assets/buildings/housing/wood_house/wood_house_l03_active.glb?url'
import woodHouseL03Construction from '../../assets/buildings/housing/wood_house/wood_house_l03_construction.glb?url'
import woodHouseL03Damaged from '../../assets/buildings/housing/wood_house/wood_house_l03_damaged.glb?url'
import woodHouseL04Active from '../../assets/buildings/housing/wood_house/wood_house_l04_active.glb?url'
import woodHouseL04Construction from '../../assets/buildings/housing/wood_house/wood_house_l04_construction.glb?url'
import woodHouseL04Damaged from '../../assets/buildings/housing/wood_house/wood_house_l04_damaged.glb?url'
import woodHouseL05Active from '../../assets/buildings/housing/wood_house/wood_house_l05_active.glb?url'
import woodHouseL05Construction from '../../assets/buildings/housing/wood_house/wood_house_l05_construction.glb?url'
import woodHouseL05Damaged from '../../assets/buildings/housing/wood_house/wood_house_l05_damaged.glb?url'
import woodHouseL06Active from '../../assets/buildings/housing/wood_house/wood_house_l06_active.glb?url'
import woodHouseL06Construction from '../../assets/buildings/housing/wood_house/wood_house_l06_construction.glb?url'
import woodHouseL06Damaged from '../../assets/buildings/housing/wood_house/wood_house_l06_damaged.glb?url'

type ModelState = 'active' | 'construction' | 'damaged' | 'ruined'

const townHallAssets = [
  { active: townHallL01Active, construction: townHallL01Construction, damaged: townHallL01Damaged, ruined: townHallL01Damaged },
  { active: townHallL02Active, construction: townHallL02Construction, damaged: townHallL02Damaged, ruined: townHallL02Damaged },
  { active: townHallL03Active, construction: townHallL03Construction, damaged: townHallL03Damaged, ruined: townHallL03Damaged },
  { active: townHallL04Active, construction: townHallL04Construction, damaged: townHallL04Damaged, ruined: townHallL04Damaged },
  { active: townHallL05Active, construction: townHallL05Construction, damaged: townHallL05Damaged, ruined: townHallL05Damaged },
  { active: townHallL06Active, construction: townHallL06Construction, damaged: townHallL06Damaged, ruined: townHallL06Damaged },
  { active: townHallL07Active, construction: townHallL07Construction, damaged: townHallL07Damaged, ruined: townHallL07Damaged },
  { active: townHallL08Active, construction: townHallL08Construction, damaged: townHallL08Damaged, ruined: townHallL08Damaged },
  { active: townHallL09Active, construction: townHallL09Construction, damaged: townHallL09Damaged, ruined: townHallL09Damaged },
  { active: townHallL10Active, construction: townHallL10Construction, damaged: townHallL10Damaged, ruined: townHallL10Damaged },
] satisfies Record<ModelState, string>[]

const dugoutAssets = [
  { active: dugoutL01Active, construction: dugoutL01Construction, damaged: dugoutL01Damaged, ruined: dugoutL01Damaged },
  { active: dugoutL02Active, construction: dugoutL02Construction, damaged: dugoutL02Damaged, ruined: dugoutL02Damaged },
  { active: dugoutL03Active, construction: dugoutL03Construction, damaged: dugoutL03Damaged, ruined: dugoutL03Damaged },
  { active: dugoutL04Active, construction: dugoutL04Construction, damaged: dugoutL04Damaged, ruined: dugoutL04Damaged },
  { active: dugoutL05Active, construction: dugoutL05Construction, damaged: dugoutL05Damaged, ruined: dugoutL05Damaged },
] satisfies Record<ModelState, string>[]

const woodHouseAssets = [
  { active: woodHouseL01Active, construction: woodHouseL01Construction, damaged: woodHouseL01Damaged, ruined: woodHouseL01Damaged },
  { active: woodHouseL02Active, construction: woodHouseL02Construction, damaged: woodHouseL02Damaged, ruined: woodHouseL02Damaged },
  { active: woodHouseL03Active, construction: woodHouseL03Construction, damaged: woodHouseL03Damaged, ruined: woodHouseL03Damaged },
  { active: woodHouseL04Active, construction: woodHouseL04Construction, damaged: woodHouseL04Damaged, ruined: woodHouseL04Damaged },
  { active: woodHouseL05Active, construction: woodHouseL05Construction, damaged: woodHouseL05Damaged, ruined: woodHouseL05Damaged },
  { active: woodHouseL06Active, construction: woodHouseL06Construction, damaged: woodHouseL06Damaged, ruined: woodHouseL06Damaged },
] satisfies Record<ModelState, string>[]

export function buildingModelAsset(building: PlacedBuilding) {
  if (building.kind === 'town_hall') {
    return townHallAssets[townHallModelLevel(building.level) - 1][townHallModelState(building)]
  }
  if (building.kind === 'dugout') {
    return dugoutAssets[dugoutModelLevel(building.level) - 1][dugoutModelState(building)]
  }
  if (building.kind === 'wood_house') {
    return woodHouseAssets[woodHouseModelLevel(building.level) - 1][woodHouseModelState(building)]
  }
  if (building.kind === 'lumber_yard') {
    const level = lumberYardModelLevel(building.level)
    const state = lumberYardModelState(building)
    const modelState = state === 'ruined' ? 'damaged' : state
    return `/assets/buildings/industry/lumber_yard/lumber_yard_l${String(level).padStart(2, '0')}_${modelState}.glb`
  }
  if (building.kind === 'field_bed') {
    const level = windleafBedModelLevel(building.level)
    const modelState = windleafBedModelState(building)
    return `/assets/buildings/fields/windleaf_bed/windleaf_bed_l${String(level).padStart(2, '0')}_${modelState === 'ruined' ? 'damaged' : modelState}.glb`
  }
  return null
}
