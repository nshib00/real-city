import { create } from 'zustand'
import { nearestWrappedScreenCoord, roundGridCoord, screenToGrid, wrapGridCoord } from '../coordinates/iso'
import type { WorldTile } from '../../shared/contracts'

export type ToolMode = 'select' | 'build' | 'road' | 'repair' | 'attack'
export type RealtimeStatus = 'connecting' | 'connected' | 'reconnecting' | 'offline'
export type BuildingState = 'planned' | 'building' | 'repairing' | 'active' | 'damaged' | 'ruined'
export type BuildingKind =
  | `ruins_${string}`
  | 'town_hall'
  | 'dugout'
  | 'field_bed'
  | 'seed_garden'
  | 'herb_bed'
  | 'mushroom_grove'
  | 'flax_field'
  | 'reed_bed'
  | 'dye_garden'
  | 'oilseed_field'
  | 'sugar_bed'
  | 'crystal_greenhouse'
  | 'coin_storage'
  | 'workshop'
  | 'brick_kiln'
  | 'brick_yard'
  | 'glass_workshop'
  | 'forge'
  | 'weaving_yard'
  | 'dye_works'
  | 'mechanical_workshop'
  | 'optical_workshop'
  | 'mint'
  | 'market'
  | 'tower'
  | 'defense_cannon'
  | 'defense_stakes'
  | 'defense_resin_snare'
  | 'defense_bolt_thrower'
  | 'defense_storm_coil'
  | 'defense_automaton_bay'
  | 'defense_guardian_enclosure'
  | 'wooden_wall'
  | 'stone_wall'
  | 'concrete_wall'
  | 'modern_wall'
  | 'road'
  | 'standard_road'
  | 'paved_road'
  | 'alliance_house'
  | 'lumber_yard'
  | 'sand_quarry'
  | 'mine'
  | 'clay_quarry'
  | 'iron_mine'
  | 'copper_mine'
  | 'resin_kiln'
  | 'sulfur_spring'
  | 'oil_well'
  | 'stone_cutters'
  | 'tile_factory'
  | 'cement_workshop'
  | 'concrete_plant'
  | 'rope_yard'
  | 'paper_workshop'
  | 'paint_workshop'
  | 'oil_press'
  | 'foundry'
  | 'steelworks'
  | 'electronics_workshop'
  | 'oil_refinery'
  | 'chemical_workshop'
  | 'military_factory'
  | 'precision_workshop'
  | 'siege_yard'
  | 'resonance_laboratory'
  | 'wood_house'
  | 'stone_house'
  | 'apartment_house'
  | 'villa'
  | 'palace'
  | 'residential_skyscraper'

type TileCoord = {
  x: number
  y: number
}

export type PlacedBuilding = {
  id: string
  kind: BuildingKind
  name: string
  level: number
  tile: TileCoord
  rotation?: number
  footprintW?: number
  footprintH?: number
  status: 'active' | 'construction'
  state?: BuildingState
  health: number
  maxHealth?: number
  cannonEnabled?: boolean
  cannonNextAttackAt?: number | null
  cannonTargetId?: string
  cannonRange?: number
  cannonDamage?: number
  cannonAmmo?: string
  cannonCooldownSeconds?: number
  cannonDamageType?: string
  trapCharges?: number
  trapMaxCharges?: number
  trapDamage?: number
  defenseSlots?: number
  defensePatrolRadius?: number
  defenseStaffRole?: string
  demolitionRefundCoins?: number
  owner: string
  startedAt: number
  completesAt: number | null
  fieldStage?: number
  growthStage?: number
  cropStage?: number
  superStage?: number
  fieldStageStartedAt?: number | null
  fieldStageReadyAt?: number | null
  fieldStageReady?: boolean
  isSuperCrop?: boolean
  superCrop?: boolean
}

export type ResourceNode = {
  id: string
  type: string
  resource: string
  amount: number
  maxAmount: number
  state: 'neutral' | 'claimed' | 'depleted'
  ownerId: string
  tile: TileCoord
  respawnAt: number | null
}

export type MonsterEntity = {
  id: string
  creatorId?: string
  expiresAt?: number
  type: 'roaming_melee' | 'resource_guardian' | 'ruins_guardian' | 'forest_stalker' | 'spore_beast' | 'ironback_brute' | 'ember_wisp' | 'ancient_colossus'
  state: 'idle' | 'wandering' | 'aggro' | 'attacking' | 'dead'
  tile: TileCoord
  targetId: string
  targetType: string
  health: number
  maxHealth: number
  damage: number
  aggroRadius: number
  updatedAt: number
}

export type CannonShotEvent = { id: string; buildingId: string; monsterId: string; damage: number; ammo: string; kind?: BuildingKind }
export type MonsterDamageEvent = { id: string; monsterId: string; tile: TileCoord; damage: number; createdAt: number }
export type BuildingDamageEvent = { id: string; buildingId: string; tile: TileCoord; damage: number; createdAt: number }

export type UIPreferences = {
  mapPowerSave: boolean
  compactPanels: boolean
  resourceRegistryOpen: boolean
  alliancePanelOpen: boolean
  buildMenuOpen: boolean
  isChatCollapsed: boolean
  areNotificationsCollapsed: boolean
}

const defaultUIPreferences: UIPreferences = {
  mapPowerSave: false,
  compactPanels: false,
  resourceRegistryOpen: false,
  alliancePanelOpen: false,
  buildMenuOpen: false,
  isChatCollapsed: false,
  areNotificationsCollapsed: false,
}

const uiPreferencesStorageKey = 'real-city.ui-preferences'

function readUIPreferences(): UIPreferences {
  const defaults = typeof window !== 'undefined' && window.matchMedia?.('(max-width: 760px), (max-height: 500px) and (max-width: 1000px)').matches
    ? { ...defaultUIPreferences, isChatCollapsed: true, areNotificationsCollapsed: true }
    : defaultUIPreferences
  if (typeof localStorage === 'undefined') {
    return defaults
  }

  try {
    const stored = localStorage.getItem(uiPreferencesStorageKey)
    if (!stored) {
      return defaults
    }
    return { ...defaults, ...JSON.parse(stored) }
  } catch {
    return defaults
  }
}

function writeUIPreferences(preferences: UIPreferences) {
  if (typeof localStorage === 'undefined') {
    return
  }

  localStorage.setItem(uiPreferencesStorageKey, JSON.stringify(preferences))
}

type GameState = {
  tool: ToolMode
  selectedTile: TileCoord | null
  selectedBuildingId: string | null
  repairMenuBuildingId: string | null
  selectedMonsterId: string | null
  hoveredTile: TileCoord | null
  placementPreviewKind: BuildingKind | null
  relocatingBuildingId: string | null
  buildings: PlacedBuilding[]
  buildingIndexById: Record<string, number>
  resourceNodes: ResourceNode[]
  resourceNodeIndexById: Record<string, number>
  monsters: MonsterEntity[]
  monsterIndexById: Record<string, number>
  deadMonsterIds: Set<string>
  cannonShots: CannonShotEvent[]
  monsterDamageEvents: MonsterDamageEvent[]
  buildingDamageEvents: BuildingDamageEvent[]
  worldTiles: WorldTile[]
  worldTileIndexByKey: Record<string, number>
  constructionNow: number
  camera: { x: number; y: number; zoom: number }
  viewport: { center: TileCoord; radius: number }
  uiPreferences: UIPreferences
  realtimeStatus: RealtimeStatus
  setTool: (tool: ToolMode) => void
  setRelocatingBuildingId: (id: string | null) => void
  selectTile: (tile: TileCoord) => void
  selectBuilding: (buildingId: string) => void
  setRepairMenuBuildingId: (buildingId: string | null) => void
  selectMonster: (monsterId: string) => void
  hoverTile: (tile: TileCoord | null) => void
  setPlacementPreviewKind: (kind: BuildingKind | null) => void
  placeBuilding: (input: { kind: BuildingKind; name: string; tile: TileCoord; durationSeconds: number; free?: boolean; owner?: string }) => { ok: true; building: PlacedBuilding } | { ok: false; reason: string }
  addBuilding: (building: PlacedBuilding) => void
  setResourceNodes: (nodes: ResourceNode[]) => void
  upsertResourceNode: (node: ResourceNode) => void
  setMonsters: (monsters: MonsterEntity[]) => void
  upsertMonster: (monster: MonsterEntity) => void
  recordCannonShot: (event: CannonShotEvent) => void
  recordMonsterDamage: (event: MonsterDamageEvent) => void
  removeMonsterDamage: (id: string) => void
  recordBuildingDamage: (event: BuildingDamageEvent) => void
  removeBuildingDamage: (id: string) => void
  setWorldTiles: (tiles: WorldTile[]) => void
  updateWorldTile: (tile: WorldTile) => void
  tickConstructions: (now: number) => void
  deleteBuilding: (buildingId: string) => void
  panCamera: (delta: { x: number; y: number }) => void
  focusTile: (input: { tile: TileCoord; viewportWidth: number; viewportHeight: number }) => void
  setZoom: (zoom: number) => void
  setZoomAt: (input: { zoom: number; focalScreen?: TileCoord; viewportSize: { width: number; height: number } }) => void
  setViewportCenter: (center: TileCoord) => void
  setViewportRadius: (radius: number) => void
  setCompactPanels: (compactPanels: boolean) => void
  setMapPowerSave: (enabled: boolean) => void
  toggleResourceRegistry: () => void
  setBuildMenuOpen: (buildMenuOpen: boolean) => void
  setAlliancePanelOpen: (alliancePanelOpen: boolean) => void
  setChatCollapsed: (isChatCollapsed: boolean) => void
  setNotificationsCollapsed: (areNotificationsCollapsed: boolean) => void
  setRealtimeStatus: (realtimeStatus: RealtimeStatus) => void
}

export const useGameStore = create<GameState>((set) => ({
  tool: 'select',
  selectedTile: null,
  selectedBuildingId: null,
  repairMenuBuildingId: null,
  selectedMonsterId: null,
  hoveredTile: null,
  placementPreviewKind: null,
  relocatingBuildingId: null,
  buildings: [],
  buildingIndexById: {},
  resourceNodes: [],
  resourceNodeIndexById: {},
  monsters: [],
  monsterIndexById: {},
  deadMonsterIds: new Set(),
  cannonShots: [],
  monsterDamageEvents: [],
  buildingDamageEvents: [],
  worldTiles: [],
  worldTileIndexByKey: {},
  constructionNow: Date.now(),
  camera: { x: 0, y: 0, zoom: 1 },
  viewport: { center: { x: 0, y: 0 }, radius: 1 },
  uiPreferences: readUIPreferences(),
  realtimeStatus: 'connected',
  recordCannonShot: (event) => set((state) => state.cannonShots.some((item) => item.id === event.id)
    ? state
    : { cannonShots: [event, ...state.cannonShots].slice(0, 30) }),
  recordMonsterDamage: (event) => set((state) => state.monsterDamageEvents.some((item) => item.id === event.id)
    ? state
    : { monsterDamageEvents: [...state.monsterDamageEvents.filter((item) => event.createdAt - item.createdAt < 1500), event].slice(-32) }),
  removeMonsterDamage: (id) => set((state) => ({ monsterDamageEvents: state.monsterDamageEvents.filter((item) => item.id !== id) })),
  recordBuildingDamage: (event) => set((state) => state.buildingDamageEvents.some((item) => item.id === event.id)
    ? state
    : { buildingDamageEvents: [...state.buildingDamageEvents.filter((item) => event.createdAt - item.createdAt < 1500), event].slice(-32) }),
  removeBuildingDamage: (id) => set((state) => ({ buildingDamageEvents: state.buildingDamageEvents.filter((item) => item.id !== id) })),
  setTool: (tool) =>
    set((state) => ({
      tool,
      relocatingBuildingId: null,
      placementPreviewKind: tool === 'build' ? state.placementPreviewKind : null,
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, buildMenuOpen: tool === 'build' ? state.uiPreferences.buildMenuOpen : false }),
    })),
  setRelocatingBuildingId: (relocatingBuildingId) => set((state) => ({
    relocatingBuildingId,
    placementPreviewKind: relocatingBuildingId ? null : state.placementPreviewKind,
    tool: relocatingBuildingId ? 'select' : state.tool,
  })),
  selectTile: (selectedTile) => {
    set({ selectedTile, selectedBuildingId: null, selectedMonsterId: null })
  },
  selectBuilding: (selectedBuildingId) =>
    set((state) => {
      const building = findByIndexedId(state.buildings, state.buildingIndexById, selectedBuildingId)
      return {
        selectedBuildingId,
        relocatingBuildingId: null,
        selectedMonsterId: null,
        selectedTile: building?.tile ?? state.selectedTile,
        placementPreviewKind: null,
        tool: 'select',
      }
    }),
  setRepairMenuBuildingId: (repairMenuBuildingId) => set({ repairMenuBuildingId }),
  selectMonster: (selectedMonsterId) =>
    set((state) => {
      const monster = findByIndexedId(state.monsters, state.monsterIndexById, selectedMonsterId)
      return {
        selectedMonsterId,
        selectedBuildingId: null,
        selectedTile: monster?.tile ?? state.selectedTile,
        placementPreviewKind: null,
        tool: 'attack',
      }
    }),
  hoverTile: (hoveredTile) => set({ hoveredTile }),
  setPlacementPreviewKind: (placementPreviewKind) => set({ placementPreviewKind }),
  placeBuilding: (input) => {
    let result: { ok: true; building: PlacedBuilding } | { ok: false; reason: string } = { ok: false, reason: 'Не удалось разместить постройку' }
    set((state) => {
      const owner = input.owner ?? 'local-player'
      const hasTownHall = state.buildings.some((building) => building.kind === 'town_hall' && building.owner === owner)
      if (input.kind !== 'town_hall' && !hasTownHall) {
        result = { ok: false, reason: 'Сначала нужна ратуша' }
        return state
      }
      if (input.kind === 'town_hall' && hasTownHall) {
        result = { ok: false, reason: 'Ратуша может быть только одна' }
        return state
      }
      const tile = input.tile
      const isTrap = (kind: BuildingKind) => kind === 'defense_stakes' || kind === 'defense_resin_snare'
      const isRoad = (kind: BuildingKind) => kind === 'road' || kind === 'standard_road' || kind === 'paved_road'
      if (state.buildings.some((building) => building.tile.x === tile.x && building.tile.y === tile.y &&
        !((isTrap(input.kind) && isRoad(building.kind)) || (isRoad(input.kind) && isTrap(building.kind))))) {
        result = { ok: false, reason: 'Клетка уже занята' }
        return state
      }
      const now = Date.now()
      const durationMs = input.free ? 0 : input.durationSeconds * 1000
      const building: PlacedBuilding = {
        id: `${input.kind}-${Date.now()}-${state.buildings.length}`,
        kind: input.kind,
        name: input.name,
        level: 1,
        tile,
        status: input.free ? 'active' : 'construction',
        health: 100,
        owner,
        startedAt: now,
        completesAt: durationMs > 0 ? now + durationMs : null,
      }
      result = { ok: true, building }
      const nextBuildings = [...state.buildings, building]
      return {
        buildings: nextBuildings,
        buildingIndexById: { ...state.buildingIndexById, [building.id]: nextBuildings.length - 1 },
        selectedBuildingId: building.id,
        selectedTile: tile,
        uiPreferences: persistUIPreferences({ ...state.uiPreferences, buildMenuOpen: false }),
      }
    })
    return result
  },
  addBuilding: (building) =>
    set((state) => {
      const result = upsertByIndexedId(state.buildings, state.buildingIndexById, building)
      return { buildings: result.items, buildingIndexById: result.indexById }
    }),
  setResourceNodes: (nodes) => set({ resourceNodes: nodes, resourceNodeIndexById: buildIndexById(nodes) }),
  upsertResourceNode: (node) =>
    set((state) => {
      const result = upsertByIndexedId(state.resourceNodes, state.resourceNodeIndexById, node)
      return { resourceNodes: result.items, resourceNodeIndexById: result.indexById }
    }),
  setMonsters: (monsters) => set((state) => {
    const visible = monsters.filter((monster) => monster.state !== 'dead' && !state.deadMonsterIds.has(monster.id))
    return { monsters: visible, monsterIndexById: buildIndexById(visible) }
  }),
  upsertMonster: (monster) =>
    set((state) => {
      if (monster.state !== 'dead' && state.deadMonsterIds.has(monster.id)) return state
      const result = monster.state === 'dead'
        ? removeByIndexedId(state.monsters, state.monsterIndexById, monster.id)
        : upsertByIndexedId(state.monsters, state.monsterIndexById, monster)
      return {
        monsters: result.items,
        monsterIndexById: result.indexById,
        deadMonsterIds: monster.state === 'dead' ? new Set([...state.deadMonsterIds, monster.id]) : state.deadMonsterIds,
        selectedMonsterId: monster.state === 'dead' && state.selectedMonsterId === monster.id ? null : state.selectedMonsterId,
      }
    }),
  setWorldTiles: (tiles) => set({ worldTiles: tiles, worldTileIndexByKey: indexWorldTiles(tiles) }),
  updateWorldTile: (tile) =>
    set((state) => {
      const result = upsertWorldTile(state.worldTiles, state.worldTileIndexByKey, tile)
      return { worldTiles: result.items, worldTileIndexByKey: result.indexByKey }
    }),
  tickConstructions: (now) =>
    set((state) => {
      let buildings: PlacedBuilding[] | null = null
      for (let index = 0; index < state.buildings.length; index += 1) {
        const building = state.buildings[index]
        const completed = building.status === 'construction' && building.state !== 'repairing' && building.completesAt && building.completesAt <= now
          ? { ...building, status: 'active' as const, state: 'active' as const, completesAt: null }
          : building
        const next = completed.fieldStageReadyAt && completed.fieldStageReadyAt <= now && !completed.fieldStageReady
          ? { ...completed, fieldStageReady: true }
          : completed
        if (next !== building) {
          buildings ??= state.buildings.slice()
          buildings[index] = next
        }
      }
      return buildings ? { constructionNow: now, buildings } : { constructionNow: now }
    }),
  deleteBuilding: (buildingId) =>
    set((state) => {
      const result = removeByIndexedId(state.buildings, state.buildingIndexById, buildingId)
      return {
        buildings: result.items,
        buildingIndexById: result.indexById,
        selectedBuildingId: state.selectedBuildingId === buildingId ? null : state.selectedBuildingId,
      }
    }),
  panCamera: (delta) =>
    set((state) => ({
      camera: {
        ...state.camera,
        x: state.camera.x + delta.x,
        y: state.camera.y + delta.y,
      },
    })),
  focusTile: ({ tile, viewportWidth, viewportHeight }) =>
    set((state) => {
      const wrappedTile = wrapGridCoord(tile)
      const origin = { x: viewportWidth * 0.48 + state.camera.x, y: viewportHeight * 0.16 + state.camera.y }
      const target = { x: (viewportWidth / 2 - origin.x) / state.camera.zoom, y: (viewportHeight / 2 - origin.y) / state.camera.zoom }
      const screen = nearestWrappedScreenCoord(wrappedTile, target)
      const camera = {
        x: viewportWidth / 2 - viewportWidth * 0.48 - screen.x * state.camera.zoom,
        y: viewportHeight / 2 - viewportHeight * 0.16 - screen.y * state.camera.zoom,
      }
      return {
        camera: { ...state.camera, ...camera },
        selectedTile: wrappedTile,
        selectedBuildingId: null,
        viewport: { center: wrappedTile, radius: state.viewport.radius },
      }
    }),
  setZoom: (zoom) =>
    set((state) => ({
      camera: { ...state.camera, zoom: Math.max(0.6, Math.min(1.6, zoom)) },
    })),
  setZoomAt: ({ zoom, focalScreen, viewportSize }) =>
    set((state) => {
      const nextZoom = Math.max(0.6, Math.min(1.6, zoom))
      const target = focalScreen ?? { x: viewportSize.width / 2, y: viewportSize.height / 2 }
      const originBase = { x: viewportSize.width * 0.48, y: viewportSize.height * 0.16 }
      const origin = { x: originBase.x + state.camera.x, y: originBase.y + state.camera.y }
      const worldScreen = {
        x: (target.x - origin.x) / state.camera.zoom,
        y: (target.y - origin.y) / state.camera.zoom,
      }
      const camera = {
        x: target.x - originBase.x - worldScreen.x * nextZoom,
        y: target.y - originBase.y - worldScreen.y * nextZoom,
      }
      const center = wrapGridCoord(roundGridCoord(screenToGrid({
        x: (viewportSize.width / 2 - originBase.x - camera.x) / nextZoom,
        y: (viewportSize.height / 2 - originBase.y - camera.y) / nextZoom,
      })))
      return { camera: { ...camera, zoom: nextZoom }, viewport: { ...state.viewport, center } }
    }),
  setViewportCenter: (center) => set((state) => ({ viewport: { ...state.viewport, center: wrapGridCoord(center) } })),
  setViewportRadius: (radius) =>
    set((state) => ({
      viewport: { ...state.viewport, radius: Math.max(1, Math.min(3, Math.round(radius))) },
    })),
  setCompactPanels: (compactPanels) =>
    set((state) => ({
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, compactPanels }),
    })),
  setMapPowerSave: (mapPowerSave) =>
    set((state) => ({
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, mapPowerSave }),
    })),
  toggleResourceRegistry: () =>
    set((state) => ({
      uiPreferences: persistUIPreferences({
        ...state.uiPreferences,
        resourceRegistryOpen: !state.uiPreferences.resourceRegistryOpen,
      }),
    })),
  setBuildMenuOpen: (buildMenuOpen) =>
    set((state) => ({
      tool: buildMenuOpen ? 'build' : state.tool,
      placementPreviewKind: buildMenuOpen ? state.placementPreviewKind : null,
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, buildMenuOpen }),
    })),
  setAlliancePanelOpen: (alliancePanelOpen) =>
    set((state) => ({
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, alliancePanelOpen }),
    })),
  setChatCollapsed: (isChatCollapsed) =>
    set((state) => ({
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, isChatCollapsed }),
    })),
  setNotificationsCollapsed: (areNotificationsCollapsed) =>
    set((state) => ({
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, areNotificationsCollapsed }),
    })),
  setRealtimeStatus: (realtimeStatus) => set({ realtimeStatus }),
}))

function persistUIPreferences(preferences: UIPreferences) {
  writeUIPreferences(preferences)
  return preferences
}

function findByIndexedId<T extends { id: string }>(items: T[], indexById: Record<string, number>, id: string) {
  const index = indexById[id]
  if (index !== undefined && items[index]?.id === id) {
    return items[index]
  }
  return items.find((item) => item.id === id)
}

function buildIndexById<T extends { id: string }>(items: T[]) {
  const index: Record<string, number> = {}
  items.forEach((item, position) => {
    index[item.id] = position
  })
  return index
}

function upsertByIndexedId<T extends { id: string }>(items: T[], indexById: Record<string, number>, item: T) {
  let index = indexById[item.id]
  if (index === undefined || items[index]?.id !== item.id) {
    index = items.findIndex((current) => current.id === item.id)
  }
  if (index === -1) {
    return {
      items: [...items, item],
      indexById: { ...indexById, [item.id]: items.length },
    }
  }
  if (items[index] === item) {
    return { items, indexById }
  }
  const next = items.slice()
  next[index] = item
  return {
    items: next,
    indexById: indexById[item.id] === index ? indexById : { ...indexById, [item.id]: index },
  }
}

function removeByIndexedId<T extends { id: string }>(items: T[], indexById: Record<string, number>, id: string) {
  let index = indexById[id]
  if (index === undefined || items[index]?.id !== id) {
    index = items.findIndex((item) => item.id === id)
  }
  if (index === -1) {
    return { items, indexById }
  }
  const next = [...items.slice(0, index), ...items.slice(index + 1)]
  return { items: next, indexById: buildIndexById(next) }
}

function indexWorldTiles(items: WorldTile[]) {
  const index: Record<string, number> = {}
  items.forEach((item, position) => {
    index[tileKey(item)] = position
  })
  return index
}

function upsertWorldTile(items: WorldTile[], indexByKey: Record<string, number>, tile: WorldTile) {
  const key = tileKey(tile)
  let index = indexByKey[key]
  if (index === undefined || tileKey(items[index]) !== key) {
    index = items.findIndex((item) => item.x === tile.x && item.y === tile.y)
  }
  if (index === -1) {
    return {
      items: [...items, tile],
      indexByKey: { ...indexByKey, [key]: items.length },
    }
  }
  if (items[index] === tile) {
    return { items, indexByKey }
  }
  const next = items.slice()
  next[index] = tile
  return {
    items: next,
    indexByKey: indexByKey[key] === index ? indexByKey : { ...indexByKey, [key]: index },
  }
}

function tileKey(tile: TileCoord) {
  return `${tile.x}:${tile.y}`
}
