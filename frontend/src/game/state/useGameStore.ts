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
  | 'warehouse'
  | 'coin_storage'
  | 'workshop'
  | 'market'
  | 'tower'
  | 'wooden_wall'
  | 'stone_wall'
  | 'concrete_wall'
  | 'modern_wall'
  | 'road'
  | 'alliance_house'
  | 'lumber_yard'
  | 'stone_cutters'
  | 'oil_refinery'
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
  type: 'roaming_melee' | 'resource_guardian' | 'ruins_guardian'
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

type GameState = {
  tool: ToolMode
  selectedTile: TileCoord | null
  selectedBuildingId: string | null
  selectedMonsterId: string | null
  hoveredTile: TileCoord | null
  buildings: PlacedBuilding[]
  resourceNodes: ResourceNode[]
  monsters: MonsterEntity[]
  worldTiles: WorldTile[]
  constructionNow: number
  camera: { x: number; y: number; zoom: number }
  viewport: { center: TileCoord; radius: number }
  uiPreferences: {
    compactPanels: boolean
    resourceRegistryOpen: boolean
    alliancePanelOpen: boolean
    buildMenuOpen: boolean
  }
  realtimeStatus: RealtimeStatus
  setTool: (tool: ToolMode) => void
  selectTile: (tile: TileCoord) => void
  selectBuilding: (buildingId: string) => void
  selectMonster: (monsterId: string) => void
  hoverTile: (tile: TileCoord | null) => void
  placeBuilding: (input: { kind: BuildingKind; name: string; tile: TileCoord; durationSeconds: number; free?: boolean }) => { ok: true; building: PlacedBuilding } | { ok: false; reason: string }
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
  setViewportCenter: (center: TileCoord) => void
  setViewportRadius: (radius: number) => void
  setCompactPanels: (compactPanels: boolean) => void
  toggleResourceRegistry: () => void
  setBuildMenuOpen: (buildMenuOpen: boolean) => void
  setAlliancePanelOpen: (alliancePanelOpen: boolean) => void
  setRealtimeStatus: (realtimeStatus: RealtimeStatus) => void
}

export const useGameStore = create<GameState>((set) => ({
  tool: 'select',
  selectedTile: null,
  selectedBuildingId: null,
  selectedMonsterId: null,
  hoveredTile: null,
  buildings: [],
  resourceNodes: [],
  monsters: [],
  worldTiles: [],
  constructionNow: Date.now(),
  camera: { x: 0, y: 0, zoom: 1 },
  viewport: { center: { x: 0, y: 0 }, radius: 1 },
  uiPreferences: {
    compactPanels: false,
    resourceRegistryOpen: false,
    alliancePanelOpen: false,
    buildMenuOpen: false,
  },
  realtimeStatus: 'connected',
  setTool: (tool) =>
    set((state) => ({
      tool,
      uiPreferences: { ...state.uiPreferences, buildMenuOpen: tool === 'build' ? state.uiPreferences.buildMenuOpen : false },
    })),
  selectTile: (selectedTile) => {
    const wrappedTile = wrapGridCoord(selectedTile)
    set({ selectedTile: wrappedTile, selectedBuildingId: null, selectedMonsterId: null })
  },
  selectBuilding: (selectedBuildingId) =>
    set((state) => {
      const building = state.buildings.find((item) => item.id === selectedBuildingId)
      return {
        selectedBuildingId,
        selectedMonsterId: null,
        selectedTile: building?.tile ?? state.selectedTile,
        tool: 'select',
      }
    }),
  selectMonster: (selectedMonsterId) =>
    set((state) => {
      const monster = state.monsters.find((item) => item.id === selectedMonsterId)
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
      const hasTownHall = state.buildings.some((building) => building.kind === 'town_hall')
      if (input.kind !== 'town_hall' && !hasTownHall) {
        result = { ok: false, reason: 'Сначала нужна ратуша' }
        return state
      }
      if (input.kind === 'town_hall' && hasTownHall) {
        result = { ok: false, reason: 'Ратуша может быть только одна' }
        return state
      }
      const tile = wrapGridCoord(input.tile)
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
        owner: 'Северный двор',
        startedAt: now,
        completesAt: durationMs > 0 ? now + durationMs : null,
      }
      result = { ok: true, building }
      return {
        buildings: [...state.buildings, building],
        selectedBuildingId: building.id,
        selectedTile: tile,
        uiPreferences: { ...state.uiPreferences, buildMenuOpen: false },
      }
    })
    return result
  },
  addBuilding: (building) =>
    set((state) => ({
      buildings: [...state.buildings.filter((item) => item.id !== building.id), building],
      selectedBuildingId: building.id,
      selectedTile: building.tile,
      uiPreferences: { ...state.uiPreferences, buildMenuOpen: false },
    })),
  setResourceNodes: (nodes) => set({ resourceNodes: nodes }),
  upsertResourceNode: (node) =>
    set((state) => ({
      resourceNodes: [...state.resourceNodes.filter((item) => item.id !== node.id), node],
    })),
  setMonsters: (monsters) => set({ monsters }),
  upsertMonster: (monster) =>
    set((state) => ({
      monsters: monster.state === 'dead' ? state.monsters.filter((item) => item.id !== monster.id) : [...state.monsters.filter((item) => item.id !== monster.id), monster],
      selectedMonsterId: monster.state === 'dead' && state.selectedMonsterId === monster.id ? null : state.selectedMonsterId,
    })),
  setWorldTiles: (tiles) => set({ worldTiles: tiles }),
  updateWorldTile: (tile) =>
    set((state) => ({
      worldTiles: state.worldTiles.map((item) => (item.x === tile.x && item.y === tile.y ? tile : item)),
    })),
  tickConstructions: (now) =>
    set((state) => ({
      constructionNow: now,
      buildings: state.buildings.map((building) => {
        const completed =
          building.status === 'construction' && building.completesAt && building.completesAt <= now
            ? { ...building, status: 'active' as const, completesAt: null }
            : building
        return completed.fieldStageReadyAt && completed.fieldStageReadyAt <= now ? { ...completed, fieldStageReady: true } : completed
      }),
    })),
  deleteBuilding: (buildingId) =>
    set((state) => ({
      buildings: state.buildings.filter((building) => building.id !== buildingId),
      selectedBuildingId: state.selectedBuildingId === buildingId ? null : state.selectedBuildingId,
    })),
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
  setViewportCenter: (center) => set((state) => ({ viewport: { ...state.viewport, center: wrapGridCoord(center) } })),
  setViewportRadius: (radius) =>
    set((state) => ({
      viewport: { ...state.viewport, radius: Math.max(1, Math.min(4, Math.round(radius))) },
    })),
  setCompactPanels: (compactPanels) =>
    set((state) => ({
      uiPreferences: { ...state.uiPreferences, compactPanels },
    })),
  toggleResourceRegistry: () =>
    set((state) => ({
      uiPreferences: {
        ...state.uiPreferences,
        resourceRegistryOpen: !state.uiPreferences.resourceRegistryOpen,
      },
    })),
  setBuildMenuOpen: (buildMenuOpen) =>
    set((state) => ({
      tool: buildMenuOpen ? 'build' : state.tool,
      uiPreferences: { ...state.uiPreferences, buildMenuOpen },
    })),
  setAlliancePanelOpen: (alliancePanelOpen) =>
    set((state) => ({
      uiPreferences: { ...state.uiPreferences, alliancePanelOpen },
    })),
  setRealtimeStatus: (realtimeStatus) => set({ realtimeStatus }),
}))
