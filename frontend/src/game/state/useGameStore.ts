import { create } from 'zustand'
import { gridToScreen, wrapCameraOffset, wrapGridCoord } from '../coordinates/iso'
import type { WorldTile } from '../../shared/contracts'

export type ToolMode = 'select' | 'build' | 'road' | 'repair' | 'raid'
export type RealtimeStatus = 'connecting' | 'connected' | 'reconnecting' | 'offline'
export type BuildingState = 'planned' | 'building' | 'active' | 'damaged' | 'ruined'
export type BuildingKind =
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
  | 'warehouse'
  | 'coin_storage'
  | 'workshop'
  | 'brick_kiln'
  | 'glass_workshop'
  | 'forge'
  | 'weaving_yard'
  | 'dye_works'
  | 'mechanical_workshop'
  | 'optical_workshop'
  | 'mint'
  | 'market'
  | 'tower'
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
  status: 'active' | 'construction'
  state?: BuildingState
  health: number
  maxHealth?: number
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

export type UIPreferences = {
  compactPanels: boolean
  resourceRegistryOpen: boolean
  alliancePanelOpen: boolean
  buildMenuOpen: boolean
  isChatCollapsed: boolean
  areNotificationsCollapsed: boolean
}

const defaultUIPreferences: UIPreferences = {
  compactPanels: false,
  resourceRegistryOpen: false,
  alliancePanelOpen: false,
  buildMenuOpen: false,
  isChatCollapsed: false,
  areNotificationsCollapsed: false,
}

const uiPreferencesStorageKey = 'real-city.ui-preferences'

function readUIPreferences(): UIPreferences {
  if (typeof localStorage === 'undefined') {
    return defaultUIPreferences
  }

  try {
    const stored = localStorage.getItem(uiPreferencesStorageKey)
    if (!stored) {
      return defaultUIPreferences
    }
    return { ...defaultUIPreferences, ...JSON.parse(stored) }
  } catch {
    return defaultUIPreferences
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
  selectedMonsterId: string | null
  hoveredTile: TileCoord | null
  buildings: PlacedBuilding[]
  buildingIndexById: Record<string, number>
  resourceNodes: ResourceNode[]
  resourceNodeIndexById: Record<string, number>
  monsters: MonsterEntity[]
  monsterIndexById: Record<string, number>
  worldTiles: WorldTile[]
  worldTileIndexByKey: Record<string, number>
  constructionNow: number
  camera: { x: number; y: number; zoom: number }
  viewport: { center: TileCoord; radius: number }
  uiPreferences: UIPreferences
  realtimeStatus: RealtimeStatus
  setTool: (tool: ToolMode) => void
  selectTile: (tile: TileCoord) => void
  selectBuilding: (buildingId: string) => void
  selectMonster: (monsterId: string) => void
  hoverTile: (tile: TileCoord | null) => void
  placeBuilding: (input: { kind: BuildingKind; name: string; tile: TileCoord; durationSeconds: number; free?: boolean; owner?: string }) => { ok: true; building: PlacedBuilding } | { ok: false; reason: string }
  addBuilding: (building: PlacedBuilding) => void
  setResourceNodes: (nodes: ResourceNode[]) => void
  upsertResourceNode: (node: ResourceNode) => void
  setMonsters: (monsters: MonsterEntity[]) => void
  upsertMonster: (monster: MonsterEntity) => void
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
  selectedMonsterId: null,
  hoveredTile: null,
  buildings: [],
  buildingIndexById: {},
  resourceNodes: [],
  resourceNodeIndexById: {},
  monsters: [],
  monsterIndexById: {},
  worldTiles: [],
  worldTileIndexByKey: {},
  constructionNow: Date.now(),
  camera: { x: 0, y: 0, zoom: 1 },
  viewport: { center: { x: 0, y: 0 }, radius: 1 },
  uiPreferences: readUIPreferences(),
  realtimeStatus: 'connected',
  setTool: (tool) =>
    set((state) => ({
      tool,
      uiPreferences: persistUIPreferences({ ...state.uiPreferences, buildMenuOpen: tool === 'build' ? state.uiPreferences.buildMenuOpen : false }),
    })),
  selectTile: (selectedTile) => {
    set({ selectedTile, selectedBuildingId: null, selectedMonsterId: null })
  },
  selectBuilding: (selectedBuildingId) =>
    set((state) => {
      const building = findByIndexedId(state.buildings, state.buildingIndexById, selectedBuildingId)
      return {
        selectedBuildingId,
        selectedMonsterId: null,
        selectedTile: building?.tile ?? state.selectedTile,
        tool: 'select',
      }
    }),
  selectMonster: (selectedMonsterId) =>
    set((state) => {
      const monster = findByIndexedId(state.monsters, state.monsterIndexById, selectedMonsterId)
      return {
        selectedMonsterId,
        selectedBuildingId: null,
        selectedTile: monster?.tile ?? state.selectedTile,
        tool: 'raid',
      }
    }),
  hoverTile: (hoveredTile) => set({ hoveredTile }),
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
      if (state.buildings.some((building) => building.tile.x === tile.x && building.tile.y === tile.y)) {
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
  setMonsters: (monsters) => set({ monsters, monsterIndexById: buildIndexById(monsters) }),
  upsertMonster: (monster) =>
    set((state) => {
      const result = monster.state === 'dead'
        ? removeByIndexedId(state.monsters, state.monsterIndexById, monster.id)
        : upsertByIndexedId(state.monsters, state.monsterIndexById, monster)
      return {
        monsters: result.items,
        monsterIndexById: result.indexById,
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
    set((state) => ({
      constructionNow: now,
      buildings: state.buildings.map((building) => {
        const completed =
          building.status === 'construction' && building.completesAt && building.completesAt <= now
            ? { ...building, status: 'active' as const, state: 'active' as const, completesAt: null }
            : building
        return completed.fieldStageReadyAt && completed.fieldStageReadyAt <= now ? { ...completed, fieldStageReady: true } : completed
      }),
    })),
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
        ...wrapCameraOffset({ x: state.camera.x + delta.x, y: state.camera.y + delta.y }),
      },
    })),
  focusTile: ({ tile, viewportWidth, viewportHeight }) =>
    set((state) => {
      const wrappedTile = wrapGridCoord(tile)
      const screen = gridToScreen(wrappedTile)
      const camera = wrapCameraOffset({
        x: viewportWidth / 2 - viewportWidth * 0.48 - screen.x * state.camera.zoom,
        y: viewportHeight / 2 - viewportHeight * 0.16 - screen.y * state.camera.zoom,
      })
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
      const camera = wrapCameraOffset({
        x: target.x - originBase.x - worldScreen.x * nextZoom,
        y: target.y - originBase.y - worldScreen.y * nextZoom,
      })
      return { camera: { ...camera, zoom: nextZoom } }
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
