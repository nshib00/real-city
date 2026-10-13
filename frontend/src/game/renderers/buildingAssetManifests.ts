import type { BuildingKind } from '../state/useGameStore'
import type { BuildingAnimationKey, RuntimeAssetManifest } from './assetManifestTypes'

export type BuildingAssetState =
  | 'active'
  | 'construction'
  | 'damaged'
  | 'ruined'
  | 'ready'
  | 'idle_no_input'
  | 'idle_no_workers'
  | `stage${'01' | '02' | '03' | '04'}`
  | `super_stage${'01' | '02' | '03' | '04' | '05' | '06'}`

export type BuildingAssetSource = 'public' | 'src-models'

export type BuildingAssetManifest = RuntimeAssetManifest & {
  kind: BuildingKind
  assetId: string
  category: string
  displayName: string
  levels: readonly number[]
  states: readonly BuildingAssetState[]
  spriteSource: BuildingAssetSource
  modelSource: BuildingAssetSource
  revision?: string
  shapeDefault?: string
  animations?: Partial<Record<BuildingAnimationKey, NonNullable<RuntimeAssetManifest['animations']>[string]>>
}

export const LUMBER_YARD_ASSET_REVISION = 'grass-ground-2026-09-22'
export const SAND_QUARRY_ASSET_REVISION = 'mcp-midpoly-l01-l11-2026-09-24'
export const CLAY_QUARRY_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-10-12'
export const MINE_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-09-28'
export const GLASS_WORKSHOP_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-09-29'
export const COIN_STORAGE_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-09-29-rework2'
export const SEED_GARDEN_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-09'
export const HERB_BED_ASSET_REVISION = 'mcp-midpoly-l01-l09-2026-10-09'
export const MUSHROOM_GROVE_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-10'
export const FLAX_FIELD_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-08'
export const REED_BED_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-09'
export const OILSEED_FIELD_ASSET_REVISION = 'mcp-midpoly-l01-l07-2026-10-09'
export const ROPE_YARD_ASSET_REVISION = 'mcp-midpoly-l01-l08-2026-10-08'
export const OIL_WELL_ASSET_REVISION = 'runtime-l01-l03-2026-10-13'

const l1To3 = [1, 2, 3] as const
const l1To5 = [1, 2, 3, 4, 5] as const
const l1To6 = [1, 2, 3, 4, 5, 6] as const
const l1To7 = [1, 2, 3, 4, 5, 6, 7] as const
const l1To8 = [1, 2, 3, 4, 5, 6, 7, 8] as const
const l1To10 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const
const l1To11 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] as const
const l1To12 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] as const
const l1To13 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13] as const
const coreStates = ['active', 'construction', 'damaged'] as const
const coreWithRuinedStates = ['active', 'construction', 'damaged', 'ruined'] as const

export const buildingAssetManifests: readonly BuildingAssetManifest[] = [
  {
    kind: 'town_hall',
    assetId: 'town_hall',
    category: 'center',
    displayName: 'Центр города',
    levels: l1To10,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'src-models',
  },
  {
    kind: 'dugout',
    assetId: 'dugout',
    category: 'housing',
    displayName: 'Землянка',
    levels: l1To5,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'src-models',
  },
  {
    kind: 'wood_house',
    assetId: 'wood_house',
    category: 'housing',
    displayName: 'Деревянный дом',
    levels: l1To6,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'src-models',
  },
  {
    kind: 'field_bed',
    assetId: 'windleaf_bed',
    category: 'fields',
    displayName: 'Грядка ветролиста',
    levels: l1To10,
    states: [
      'active',
      'construction',
      'damaged',
      'stage01',
      'stage02',
      'stage03',
      'stage04',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
  },
  {
    kind: 'seed_garden',
    assetId: 'seed_garden',
    category: 'fields',
    displayName: 'Семенной огород',
    levels: l1To10,
    states: [
      'active',
      'construction',
      'damaged',
      'ruined',
      'stage01',
      'stage02',
      'stage03',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
    revision: SEED_GARDEN_ASSET_REVISION,
  },
  {
    kind: 'flax_field',
    assetId: 'flax_field',
    category: 'fields',
    displayName: 'Льняное поле',
    levels: l1To10,
    states: [
      'active',
      'construction',
      'damaged',
      'ruined',
      'stage01',
      'stage02',
      'stage03',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
    revision: FLAX_FIELD_ASSET_REVISION,
  },
  {
    kind: 'herb_bed',
    assetId: 'herb_bed',
    category: 'fields',
    displayName: 'Травяная грядка',
    levels: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    states: [
      'active',
      'construction',
      'damaged',
      'ruined',
      'stage01',
      'stage02',
      'stage03',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
    revision: HERB_BED_ASSET_REVISION,
  },
  {
    kind: 'mushroom_grove',
    assetId: 'mushroom_grove',
    category: 'fields',
    displayName: 'Грибница',
    levels: l1To10,
    states: [
      'active',
      'construction',
      'damaged',
      'ruined',
      'stage01',
      'stage02',
      'stage03',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
    revision: MUSHROOM_GROVE_ASSET_REVISION,
  },
  {
    kind: 'reed_bed',
    assetId: 'reed_bed',
    category: 'fields',
    displayName: 'Тростниковая грядка',
    levels: l1To10,
    states: [
      'active',
      'construction',
      'damaged',
      'ruined',
      'stage01',
      'stage02',
      'stage03',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
    revision: REED_BED_ASSET_REVISION,
  },
  {
    kind: 'oilseed_field',
    assetId: 'oilseed_field',
    category: 'fields',
    displayName: 'Масличное поле',
    levels: l1To7,
    states: [
      'active',
      'construction',
      'damaged',
      'ruined',
      'stage01',
      'stage02',
      'stage03',
      'super_stage01',
      'super_stage02',
      'super_stage03',
      'super_stage04',
      'super_stage05',
      'super_stage06',
    ],
    spriteSource: 'public',
    modelSource: 'public',
    revision: OILSEED_FIELD_ASSET_REVISION,
  },
  {
    kind: 'lumber_yard',
    assetId: 'lumber_yard',
    category: 'industry',
    displayName: 'Лесопильный двор',
    levels: l1To13,
    states: coreStates,
    anchor: [256, 292],
    footprint: [1, 1],
    render: {
      mode: 'sprite',
      size: [512, 384],
      preferredFormat: 'webp',
      fallbackFormat: 'png',
    },
    atlas: {
      image: 'lumber_yard.webp',
      json: 'lumber_yard.atlas.json',
      revision: LUMBER_YARD_ASSET_REVISION,
    },
    animations: {
      working: {
        type: 'overlay',
        fps: 8,
        frames: 12,
        loop: true,
        anchor: [256, 292],
        framePrefix: 'lumber_yard_working_',
      },
      damaged_smoke: {
        type: 'shared_overlay',
        id: 'smoke_small',
        fps: 6,
        loop: true,
      },
    },
    spriteSource: 'public',
    modelSource: 'public',
    revision: LUMBER_YARD_ASSET_REVISION,
  },
  {
    kind: 'sand_quarry',
    assetId: 'sand_quarry',
    category: 'industry',
    displayName: 'Песчаный карьер',
    levels: l1To11,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'public',
    revision: SAND_QUARRY_ASSET_REVISION,
  },
  {
    kind: 'clay_quarry',
    assetId: 'clay_quarry',
    category: 'industry',
    displayName: 'Глиняный карьер',
    levels: l1To12,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'public',
    revision: CLAY_QUARRY_ASSET_REVISION,
  },
  {
    kind: 'mine',
    assetId: 'mine',
    category: 'industry',
    displayName: 'Шахта',
    levels: l1To12,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'public',
    revision: MINE_ASSET_REVISION,
  },
  {
    kind: 'glass_workshop',
    assetId: 'glass_workshop',
    category: 'industry',
    displayName: 'Стекольная мастерская',
    levels: l1To12,
    states: ['active', 'construction', 'damaged', 'ruined'],
    spriteSource: 'public',
    modelSource: 'public',
    revision: GLASS_WORKSHOP_ASSET_REVISION,
  },
  {
    kind: 'rope_yard',
    assetId: 'rope_yard',
    category: 'industry',
    displayName: 'Канатный двор',
    levels: l1To8,
    states: ['active', 'ready', 'idle_no_input', 'idle_no_workers', 'construction', 'damaged', 'ruined'],
    spriteSource: 'public',
    modelSource: 'public',
    revision: ROPE_YARD_ASSET_REVISION,
  },
  {
    kind: 'oil_well',
    assetId: 'oil_well',
    category: 'industry',
    displayName: 'Нефтяная вышка',
    levels: l1To3,
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    revision: OIL_WELL_ASSET_REVISION,
  },
  {
    kind: 'coin_storage',
    assetId: 'coin_storage',
    category: 'storage',
    displayName: 'Хранилище монет',
    levels: l1To12,
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    revision: COIN_STORAGE_ASSET_REVISION,
  },
  {
    kind: 'road',
    assetId: 'ground_road',
    category: 'roads',
    displayName: 'Грунтовая дорога',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
  {
    kind: 'standard_road',
    assetId: 'common_road',
    category: 'roads',
    displayName: 'Обычная дорога',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
  {
    kind: 'paved_road',
    assetId: 'paved_road',
    category: 'roads',
    displayName: 'Мостовая',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
  {
    kind: 'wooden_wall',
    assetId: 'wooden_wall',
    category: 'roads',
    displayName: 'Деревянная стена',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
  {
    kind: 'stone_wall',
    assetId: 'stone_wall',
    category: 'roads',
    displayName: 'Каменная стена',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
  {
    kind: 'concrete_wall',
    assetId: 'reinforced_wall',
    category: 'roads',
    displayName: 'Усиленная стена',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
  {
    kind: 'modern_wall',
    assetId: 'reinforced_wall',
    category: 'roads',
    displayName: 'Современная стена',
    levels: [1],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
  },
]
