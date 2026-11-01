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
  | 'armed'
  | 'triggered'
  | 'empty'
  | 'no_crew'
  | 'no_fuel'
  | 'no_mechanic'
  | 'no_keeper'
  | `stage${'01' | '02' | '03' | '04'}`
  | `super_stage${'01' | '02' | '03' | '04' | '05' | '06'}`

export type BuildingAssetSource = 'public' | 'src-models'

export type BuildingAssetManifest = RuntimeAssetManifest & {
  kind: BuildingKind
  assetId: string
  filePrefix?: string
  category: string
  displayName: string
  levels: readonly number[]
  states: readonly BuildingAssetState[]
  spriteSource: BuildingAssetSource
  modelSource: BuildingAssetSource
  strictStates?: boolean
  revision?: string
  modelLod?: string
  shapeDefault?: string
  animations?: Partial<Record<BuildingAnimationKey, NonNullable<RuntimeAssetManifest['animations']>[string]>>
}

export const LUMBER_YARD_ASSET_REVISION = 'grass-ground-2026-09-22'
export const SAND_QUARRY_ASSET_REVISION = 'mcp-midpoly-l01-l11-2026-09-24'
export const CLAY_QUARRY_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-10-12'
export const MINE_ASSET_REVISION = 'mountain-detail-runtime-l01-states-2026-10-14'
export const GLASS_WORKSHOP_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-09-29'
export const COIN_STORAGE_ASSET_REVISION = 'mcp-midpoly-l01-l12-2026-09-29-rework2'
export const SEED_GARDEN_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-09'
export const HERB_BED_ASSET_REVISION = 'mcp-midpoly-l01-l09-2026-10-09'
export const MUSHROOM_GROVE_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-10'
export const FLAX_FIELD_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-08'
export const REED_BED_ASSET_REVISION = 'mcp-midpoly-l01-l10-2026-10-09'
export const OILSEED_FIELD_ASSET_REVISION = 'mcp-midpoly-l01-l07-2026-10-09'
export const ROPE_YARD_ASSET_REVISION = 'mcp-midpoly-l01-l08-2026-10-08'
export const OIL_WELL_ASSET_REVISION = 'oil-well-no-side-rods-2026-10-14'
export const DEFENSE_CANNON_ASSET_REVISION = 'defense-cannon-2026-10-17'
export const TOWN_HALL_ASSET_REVISION = 'town-hall-vertical-2026-10-26'

const l1To3 = [1, 2, 3] as const
const l1To5 = [1, 2, 3, 4, 5] as const
const l1To6 = [1, 2, 3, 4, 5, 6] as const
const l1To7 = [1, 2, 3, 4, 5, 6, 7] as const
const l1To8 = [1, 2, 3, 4, 5, 6, 7, 8] as const
const l1To10 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const
const l1To11 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] as const
const l1To12 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] as const
const l1To13 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13] as const
const l1To15 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] as const
const coreStates = ['active', 'construction', 'damaged'] as const
const coreWithRuinedStates = ['active', 'construction', 'damaged', 'ruined'] as const
const modularWallRender = {
  anchor: [128, 160],
  render: {
    mode: 'sprite',
    size: [256, 256],
    preferredFormat: 'png',
    fallbackFormat: 'png',
  },
} as const
const modularRoadRender = {
  anchor: [128, 160],
  render: {
    mode: 'sprite',
    size: [256, 256],
    preferredFormat: 'png',
    fallbackFormat: 'png',
  },
} as const

export const buildingAssetManifests: readonly BuildingAssetManifest[] = [
  {
    kind: 'dye_garden', assetId: 'dye_garden', category: 'fields', displayName: 'Красильный сад',
    levels: l1To6,
    states: ['construction', 'stage01', 'stage02', 'stage03', 'stage04', 'active', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'dye-garden-2026-10-19',
  },
  {
    kind: 'crystal_greenhouse', assetId: 'crystal_greenhouse', category: 'fields', displayName: 'Кристальная оранжерея',
    levels: [1, 2, 3, 4],
    states: ['construction', 'stage01', 'stage02', 'stage03', 'stage04', 'active', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'crystal-greenhouse-2026-10-19',
  },
  {
    kind: 'defense_cannon', assetId: 'defense_cannon', category: 'defense', displayName: 'Пушка',
    levels: l1To12, states: coreWithRuinedStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: DEFENSE_CANNON_ASSET_REVISION,
  },
  { kind: 'defense_stakes', assetId: 'defense_stakes', category: 'defense', displayName: 'Колья',
    levels: l1To6, states: ['construction', 'armed', 'triggered', 'empty', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public', modelLod: 'LOD0' },
  { kind: 'defense_resin_snare', assetId: 'defense_resin_snare', category: 'defense', displayName: 'Смоляная западня',
    levels: [1, 2, 3, 4], states: ['construction', 'armed', 'triggered', 'empty', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public', modelLod: 'LOD0' },
  { kind: 'defense_bolt_thrower', assetId: 'defense_bolt_thrower', category: 'defense', displayName: 'Болтомёт',
    levels: l1To8, states: ['construction', 'active', 'no_crew', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public', modelLod: 'LOD0' },
  { kind: 'defense_storm_coil', assetId: 'defense_storm_coil', category: 'defense', displayName: 'Грозовая катушка',
    levels: l1To6, states: ['construction', 'active', 'no_crew', 'no_fuel', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public', modelLod: 'LOD0' },
  { kind: 'defense_automaton_bay', assetId: 'defense_automaton_bay', category: 'defense', displayName: 'Мастерская автоматонов',
    levels: l1To5, states: ['construction', 'active', 'no_mechanic', 'no_fuel', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public', modelLod: 'LOD0' },
  { kind: 'defense_guardian_enclosure', assetId: 'defense_guardian_enclosure', category: 'defense', displayName: 'Вольер союзников',
    levels: l1To5, states: ['construction', 'active', 'no_keeper', 'damaged', 'ruined'],
    spriteSource: 'public', modelSource: 'public', modelLod: 'LOD0' },
  {
    kind: 'tower', assetId: 'tower', category: 'defense', displayName: 'Сторожевая башня',
    levels: [1], states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'watchtower-2026-10-17',
  },
  {
    kind: 'town_hall',
    assetId: 'town_hall',
    category: 'center',
    displayName: 'Центр города',
    levels: l1To15,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'public',
    modelLod: 'LOD0',
    revision: TOWN_HALL_ASSET_REVISION,
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
    kind: 'stone_house',
    assetId: 'stone_house',
    category: 'housing',
    displayName: 'Каменный дом',
    levels: l1To6,
    states: coreStates,
    spriteSource: 'public',
    modelSource: 'public',
    revision: 'stone-house-l01-l06-runtime-glb-2026-10-22',
  },
  {
    kind: 'villa',
    assetId: 'villa',
    category: 'housing',
    displayName: 'Вилла',
    levels: l1To5,
    states: ['active'],
    spriteSource: 'public',
    modelSource: 'public',
    modelLod: 'LOD0',
    strictStates: true,
    revision: 'villa-l01-l05-2026-10-24',
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
    kind: 'cement_workshop', assetId: 'cement_workshop', category: 'industry', displayName: 'Цементный цех',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'cement-workshop-2026-10-18',
  },
  {
    kind: 'brick_yard', assetId: 'brick_yard', category: 'industry', displayName: 'Кирпичный двор',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'brick-yard-2026-10-17',
  },
  {
    kind: 'concrete_plant', assetId: 'concrete_plant', category: 'industry', displayName: 'Бетонный завод',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'concrete-plant-2026-10-18',
  },
  {
    kind: 'foundry', assetId: 'foundry', category: 'industry', displayName: 'Литейная',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'foundry-vat-2026-10-18',
  },
  {
    kind: 'military_factory', assetId: 'military_factory', category: 'industry', displayName: 'Военный завод',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'military-factory-2026-10-18',
  },
  {
    kind: 'paper_workshop', assetId: 'paper_workshop', category: 'industry', displayName: 'Бумажная мастерская',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'paper-workshop-2026-10-18',
  },
  {
    kind: 'tile_factory', assetId: 'tile_factory', category: 'industry', displayName: 'Черепичный завод',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'tile-factory-2026-10-18',
  },
  {
    kind: 'weaving_yard', assetId: 'weaving_yard', category: 'industry', displayName: 'Ткацкая мастерская',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'weaving-yard-2026-10-18',
  },
  {
    kind: 'dye_works', assetId: 'dye_works', category: 'industry', displayName: 'Красильня',
    levels: [1], states: coreWithRuinedStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'dye-works-2026-11-01',
  },
  {
    kind: 'siege_yard', assetId: 'siege_yard', category: 'industry', displayName: 'Осадный двор',
    levels: [1, 2], states: coreWithRuinedStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'siege-yard-2026-11-01',
  },
  {
    kind: 'resonance_laboratory', assetId: 'resonance_laboratory', category: 'industry', displayName: 'Резонансная лаборатория',
    levels: [1], states: coreWithRuinedStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'resonance-laboratory-2026-11-01',
  },
  {
    kind: 'paint_workshop', assetId: 'paint_workshop', category: 'industry', displayName: 'Красильная мастерская',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'paint-workshop-2026-10-18',
  },
  {
    kind: 'electronics_workshop', assetId: 'electronics_workshop', category: 'industry', displayName: 'Электронная мастерская',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'electronics-workshop-2026-10-18',
  },
  {
    kind: 'mechanical_workshop', assetId: 'mechanical_workshop', category: 'industry', displayName: 'Механическая мастерская',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'mechanical-workshop-steampunk-2026-10-18',
  },
  {
    kind: 'oil_press', assetId: 'oil_press', category: 'industry', displayName: 'Маслобойня',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'oil-press-2026-10-18',
  },
  {
    kind: 'oil_refinery', assetId: 'oil_refinery', category: 'industry', displayName: 'Нефтеперерабатывающий завод',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'oil-refinery-2026-10-18',
  },
  {
    kind: 'resin_kiln', assetId: 'resin_kiln', category: 'industry', displayName: 'Смолокурня',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'resin-kiln-2026-10-18',
  },
  {
    kind: 'steelworks', assetId: 'steelworks', category: 'industry', displayName: 'Сталеплавильный завод',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'steelworks-2026-10-18',
  },
  {
    kind: 'sulfur_spring', assetId: 'sulfur_spring', category: 'industry', displayName: 'Серный источник',
    levels: l1To10, states: coreStates, spriteSource: 'public', modelSource: 'public',
    modelLod: 'LOD0', revision: 'sulfur-spring-2026-10-18',
  },
  {
    kind: 'mine',
    assetId: 'mine',
    category: 'industry',
    displayName: 'Шахта',
    levels: l1To12,
    states: coreStates,
    anchor: [256, 320],
    render: {
      mode: 'sprite',
      size: [512, 512],
      mapScale: 0.58,
      preferredFormat: 'png',
      fallbackFormat: 'png',
    },
    spriteSource: 'public',
    modelSource: 'public',
    revision: MINE_ASSET_REVISION,
  },
  {
    kind: 'copper_mine',
    assetId: 'copper_mine',
    category: 'industry',
    displayName: 'Медный рудник',
    levels: l1To10,
    states: coreStates,
    anchor: [256, 320],
    render: {
      mode: 'sprite',
      size: [512, 512],
      mapScale: 0.58,
      preferredFormat: 'png',
      fallbackFormat: 'png',
    },
    spriteSource: 'public',
    modelSource: 'public',
    modelLod: 'LOD0',
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
    anchor: [256, 292],
    render: {
      mode: 'sprite',
      size: [512, 384],
      preferredFormat: 'png',
      fallbackFormat: 'png',
    },
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
    ...modularRoadRender,
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
    ...modularRoadRender,
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
    ...modularRoadRender,
  },
  {
    kind: 'wooden_wall',
    assetId: 'wooden_wall',
    category: 'roads',
    displayName: 'Деревянная стена',
    levels: [1, 2, 3],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
    ...modularWallRender,
  },
  {
    kind: 'stone_wall',
    assetId: 'stone_wall',
    category: 'roads',
    displayName: 'Каменная стена',
    levels: [4, 5, 6, 7],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
    ...modularWallRender,
  },
  {
    kind: 'concrete_wall',
    assetId: 'concrete_wall',
    category: 'roads',
    displayName: 'Бетонная стена',
    levels: [8, 9, 10],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
    ...modularWallRender,
  },
  {
    kind: 'modern_wall',
    assetId: 'modern_wall',
    category: 'roads',
    displayName: 'Современная стена',
    levels: [11, 12, 13],
    states: coreWithRuinedStates,
    spriteSource: 'public',
    modelSource: 'public',
    shapeDefault: 'single',
    ...modularWallRender,
  },
]
