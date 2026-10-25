import type { WorldTile } from '../../shared/contracts'
import type { BuildingKind, MonsterEntity, PlacedBuilding, ResourceNode } from '../state/useGameStore'

export type PerformanceScenarioName = 'buildings' | 'monsters' | 'mixed'

export type PerformanceScenario = {
  name: PerformanceScenarioName
  buildings: PlacedBuilding[]
  monsters: MonsterEntity[]
  resources: ResourceNode[]
  tiles: WorldTile[]
}

type ScenarioOptions = {
  center?: { x: number; y: number }
  buildingCount?: number
  monsterCount?: number
  resourceCount?: number
  tileRadius?: number
  now?: number
}

const BUILDING_KINDS: BuildingKind[] = [
  'town_hall',
  'lumber_yard',
  'sand_quarry',
  'mine',
  'glass_workshop',
  'coin_storage',
  'rope_yard',
  'field_bed',
  'seed_garden',
  'flax_field',
  'road',
]

const MONSTER_TYPES: MonsterEntity['type'][] = [
  'roaming_melee',
  'resource_guardian',
  'ruins_guardian',
  'forest_stalker',
  'spore_beast',
  'ironback_brute',
  'ember_wisp',
  'ancient_colossus',
]

const MONSTER_STATES: MonsterEntity['state'][] = ['idle', 'wandering', 'aggro', 'attacking']

export function resolvePerformanceScenarioFromSearch(search: string, isDev = import.meta.env.DEV): PerformanceScenario | null {
  if (!isDev) {
    return null
  }

  const params = new URLSearchParams(search)
  const name = scenarioName(params.get('perf') ?? params.get('perfScenario'))
  if (!name) {
    return null
  }

  return createPerformanceScenario(name, {
    buildingCount: numberParam(params, 'perfBuildings', name === 'monsters' ? 360 : 2600),
    monsterCount: numberParam(params, 'perfMonsters', name === 'buildings' ? 160 : 720),
    resourceCount: numberParam(params, 'perfResources', 260),
    tileRadius: numberParam(params, 'perfTileRadius', 34),
    now: Date.now(),
  })
}

export function createPerformanceScenario(name: PerformanceScenarioName, options: ScenarioOptions = {}): PerformanceScenario {
  const center = options.center ?? { x: 0, y: 0 }
  const buildingCount = name === 'monsters' ? options.buildingCount ?? 360 : options.buildingCount ?? 2600
  const monsterCount = name === 'buildings' ? options.monsterCount ?? 160 : options.monsterCount ?? 720
  const resourceCount = options.resourceCount ?? 260
  const tileRadius = options.tileRadius ?? 34
  const now = options.now ?? Date.now()

  return {
    name,
    buildings: createFakeBuildings(buildingCount, center, now),
    monsters: createAnimatedMonsters(monsterCount, center, now),
    resources: createFakeResources(resourceCount, center, now),
    tiles: createFakeTiles(tileRadius, center),
  }
}

export function createFakeBuildings(count: number, center = { x: 0, y: 0 }, now = Date.now()): PlacedBuilding[] {
  const columns = Math.max(1, Math.ceil(Math.sqrt(count * 1.45)))
  const rows = Math.max(1, Math.ceil(count / columns))
  const startX = center.x - Math.floor(columns / 2)
  const startY = center.y - Math.floor(rows / 2)
  const buildings: PlacedBuilding[] = []

  for (let index = 0; index < count; index += 1) {
    const kind = BUILDING_KINDS[index % BUILDING_KINDS.length]
    const x = startX + (index % columns)
    const y = startY + Math.floor(index / columns)
    const health = index % 17 === 0 ? 18 : index % 11 === 0 ? 48 : 100
    buildings.push({
      id: `perf-building-${index}`,
      kind,
      name: `Perf ${kind} ${index}`,
      level: (index % 4) + 1,
      tile: { x, y },
      status: index % 23 === 0 ? 'construction' : 'active',
      state: health < 35 ? 'damaged' : 'active',
      health,
      maxHealth: 100,
      owner: index % 5 === 0 ? 'perf-rival' : 'local-player',
      startedAt: now - 60_000,
      completesAt: index % 23 === 0 ? now + 120_000 : null,
      fieldStage: kind.includes('field') || kind.includes('garden') || kind === 'field_bed' ? (index % 4) + 1 : undefined,
      fieldStageReady: index % 7 === 0,
      fieldStageReadyAt: index % 7 === 0 ? now - 1000 : now + 90_000,
    })
  }

  return buildings
}

export function createAnimatedMonsters(count: number, center = { x: 0, y: 0 }, now = Date.now()): MonsterEntity[] {
  const columns = Math.max(1, Math.ceil(Math.sqrt(count * 1.25)))
  const startX = center.x - Math.floor(columns / 2)
  const startY = center.y + 8
  const monsters: MonsterEntity[] = []

  for (let index = 0; index < count; index += 1) {
    const type = MONSTER_TYPES[index % MONSTER_TYPES.length]
    const maxHealth = type === 'ancient_colossus' ? 900 : 90 + (index % 6) * 30
    const state = MONSTER_STATES[index % MONSTER_STATES.length]
    monsters.push({
      id: `perf-monster-${index}`,
      type,
      state,
      tile: {
        x: startX + (index % columns) + (state === 'wandering' ? 1 : 0),
        y: startY + Math.floor(index / columns),
      },
      targetId: state === 'attacking' ? `perf-building-${index % 200}` : '',
      targetType: state === 'attacking' ? 'building' : '',
      health: Math.max(1, Math.round(maxHealth * (0.35 + (index % 7) * 0.09))),
      maxHealth,
      damage: 8 + (index % 9) * 3,
      aggroRadius: 3 + (index % 4),
      updatedAt: now - (index % 9) * 140,
    })
  }

  return monsters
}

export function createFakeResources(count: number, center = { x: 0, y: 0 }, now = Date.now()): ResourceNode[] {
  const resources = ['wood', 'stone', 'oil']
  const columns = Math.max(1, Math.ceil(Math.sqrt(count)))
  const startX = center.x - Math.floor(columns / 2)
  const startY = center.y - 18
  const nodes: ResourceNode[] = []

  for (let index = 0; index < count; index += 1) {
    const maxAmount = 80 + (index % 5) * 40
    const depleted = index % 13 === 0
    nodes.push({
      id: `perf-resource-${index}`,
      type: `${resources[index % resources.length]}_node`,
      resource: resources[index % resources.length],
      amount: depleted ? 0 : Math.round(maxAmount * (0.25 + (index % 8) * 0.09)),
      maxAmount,
      state: depleted ? 'depleted' : index % 3 === 0 ? 'claimed' : 'neutral',
      ownerId: index % 3 === 0 ? 'local-player' : '',
      tile: { x: startX + (index % columns), y: startY + Math.floor(index / columns) },
      respawnAt: depleted ? now + 300_000 : null,
    })
  }

  return nodes
}

export function createFakeTiles(radius: number, center = { x: 0, y: 0 }): WorldTile[] {
  const tiles: WorldTile[] = []
  for (let y = center.y - radius; y <= center.y + radius; y += 1) {
    for (let x = center.x - radius; x <= center.x + radius; x += 1) {
      tiles.push({
        x,
        y,
        chunk_x: Math.floor(x / 16),
        chunk_y: Math.floor(y / 16),
        terrain: (x + y) % 19 === 0 ? 'water' : (x * 3 + y) % 17 === 0 ? 'forest' : (x - y) % 23 === 0 ? 'mountain' : 'grass',
        elevation: Math.abs((x * 7 + y * 11) % 9),
        safe_zone: Math.abs(x - center.x) < 4 && Math.abs(y - center.y) < 4,
        forest_density: (x * 5 + y * 3) % 17 === 0 ? 3 : 0,
      })
    }
  }
  return tiles
}

function scenarioName(value: string | null): PerformanceScenarioName | null {
  if (value === 'buildings' || value === 'monsters' || value === 'mixed') {
    return value
  }
  if (value === '1' || value === 'true' || value === 'objects') {
    return 'mixed'
  }
  return null
}

function numberParam(params: URLSearchParams, key: string, fallback: number) {
  const raw = params.get(key)
  if (raw === null || raw.trim() === '') return fallback
  const value = Number(raw)
  return Number.isFinite(value) && value >= 0 ? Math.round(value) : fallback
}
