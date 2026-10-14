import { Application, Assets, Container, Graphics, Sprite, Texture } from 'pixi.js'
import { useEffect, useRef } from 'react'
import type { MouseEvent, PointerEvent } from 'react'

import type { WorldTile } from '../../shared/contracts'
import { nearestWrappedScreenCoord, roundGridCoord, screenToGrid, TILE_HEIGHT, TILE_WIDTH } from '../coordinates/iso'
import type { MonsterEntity, PlacedBuilding, ResourceNode } from '../state/useGameStore'
import { buildingOverlayDrawCommands, type BuildingOverlayDrawCommand } from './objectLayer/buildingOverlayDrawData'
import { monsterDrawCommands, nextMonsterRenderMemory, type MonsterDrawCommand, type MonsterRenderMemory } from './objectLayer/monsterDrawData'
import { buildingDrawCommands, type BuildingDrawCommand } from './objectLayer/objectDrawData'
import { objectLayerSortKey } from './objectLayer/objectDepth'
import { resourceDrawCommands, type ResourceDrawCommand } from './objectLayer/resourceDrawData'
import { buildingHitAtTile } from './mapHitTarget'
import { recordPixiFrame, registerPixiContext } from './renderPerformanceMetrics'
import { preloadTerrainPngTextures, TERRAIN_SPRITE, terrainTextureUrl } from './terrainTextures'
import { tileOccupancyKey } from './visibleObjects'

type Camera = {
  x: number
  y: number
  zoom: number
}

type TileCoord = {
  x: number
  y: number
}

type PixiStageProps = {
  tiles: WorldTile[]
  occupiedTiles: Set<string>
  buildings?: PlacedBuilding[]
  allBuildings?: PlacedBuilding[]
  resources?: ResourceNode[]
  monsters?: MonsterEntity[]
  camera: Camera
  selectedTile: TileCoord | null
  hoveredTile: TileCoord | null
  selectedBuildingId?: string | null
  selectedMonsterId?: string | null
  onSelectTile: (tile: TileCoord) => void
  onHoverTile: (tile: TileCoord | null) => void
  onSelectBuilding?: (building: PlacedBuilding) => void
  onSelectMonster?: (monster: MonsterEntity) => void
}

const TERRAIN_COLORS: Record<string, number> = {
  grass: 0x83d96f,
  forest: 0x1f6f43,
  water: 0x67c7f0,
  mountain: 0x777d82,
  road: 0xa77952,
  oil_well: 0x000000,
  ruins: 0xe9842c,
}

const TILE_POINTS = [0, -TILE_HEIGHT / 2, TILE_WIDTH / 2, 0, 0, TILE_HEIGHT / 2, -TILE_WIDTH / 2, 0]

type BuildingHitArea = {
  building: PlacedBuilding
  left: number
  right: number
  top: number
  bottom: number
  sortKey: number
}

type MonsterHitArea = {
  monster: MonsterEntity
  left: number
  right: number
  top: number
  bottom: number
  sortKey: number
}

type ResourceHitArea = {
  node: ResourceNode
  left: number
  right: number
  top: number
  bottom: number
  sortKey: number
}

type RetainedChild = Container['children'][number]
type RetainedChildCache = Map<string, RetainedChild>
type TextureLoadState = 'loading' | 'loaded' | 'failed'

const textureLoadStates = new Map<string, TextureLoadState>()

export function PixiStage({
  tiles,
  occupiedTiles,
  buildings = [],
  allBuildings = buildings,
  resources = [],
  monsters = [],
  camera,
  selectedTile,
  hoveredTile,
  selectedBuildingId = null,
  selectedMonsterId = null,
  onSelectTile,
  onHoverTile,
  onSelectBuilding,
  onSelectMonster,
}: PixiStageProps) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const appRef = useRef<Application | null>(null)
  const terrainSpritesRef = useRef<Container | null>(null)
  const objectSpritesRef = useRef<Container | null>(null)
  const monsterSpritesRef = useRef<Container | null>(null)
  const buildingAnimationOverlaysRef = useRef<Container | null>(null)
  const terrainSpriteCacheRef = useRef<RetainedChildCache>(new Map())
  const buildingSpriteCacheRef = useRef<RetainedChildCache>(new Map())
  const resourceSpriteCacheRef = useRef<RetainedChildCache>(new Map())
  const buildingOverlayCacheRef = useRef<RetainedChildCache>(new Map())
  const terrainRef = useRef<Graphics | null>(null)
  const overlayRef = useRef<Graphics | null>(null)
  const tilesRef = useRef<WorldTile[]>(tiles)
  const occupiedTilesRef = useRef<Set<string>>(occupiedTiles)
  const buildingsRef = useRef<PlacedBuilding[]>(buildings)
  const allBuildingsRef = useRef<PlacedBuilding[]>(allBuildings)
  const resourcesRef = useRef<ResourceNode[]>(resources)
  const monstersRef = useRef<MonsterEntity[]>(monsters)
  const buildingDrawCommandsRef = useRef<BuildingDrawCommand[]>([])
  const monsterRenderMemoryRef = useRef<Map<string, MonsterRenderMemory>>(new Map())
  const cameraRef = useRef<Camera>(camera)
  const selectedTileRef = useRef<TileCoord | null>(selectedTile)
  const hoveredTileRef = useRef<TileCoord | null>(hoveredTile)
  const selectedBuildingIdRef = useRef<string | null>(selectedBuildingId)
  const selectedMonsterIdRef = useRef<string | null>(selectedMonsterId)
  const buildingHitAreasRef = useRef<BuildingHitArea[]>([])
  const resourceHitAreasRef = useRef<ResourceHitArea[]>([])
  const monsterHitAreasRef = useRef<MonsterHitArea[]>([])
  const redrawRef = useRef<(() => void) | null>(null)

  function redraw() {
    const app = appRef.current
    const terrainSprites = terrainSpritesRef.current
    const objectSprites = objectSpritesRef.current
    const monsterSprites = monsterSpritesRef.current
    const buildingAnimationOverlays = buildingAnimationOverlaysRef.current
    const terrain = terrainRef.current
    const overlay = overlayRef.current
    if (!app || !terrainSprites || !objectSprites || !monsterSprites || !buildingAnimationOverlays || !terrain || !overlay) {
      return
    }
    buildingDrawCommandsRef.current = drawStage(
      app,
      terrainSprites,
      objectSprites,
      monsterSprites,
      buildingAnimationOverlays,
      terrainSpriteCacheRef.current,
      buildingSpriteCacheRef.current,
      resourceSpriteCacheRef.current,
      buildingOverlayCacheRef.current,
      terrain,
      overlay,
      tilesRef.current,
      occupiedTilesRef.current,
      buildingsRef.current,
      allBuildingsRef.current,
      resourcesRef.current,
      monstersRef.current,
      cameraRef.current,
      selectedTileRef.current,
      hoveredTileRef.current,
      selectedBuildingIdRef.current,
      selectedMonsterIdRef.current,
      buildingHitAreasRef.current,
      resourceHitAreasRef.current,
      monsterHitAreasRef.current,
      monsterRenderMemoryRef.current,
      () => redrawRef.current?.(),
    )
  }

  redrawRef.current = redraw

  useEffect(() => {
    let app: Application | null = null
    let disposed = false
    let unregisterPixiContext: (() => void) | null = null

    async function mount() {
      if (!hostRef.current) {
        return
      }
      const nextApp = new Application()
      await nextApp.init({
        antialias: true,
        autoDensity: true,
        backgroundAlpha: 0,
        resolution: window.devicePixelRatio || 1,
        resizeTo: hostRef.current,
      })
      if (disposed || !hostRef.current) {
        nextApp.destroy()
        return
      }
      app = nextApp
      appRef.current = nextApp
      unregisterPixiContext = registerPixiContext()
      app.ticker.maxFPS = 60
      terrainSpritesRef.current = new Container()
      objectSpritesRef.current = new Container()
      monsterSpritesRef.current = new Container()
      buildingAnimationOverlaysRef.current = new Container()
      terrainRef.current = new Graphics()
      overlayRef.current = new Graphics()
      app.stage.addChild(terrainSpritesRef.current)
      app.stage.addChild(terrainRef.current)
      app.stage.addChild(objectSpritesRef.current)
      app.stage.addChild(monsterSpritesRef.current)
      app.stage.addChild(overlayRef.current)
      app.stage.addChild(buildingAnimationOverlaysRef.current)
      hostRef.current.appendChild(app.canvas)
      const animateMonsters = () => {
        recordPixiFrame(performance.now())
        if (!monsterSpritesRef.current) {
          return
        }
        drawMonsterLayer(
          monsterSpritesRef.current,
          monstersRef.current,
          selectedMonsterIdRef.current,
          cameraRef.current,
          app?.screen.width ?? 0,
          app?.screen.height ?? 0,
          monsterHitAreasRef.current,
          monsterRenderMemoryRef.current,
          performance.now(),
        )
      }
      const animateBuildingOverlays = () => {
        if (!buildingAnimationOverlaysRef.current) {
          return
        }
        drawBuildingAnimationOverlays(
          buildingAnimationOverlaysRef.current,
          buildingOverlayCacheRef.current,
          buildingDrawCommandsRef.current,
          cameraRef.current,
          app?.screen.width ?? 0,
          app?.screen.height ?? 0,
          performance.now(),
        )
      }
      app.ticker.add(animateMonsters)
      app.ticker.add(animateBuildingOverlays)
      redraw()
      void preloadTerrainPngTextures().then(() => {
        if (!disposed && terrainSpritesRef.current && objectSpritesRef.current && monsterSpritesRef.current && buildingAnimationOverlaysRef.current && terrainRef.current && overlayRef.current) {
          redraw()
        }
      })
    }

    void mount()

    return () => {
      disposed = true
      app?.destroy()
      unregisterPixiContext?.()
      unregisterPixiContext = null
      appRef.current = null
      terrainSpritesRef.current = null
      objectSpritesRef.current = null
      monsterSpritesRef.current = null
      buildingAnimationOverlaysRef.current = null
      terrainRef.current = null
      overlayRef.current = null
      app = null
    }
  }, [])

  useEffect(() => {
    tilesRef.current = tiles
    occupiedTilesRef.current = occupiedTiles
    buildingsRef.current = buildings
    allBuildingsRef.current = allBuildings
    resourcesRef.current = resources
    monstersRef.current = monsters
    cameraRef.current = camera
    selectedTileRef.current = selectedTile
    hoveredTileRef.current = hoveredTile
    selectedBuildingIdRef.current = selectedBuildingId
    selectedMonsterIdRef.current = selectedMonsterId
    const app = appRef.current
    const terrainSprites = terrainSpritesRef.current
    const objectSprites = objectSpritesRef.current
    const monsterSprites = monsterSpritesRef.current
    const buildingAnimationOverlays = buildingAnimationOverlaysRef.current
    const terrain = terrainRef.current
    const overlay = overlayRef.current
    if (app && terrainSprites && objectSprites && monsterSprites && buildingAnimationOverlays && terrain && overlay) {
      redraw()
    }
  }, [allBuildings, buildings, camera, hoveredTile, monsters, occupiedTiles, resources, selectedBuildingId, selectedMonsterId, selectedTile, tiles])

  return (
    <div
      className="pixi-stage"
      data-testid="pixi-stage-host"
      ref={hostRef}
      role="presentation"
      onClick={(event) => {
        const tile = eventToTile(event, hostRef.current, cameraRef.current)
        const buildingOnTile = buildingHitAtTile(tile, buildingHitAreasRef.current)
        if (buildingOnTile) {
          onSelectBuilding?.(buildingOnTile)
          return
        }
        const object = eventToMapObject(event, hostRef.current, buildingHitAreasRef.current, resourceHitAreasRef.current, monsterHitAreasRef.current)
        if (object?.type === 'building') {
          if (tile && !occupiedTilesRef.current.has(tileOccupancyKey(tile))) {
            onSelectTile(tile)
            return
          }
          onSelectBuilding?.(object.building)
          return
        }
        if (object?.type === 'resource') {
          onSelectTile(object.node.tile)
          return
        }
        if (object?.type === 'monster') {
          onSelectMonster?.(object.monster)
          return
        }
        if (tile) {
          onSelectTile(tile)
        }
      }}
      onPointerMove={(event) => {
        if (event.buttons === 1) {
          return
        }
        onHoverTile(eventToTile(event, hostRef.current, cameraRef.current))
      }}
      onPointerLeave={() => onHoverTile(null)}
    />
  )
}

function drawStage(
  app: Application,
  terrainSprites: Container,
  objectSprites: Container,
  monsterSprites: Container,
  buildingAnimationOverlays: Container,
  terrainSpriteCache: RetainedChildCache,
  buildingSpriteCache: RetainedChildCache,
  resourceSpriteCache: RetainedChildCache,
  buildingOverlayCache: RetainedChildCache,
  terrain: Graphics,
  overlay: Graphics,
  tiles: WorldTile[],
  _occupiedTiles: Set<string>,
  buildings: PlacedBuilding[],
  allBuildings: PlacedBuilding[],
  resources: ResourceNode[],
  monsters: MonsterEntity[],
  camera: Camera,
  selectedTile: TileCoord | null,
  hoveredTile: TileCoord | null,
  selectedBuildingId: string | null,
  selectedMonsterId: string | null,
  buildingHitAreas: BuildingHitArea[],
  resourceHitAreas: ResourceHitArea[],
  monsterHitAreas: MonsterHitArea[],
  monsterRenderMemory: Map<string, MonsterRenderMemory>,
  requestRedraw: () => void,
) {
  const width = app.screen.width
  const height = app.screen.height
  const origin = { x: width * 0.48 + camera.x, y: height * 0.16 + camera.y }
  const screenTarget = { x: (width / 2 - origin.x) / camera.zoom, y: (height / 2 - origin.y) / camera.zoom }
  buildingHitAreas.length = 0
  resourceHitAreas.length = 0
  monsterHitAreas.length = 0
  terrain.clear()
  overlay.clear()
  const activeTerrainKeys = new Set<string>()
  const activeBuildingIds = new Set<string>()
  const activeResourceIds = new Set<string>()

  const visibleTiles: { tile: WorldTile; x: number; y: number }[] = []
  for (const tile of tiles) {
    const pos = nearestWrappedScreenCoord(tile, screenTarget)
    const x = origin.x + pos.x * camera.zoom
    const y = origin.y + pos.y * camera.zoom
    const spriteScale = TILE_WIDTH * camera.zoom / TERRAIN_SPRITE.footprintWidth
    const halfWidth = TERRAIN_SPRITE.width * spriteScale / 2
    const topHeight = TERRAIN_SPRITE.height * TERRAIN_SPRITE.anchorY * spriteScale
    const bottomHeight = (TILE_HEIGHT * camera.zoom) / 2
    if (x + halfWidth < 0 || x - halfWidth > width || y + bottomHeight < 0 || y - topHeight > height) {
      continue
    }
    visibleTiles.push({ tile, x, y })
  }

  for (const { tile, x, y } of visibleTiles) {
    const textureUrl = terrainTextureUrl(tile)
    if (textureUrl && isTextureReady(textureUrl, requestRedraw)) {
      const key = tileOccupancyKey(tile)
      activeTerrainKeys.add(key)
      drawTerrainSprite(objectSprites, terrainSpriteCache, key, textureUrl, x, y, camera.zoom, objectLayerSortKey(tile, -100))
      if (tile.safe_zone) {
        drawDiamondBorder(terrain, x, y, camera.zoom, 0xf2c14e, 0.42)
      }
    } else {
      drawDiamond(terrain, x, y, camera.zoom, terrainColor(tile), tile.safe_zone ? 0xf2c14e : 0xffffff, tile.safe_zone ? 0.42 : 0.18)
    }
  }

  if (hoveredTile) {
    drawOverlay(overlay, hoveredTile, origin, screenTarget, camera.zoom, 0xffffff, 0.36)
  }
  if (selectedTile) {
    drawOverlay(overlay, selectedTile, origin, screenTarget, camera.zoom, 0xf2c14e, 0.9)
  }

  const buildingCommands = buildingDrawCommands(buildings, { allBuildings, selectedBuildingId })
  for (const command of buildingCommands) {
    activeBuildingIds.add(command.id)
    drawBuildingSprite(objectSprites, buildingSpriteCache, command, origin, screenTarget, camera.zoom, buildingHitAreas, requestRedraw)
  }
  for (const command of resourceDrawCommands(resources)) {
    activeResourceIds.add(command.id)
    drawResourceNode(objectSprites, resourceSpriteCache, command, origin, screenTarget, camera.zoom, resourceHitAreas)
  }
  pruneRetainedChildren(terrainSpriteCache, activeTerrainKeys)
  pruneRetainedChildren(buildingSpriteCache, activeBuildingIds)
  pruneRetainedChildren(resourceSpriteCache, activeResourceIds)
  const nowMs = performance.now()
  drawMonsterLayer(monsterSprites, monsters, selectedMonsterId, camera, width, height, monsterHitAreas, monsterRenderMemory, nowMs)
  drawBuildingOverlayCommands(
    buildingAnimationOverlays,
    buildingOverlayCache,
    buildingOverlayDrawCommands(buildingCommands, { zoom: camera.zoom, nowMs }),
    origin,
    screenTarget,
    camera.zoom,
  )
  return buildingCommands
}

function pruneRetainedChildren(cache: RetainedChildCache, activeKeys: ReadonlySet<string>) {
  for (const [key, child] of cache) {
    if (!activeKeys.has(key)) {
      child.parent?.removeChild(child)
      child.destroy({ children: true })
      cache.delete(key)
    }
  }
}

function drawMonsterLayer(
  target: Container,
  monsters: MonsterEntity[],
  selectedMonsterId: string | null,
  camera: Camera,
  width: number,
  height: number,
  monsterHitAreas: MonsterHitArea[],
  monsterRenderMemory: Map<string, MonsterRenderMemory>,
  nowMs: number,
) {
  monsterHitAreas.length = 0
  const origin = { x: width * 0.48 + camera.x, y: height * 0.16 + camera.y }
  const screenTarget = { x: (width / 2 - origin.x) / camera.zoom, y: (height / 2 - origin.y) / camera.zoom }
  const nextMonsterMemory = nextMonsterRenderMemory(monsters, monsterRenderMemory, nowMs)
  monsterRenderMemory.clear()
  for (const [id, memory] of nextMonsterMemory) {
    monsterRenderMemory.set(id, memory)
  }
  const activeMonsterIds = new Set(monsters.map((monster) => monster.id))
  for (const child of target.children.filter(isMonsterLayerChild)) {
    const monsterId = (child as Container & { objectLayerKind?: string; objectId?: string }).objectId
    if (!monsterId || !activeMonsterIds.has(monsterId)) {
      target.removeChild(child)
      child.destroy({ children: true })
    }
  }
  target.sortableChildren = true
  for (const command of monsterDrawCommands(monsters, { selectedMonsterId, previous: monsterRenderMemory, nowMs })) {
    drawMonsterSprite(target, command, origin, screenTarget, camera.zoom, monsterHitAreas)
  }
}

function isMonsterLayerChild(child: Container['children'][number]) {
  return (child as { objectLayerKind?: string }).objectLayerKind === 'monster'
}

function drawBuildingAnimationOverlays(
  target: Container,
  cache: RetainedChildCache,
  buildingCommands: BuildingDrawCommand[],
  camera: Camera,
  width: number,
  height: number,
  nowMs: number,
) {
  const origin = { x: width * 0.48 + camera.x, y: height * 0.16 + camera.y }
  const screenTarget = { x: (width / 2 - origin.x) / camera.zoom, y: (height / 2 - origin.y) / camera.zoom }
  drawBuildingOverlayCommands(
    target,
    cache,
    buildingOverlayDrawCommands(buildingCommands, { zoom: camera.zoom, nowMs }),
    origin,
    screenTarget,
    camera.zoom,
  )
}

function drawBuildingOverlayCommands(
  target: Container,
  cache: RetainedChildCache,
  commands: BuildingOverlayDrawCommand[],
  origin: TileCoord,
  screenTarget: TileCoord,
  zoom: number,
) {
  target.sortableChildren = true
  const activeKeys = new Set<string>()
  for (const command of commands) {
    const key = `${command.buildingId}:${command.key}`
    activeKeys.add(key)
    drawBuildingOverlay(target, cache, key, command, origin, screenTarget, zoom)
  }
  pruneRetainedChildren(cache, activeKeys)
}

function drawBuildingOverlay(
  target: Container,
  cache: RetainedChildCache,
  key: string,
  command: BuildingOverlayDrawCommand,
  origin: TileCoord,
  screenTarget: TileCoord,
  zoom: number,
) {
  const pos = nearestWrappedScreenCoord(command.tile, screenTarget)
  const x = origin.x + pos.x * zoom
  const y = origin.y + pos.y * zoom
  const graphic = getOrCreateGraphics(target, cache, key)
  graphic.clear()
  graphic.zIndex = command.sortKey
  graphic.alpha = overlayAlpha(command)

  if (command.key === 'damaged_smoke') {
    drawSmokeOverlay(graphic, x, y, zoom, command.phase)
  } else if (command.key === 'damaged_fire') {
    drawFireOverlay(graphic, x, y, zoom, command.phase)
  } else if (command.key === 'construction_dust') {
    drawDustOverlay(graphic, x, y, zoom, command.phase)
  } else if (command.key === 'ready_to_collect') {
    drawReadyOverlay(graphic, x, y, zoom, command.phase)
  } else if (command.key === 'under_attack') {
    drawHitFlashOverlay(graphic, x, y, zoom, command.phase)
  } else {
    drawWorkingOverlay(graphic, x, y, zoom, command.phase)
  }

}

function overlayAlpha(command: BuildingOverlayDrawCommand) {
  if (command.key === 'under_attack') {
    return Math.max(0.12, 1 - command.phase)
  }
  return command.selected ? 1 : 0.86
}

function drawWorkingOverlay(target: Graphics, x: number, y: number, zoom: number, phase: number) {
  const pulse = Math.sin(phase * Math.PI * 2) * 0.5 + 0.5
  const radius = (3 + pulse * 3) * zoom
  const offsetY = (118 - pulse * 8) * zoom
  target.circle(x - 28 * zoom, y - offsetY, radius).fill({ color: 0xffc857, alpha: 0.65 })
  target.circle(x + 10 * zoom, y - (offsetY + 16 * zoom), radius * 0.72).fill({ color: 0xfff1a8, alpha: 0.55 })
  target.circle(x + 36 * zoom, y - (offsetY - 8 * zoom), radius * 0.56).fill({ color: 0xe98735, alpha: 0.45 })
}

function drawSmokeOverlay(target: Graphics, x: number, y: number, zoom: number, phase: number) {
  for (let index = 0; index < 3; index += 1) {
    const localPhase = (phase + index * 0.28) % 1
    const drift = Math.sin((localPhase + index) * Math.PI * 2) * 10 * zoom
    const radius = (8 + localPhase * 12) * zoom
    const alpha = Math.max(0, 0.42 * (1 - localPhase))
    target.circle(x + (18 + index * 12) * zoom + drift, y - (126 + localPhase * 54) * zoom, radius).fill({ color: 0x4d5354, alpha })
  }
}

function drawFireOverlay(target: Graphics, x: number, y: number, zoom: number, phase: number) {
  for (let index = 0; index < 3; index += 1) {
    const localPhase = (phase + index * 0.18) % 1
    const flameHeight = (18 + (1 - localPhase) * 12) * zoom
    const baseX = x + (index * 11 - 2) * zoom
    const baseY = y - (112 + index * 5) * zoom
    target
      .poly([baseX - 8 * zoom, baseY, baseX, baseY - flameHeight, baseX + 8 * zoom, baseY], true)
      .fill({ color: index === 1 ? 0xfff1a8 : 0xff6b35, alpha: 0.58 + localPhase * 0.2 })
  }
}

function drawDustOverlay(target: Graphics, x: number, y: number, zoom: number, phase: number) {
  for (let index = 0; index < 4; index += 1) {
    const localPhase = (phase + index * 0.22) % 1
    const side = index % 2 === 0 ? -1 : 1
    const radius = (4 + localPhase * 7) * zoom
    target.circle(x + side * (34 + localPhase * 30) * zoom, y - (38 + index * 5) * zoom, radius).fill({
      color: 0xc49a6c,
      alpha: Math.max(0, 0.45 * (1 - localPhase)),
    })
  }
}

function drawReadyOverlay(target: Graphics, x: number, y: number, zoom: number, phase: number) {
  const bob = Math.sin(phase * Math.PI * 2) * 5 * zoom
  const cx = x + 70 * zoom
  const cy = y - 178 * zoom + bob
  const radius = 13 * zoom
  target.circle(cx, cy, radius).fill({ color: 0x2f9e44, alpha: 0.88 }).stroke({ color: 0xd8f5a2, alpha: 0.95, width: Math.max(1, 2 * zoom) })
  target
    .poly([cx - 6 * zoom, cy, cx - 1 * zoom, cy + 5 * zoom, cx + 8 * zoom, cy - 7 * zoom], false)
    .stroke({ color: 0xffffff, alpha: 0.95, width: Math.max(1.5, 2.4 * zoom) })
}

function drawHitFlashOverlay(target: Graphics, x: number, y: number, zoom: number, phase: number) {
  const radius = (58 + phase * 28) * zoom
  target.circle(x, y - 112 * zoom, radius).stroke({ color: 0xff4d4f, alpha: Math.max(0, 0.75 * (1 - phase)), width: Math.max(2, 4 * zoom) })
}

function drawBuildingSprite(
  target: Container,
  cache: RetainedChildCache,
  command: BuildingDrawCommand,
  origin: TileCoord,
  screenTarget: TileCoord,
  zoom: number,
  buildingHitAreas: BuildingHitArea[],
  requestRedraw: () => void,
) {
  const pos = nearestWrappedScreenCoord(command.tile, screenTarget)
  const x = origin.x + pos.x * zoom
  const y = origin.y + pos.y * zoom
  target.sortableChildren = true
  if (command.textureUrl && isTextureReady(command.textureUrl, requestRedraw)) {
    const sprite = getOrCreateSprite(target, cache, command.id, command.textureUrl)
    sprite.anchor.set(command.anchor.x, command.anchor.y)
    sprite.position.set(x, y)
    sprite.width = command.size.width * zoom
    sprite.height = command.size.height * zoom
    sprite.zIndex = command.sortKey
    sprite.alpha = 0.98
    sprite.tint = 0xffffff
  } else {
    const fallback = getOrCreateGraphics(target, cache, command.id)
    fallback.clear()
    fallback.zIndex = command.sortKey
    drawBuildingFallback(fallback, command, x, y, zoom)
  }

  const left = x - command.size.width * zoom * command.anchor.x
  const top = y - command.size.height * zoom * command.anchor.y
  buildingHitAreas.push({
    building: command.building,
    left,
    right: left + command.size.width * zoom,
    top,
    bottom: top + command.size.height * zoom,
    sortKey: command.sortKey,
  })
}

function drawBuildingFallback(target: Graphics, command: BuildingDrawCommand, x: number, y: number, zoom: number) {
  const palette = buildingFallbackPalette(command.building.kind)
  const healthRatio = command.building.maxHealth && command.building.maxHealth > 0
    ? Math.max(0, Math.min(1, command.building.health / command.building.maxHealth))
    : Math.max(0, Math.min(1, command.building.health / 100))
  const damaged = healthRatio <= 0.35
  const construction = command.building.status === 'construction'
  const width = 96 * zoom
  const height = 92 * zoom
  const baseY = y + 8 * zoom

  target.ellipse(x, baseY + 18 * zoom, width * 0.52, 18 * zoom).fill({ color: 0x000000, alpha: 0.2 })
  target
    .poly([
      x - width * 0.42, baseY,
      x, baseY - height * 0.28,
      x + width * 0.42, baseY,
      x, baseY + height * 0.25,
    ], true)
    .fill({ color: palette.base, alpha: construction ? 0.68 : 0.92 })
    .stroke({ color: palette.stroke, alpha: 0.58, width: Math.max(1.5, 2.2 * zoom) })
  target
    .poly([
      x - width * 0.34, baseY - height * 0.16,
      x, baseY - height * 0.4,
      x + width * 0.34, baseY - height * 0.16,
      x, baseY + height * 0.06,
    ], true)
    .fill({ color: palette.roof, alpha: construction ? 0.58 : 0.9 })

  if (construction) {
    target.rect(x - width * 0.28, baseY - height * 0.14, width * 0.56, Math.max(4, 7 * zoom)).fill({ color: 0xf2c14e, alpha: 0.8 })
    target.rect(x - width * 0.2, baseY + height * 0.06, width * 0.4, Math.max(3, 5 * zoom)).fill({ color: 0xf2c14e, alpha: 0.6 })
  } else {
    target.rect(x - width * 0.09, baseY - height * 0.08, width * 0.18, height * 0.28).fill({ color: palette.detail, alpha: 0.88 })
  }

  if (damaged) {
    target
      .poly([
        x + width * 0.12, baseY - height * 0.32,
        x + width * 0.22, baseY - height * 0.16,
        x + width * 0.1, baseY - height * 0.04,
      ], false)
      .stroke({ color: 0x3d2d2f, alpha: 0.9, width: Math.max(1.5, 2.4 * zoom) })
  }
}

function buildingFallbackPalette(kind: string) {
  if (kind.includes('wall')) {
    return { base: 0x858c8f, roof: 0x6b7377, detail: 0x3f484d, stroke: 0xc4cccf }
  }
  if (kind.includes('road')) {
    return { base: 0xa77952, roof: 0x7c583b, detail: 0xd0aa70, stroke: 0xe5c68c }
  }
  if (kind.includes('field') || kind.includes('garden') || kind.includes('bed')) {
    return { base: 0x3e7f4f, roof: 0x65a86a, detail: 0xe2c46f, stroke: 0xb9d989 }
  }
  if (kind.includes('storage') || kind.includes('warehouse')) {
    return { base: 0x8c6b45, roof: 0x5f4632, detail: 0xe2b766, stroke: 0xd8b987 }
  }
  if (kind.includes('tower') || kind.includes('military')) {
    return { base: 0x6f7782, roof: 0x9a4d45, detail: 0x2f3945, stroke: 0xd1d7d9 }
  }
  return { base: 0x6d8a78, roof: 0xb45f45, detail: 0xf2c14e, stroke: 0xd8e0d2 }
}

function drawMonsterSprite(
  target: Container,
  command: MonsterDrawCommand,
  origin: TileCoord,
  screenTarget: TileCoord,
  zoom: number,
  monsterHitAreas: MonsterHitArea[],
) {
  const pos = nearestWrappedScreenCoord(command.displayTile, screenTarget)
  const x = origin.x + pos.x * zoom
  const y = origin.y + (pos.y - 18) * zoom
  const group = getOrCreateMonsterGroup(target, command.id)
  for (const child of group.removeChildren()) {
    child.destroy()
  }
  const monsterGroup = group as Container & { objectLayerKind: string; objectId: string }
  monsterGroup.objectLayerKind = 'monster'
  monsterGroup.objectId = command.id
  group.zIndex = command.sortKey

  drawMonsterFallback(group, command, x, y, zoom)
  drawMonsterHealthBar(group, command, x, y, zoom)

  const left = x - command.size.width * zoom * command.anchor.x
  const top = y - command.size.height * zoom * command.anchor.y
  monsterHitAreas.push({
    monster: command.monster,
    left,
    right: left + command.size.width * zoom,
    top,
    bottom: top + command.size.height * zoom,
    sortKey: command.sortKey,
  })
}

function getOrCreateMonsterGroup(target: Container, id: string) {
  const existing = target.children.find((child) => isMonsterLayerChild(child) && (child as Container & { objectId?: string }).objectId === id)
  if (existing) {
    return existing as Container
  }
  const group = new Container()
  const monsterGroup = group as Container & { objectLayerKind: string; objectId: string }
  monsterGroup.objectLayerKind = 'monster'
  monsterGroup.objectId = id
  target.addChild(group)
  return group
}

function drawResourceNode(
  target: Container,
  cache: RetainedChildCache,
  command: ResourceDrawCommand,
  origin: TileCoord,
  screenTarget: TileCoord,
  zoom: number,
  resourceHitAreas: ResourceHitArea[],
) {
  const pos = nearestWrappedScreenCoord(command.tile, screenTarget)
  const x = origin.x + pos.x * zoom
  const y = origin.y + (pos.y - 18) * zoom
  const group = getOrCreateContainer(target, cache, command.id)
  for (const child of group.removeChildren()) {
    child.destroy()
  }
  group.zIndex = command.sortKey
  target.sortableChildren = true

  drawResourceFallback(group, command, x, y, zoom)

  const left = x - command.size.width * zoom * command.anchor.x
  const top = y - command.size.height * zoom * command.anchor.y
  resourceHitAreas.push({
    node: command.node,
    left,
    right: left + command.size.width * zoom,
    top,
    bottom: top + command.size.height * zoom,
    sortKey: command.sortKey,
  })
}

function drawResourceFallback(target: Container, command: ResourceDrawCommand, x: number, y: number, zoom: number) {
  const graphic = new Graphics()
  const palette = resourcePalette(command.resource)
  const width = command.size.width * zoom
  const height = command.size.height * zoom
  const depleted = command.overlayState === 'depleted'
  const alpha = depleted ? 0.42 : 0.92

  graphic.ellipse(x, y + height * 0.16, width * 0.38, height * 0.16).fill({ color: 0x000000, alpha: 0.2 })
  if (command.resource === 'wood') {
    graphic.roundRect(x - width * 0.08, y - height * 0.36, width * 0.16, height * 0.48, 4 * zoom).fill({ color: 0x8b5a2b, alpha })
    graphic.circle(x - width * 0.12, y - height * 0.34, width * 0.2).fill({ color: palette.primary, alpha })
    graphic.circle(x + width * 0.08, y - height * 0.42, width * 0.22).fill({ color: palette.secondary, alpha })
    graphic.circle(x + width * 0.16, y - height * 0.22, width * 0.18).fill({ color: palette.primary, alpha })
  } else if (command.resource === 'oil') {
    graphic.ellipse(x, y - height * 0.14, width * 0.28, height * 0.22).fill({ color: palette.primary, alpha })
    graphic.rect(x - width * 0.1, y - height * 0.5, width * 0.2, height * 0.36).fill({ color: palette.secondary, alpha })
    graphic.circle(x + width * 0.2, y - height * 0.46, Math.max(2, 5 * zoom)).fill({ color: 0x2bd0ff, alpha: depleted ? 0.24 : 0.7 })
  } else {
    graphic.poly([
      x - width * 0.32, y + height * 0.08,
      x - width * 0.18, y - height * 0.28,
      x + width * 0.1, y - height * 0.34,
      x + width * 0.34, y - height * 0.04,
      x + width * 0.18, y + height * 0.18,
    ], true).fill({ color: palette.primary, alpha })
    graphic.circle(x - width * 0.04, y - height * 0.16, Math.max(3, 8 * zoom)).fill({ color: palette.secondary, alpha: alpha * 0.9 })
  }

  if (command.overlayState === 'claimed') {
    graphic.ellipse(x, y + height * 0.16, width * 0.44, height * 0.19).stroke({ color: 0xf2c14e, alpha: 0.9, width: Math.max(1.5, 2.2 * zoom) })
  } else if (command.overlayState === 'contested') {
    graphic.ellipse(x, y + height * 0.16, width * 0.46, height * 0.2).stroke({ color: 0xff4d4f, alpha: 0.86, width: Math.max(1.5, 2.4 * zoom) })
  }

  const barWidth = width * 0.54
  const barHeight = Math.max(3, 4 * zoom)
  graphic.roundRect(x - barWidth / 2, y + height * 0.28, barWidth, barHeight, barHeight / 2).fill({ color: 0x15191c, alpha: 0.52 })
  graphic.roundRect(x - barWidth / 2, y + height * 0.28, barWidth * command.amountRatio, barHeight, barHeight / 2).fill({ color: depleted ? 0x8d9290 : 0x66d17a, alpha: 0.82 })

  target.addChild(graphic)
}

function resourcePalette(resource: string) {
  if (resource === 'wood') {
    return { primary: 0x2f7f4f, secondary: 0x47a86c }
  }
  if (resource === 'oil') {
    return { primary: 0x07090c, secondary: 0x2f3945 }
  }
  return { primary: 0x8d9290, secondary: 0xc2c9c7 }
}

function drawMonsterFallback(target: Container, command: MonsterDrawCommand, x: number, y: number, zoom: number) {
  const graphic = new Graphics()
  const healthTint = command.healthRatio < 0.35 ? 0xb23a48 : command.monster.state === 'attacking' ? 0xd77a32 : 0x4b6f7f
  const bodyWidth = command.size.width * 0.34 * zoom
  const bodyHeight = command.size.height * 0.42 * zoom
  const bob = command.animationKey === 'walk' ? Math.sin(performance.now() / 110 + command.id.length) * 3 * zoom : 0
  const yBase = y + bob

  graphic.ellipse(x, yBase - bodyHeight * 0.46, bodyWidth * 0.62, bodyHeight * 0.72).fill({ color: healthTint, alpha: command.monster.state === 'dead' ? 0.36 : 0.92 })
  graphic.circle(x, yBase - bodyHeight * 1.08, bodyWidth * 0.42).fill({ color: 0x263238, alpha: command.monster.state === 'dead' ? 0.32 : 0.95 })
  graphic.circle(x - bodyWidth * 0.16, yBase - bodyHeight * 1.14, Math.max(1.5, 3 * zoom)).fill({ color: 0xffe08a, alpha: 0.9 })
  graphic.circle(x + bodyWidth * 0.16, yBase - bodyHeight * 1.14, Math.max(1.5, 3 * zoom)).fill({ color: 0xffe08a, alpha: 0.9 })

  if (command.selected) {
    graphic
      .ellipse(x, y + 4 * zoom, bodyWidth * 0.84, 13 * zoom)
      .stroke({ color: 0xfff1a8, alpha: 0.95, width: Math.max(1.5, 2.5 * zoom) })
  } else {
    graphic.ellipse(x, y + 5 * zoom, bodyWidth * 0.72, 9 * zoom).fill({ color: 0x000000, alpha: 0.18 })
  }

  if (command.animationKey === 'attack') {
    const side = command.direction === 'nw' || command.direction === 'sw' ? -1 : 1
    graphic
      .poly([x + side * bodyWidth * 0.55, yBase - bodyHeight * 0.9, x + side * bodyWidth * 1.05, yBase - bodyHeight * 1.12, x + side * bodyWidth * 0.72, yBase - bodyHeight * 0.72], true)
      .fill({ color: 0xffc857, alpha: 0.58 })
  }

  target.addChild(graphic)
}

function drawMonsterHealthBar(target: Container, command: MonsterDrawCommand, x: number, y: number, zoom: number) {
  if (command.monster.state === 'dead') {
    return
  }
  const width = 58 * zoom
  const height = Math.max(3, 5 * zoom)
  const top = y - command.size.height * 0.78 * zoom
  const graphic = new Graphics()
  graphic.roundRect(x - width / 2, top, width, height, height / 2).fill({ color: 0x15191c, alpha: 0.74 })
  graphic.roundRect(x - width / 2, top, width * command.healthRatio, height, height / 2).fill({ color: command.healthRatio < 0.35 ? 0xff4d4f : 0x66d17a, alpha: 0.92 })
  target.addChild(graphic)
}

function drawTerrainSprite(target: Container, cache: RetainedChildCache, key: string, textureUrl: string, x: number, y: number, zoom: number, sortKey: number) {
  const sprite = getOrCreateSprite(target, cache, key, textureUrl)
  sprite.anchor.set(TERRAIN_SPRITE.anchorX, TERRAIN_SPRITE.anchorY)
  sprite.position.set(x, y)
  const scale = TILE_WIDTH * zoom / TERRAIN_SPRITE.footprintWidth
  sprite.width = TERRAIN_SPRITE.width * scale
  sprite.height = TERRAIN_SPRITE.height * scale
  sprite.zIndex = sortKey
  target.sortableChildren = true
}

function isTextureReady(textureUrl: string, onChange: () => void) {
  const status = textureLoadStates.get(textureUrl)
  if (status === 'loaded') {
    return true
  }
  if (status === 'failed') {
    return false
  }
  if (status !== 'loading') {
    textureLoadStates.set(textureUrl, 'loading')
    void Assets.load(textureUrl).then(
      () => {
        textureLoadStates.set(textureUrl, 'loaded')
        onChange()
      },
      () => {
        textureLoadStates.set(textureUrl, 'failed')
        onChange()
      },
    )
  }
  return false
}

function getOrCreateSprite(target: Container, cache: RetainedChildCache, key: string, textureUrl: string) {
  const existing = cache.get(key)
  const existingSprite = existing instanceof Sprite ? existing : null
  if (existing && !existingSprite) {
    target.removeChild(existing)
    existing.destroy({ children: true })
    cache.delete(key)
  }
  if (existingSprite) {
    const tagged = existingSprite as Sprite & { textureUrl?: string }
    if (tagged.textureUrl !== textureUrl) {
      tagged.texture = Texture.from(textureUrl)
      tagged.textureUrl = textureUrl
    }
    return existingSprite
  }
  const sprite = new Sprite(Texture.from(textureUrl)) as Sprite & { textureUrl?: string }
  sprite.textureUrl = textureUrl
  cache.set(key, sprite)
  target.addChild(sprite)
  return sprite
}

function getOrCreateGraphics(target: Container, cache: RetainedChildCache, key: string) {
  const existing = cache.get(key)
  const existingGraphics = existing instanceof Graphics ? existing : null
  if (existing && !existingGraphics) {
    target.removeChild(existing)
    existing.destroy({ children: true })
    cache.delete(key)
  }
  if (existingGraphics) {
    return existingGraphics
  }
  const graphic = new Graphics()
  cache.set(key, graphic)
  target.addChild(graphic)
  return graphic
}

function getOrCreateContainer(target: Container, cache: RetainedChildCache, key: string) {
  const existing = cache.get(key)
  const existingContainer = existing instanceof Container && !(existing instanceof Sprite) && !(existing instanceof Graphics) ? existing : null
  if (existing && !existingContainer) {
    target.removeChild(existing)
    existing.destroy({ children: true })
    cache.delete(key)
  }
  if (existingContainer) {
    return existingContainer
  }
  const group = new Container()
  cache.set(key, group)
  target.addChild(group)
  return group
}

function terrainColor(tile: WorldTile) {
  return TERRAIN_COLORS[tile.terrain] ?? TERRAIN_COLORS.grass
}

function drawDiamond(target: Graphics, x: number, y: number, zoom: number, fill: number, stroke: number, strokeAlpha: number) {
  target
    .poly(TILE_POINTS.map((value, index) => (index % 2 === 0 ? x + value * zoom : y + value * zoom)), true)
    .fill({ color: fill })
    .stroke({ color: stroke, alpha: strokeAlpha, width: Math.max(1, zoom) })
}

function drawDiamondBorder(target: Graphics, x: number, y: number, zoom: number, stroke: number, strokeAlpha: number) {
  target
    .poly(TILE_POINTS.map((value, index) => (index % 2 === 0 ? x + value * zoom : y + value * zoom)), true)
    .stroke({ color: stroke, alpha: strokeAlpha, width: Math.max(1, zoom) })
}

function drawOverlay(target: Graphics, tile: TileCoord, origin: TileCoord, screenTarget: TileCoord, zoom: number, color: number, alpha: number) {
  const pos = nearestWrappedScreenCoord(tile, screenTarget)
  const x = origin.x + pos.x * zoom
  const y = origin.y + pos.y * zoom
  const points = TILE_POINTS.map((value, index) => (index % 2 === 0 ? x + value * zoom : y + value * zoom))
  target
    .poly(points, true)
    .fill({ color, alpha: Math.min(0.18, alpha * 0.18) })
    .stroke({ color, alpha, width: Math.max(2, 2 * zoom) })
  target.alpha = 1
}

function eventToTile(event: PointerEvent<HTMLDivElement> | MouseEvent<HTMLDivElement>, host: HTMLDivElement | null, camera: Camera): TileCoord | null {
  if (!host) {
    return null
  }
  const rect = host.getBoundingClientRect()
  const origin = { x: rect.width * 0.48 + camera.x, y: rect.height * 0.16 + camera.y }
  const screen = {
    x: (event.clientX - rect.left - origin.x) / camera.zoom,
    y: (event.clientY - rect.top - origin.y) / camera.zoom,
  }
  return roundGridCoord(screenToGrid(screen))
}

function eventToMapObject(
  event: PointerEvent<HTMLDivElement> | MouseEvent<HTMLDivElement>,
  host: HTMLDivElement | null,
  buildingHitAreas: readonly BuildingHitArea[],
  resourceHitAreas: readonly ResourceHitArea[],
  monsterHitAreas: readonly MonsterHitArea[],
) {
  if (!host) {
    return null
  }
  const rect = host.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  const buildingMatches = buildingHitAreas
    .filter((area) => x >= area.left && x <= area.right && y >= area.top && y <= area.bottom)
    .map((area) => ({ type: 'building' as const, building: area.building, sortKey: area.sortKey }))
  const monsterMatches = monsterHitAreas
    .filter((area) => x >= area.left && x <= area.right && y >= area.top && y <= area.bottom)
    .map((area) => ({ type: 'monster' as const, monster: area.monster, sortKey: area.sortKey }))
  const resourceMatches = resourceHitAreas
    .filter((area) => x >= area.left && x <= area.right && y >= area.top && y <= area.bottom)
    .map((area) => ({ type: 'resource' as const, node: area.node, sortKey: area.sortKey }))
  const matches = [...buildingMatches, ...resourceMatches, ...monsterMatches]
    .sort((left, right) => right.sortKey - left.sortKey)
  return matches[0] ?? null
}
