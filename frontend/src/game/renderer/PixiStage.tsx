import { Application, Container, Graphics, Sprite, Texture } from 'pixi.js'
import { useEffect, useRef } from 'react'
import type { MouseEvent, PointerEvent } from 'react'

import type { WorldTile } from '../../shared/contracts'
import { nearestWrappedScreenCoord, roundGridCoord, screenToGrid, TILE_HEIGHT, TILE_WIDTH, wrapGridCoord } from '../coordinates/iso'
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
  camera: Camera
  selectedTile: TileCoord | null
  hoveredTile: TileCoord | null
  onSelectTile: (tile: TileCoord) => void
  onHoverTile: (tile: TileCoord | null) => void
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

export function PixiStage({ tiles, occupiedTiles, camera, selectedTile, hoveredTile, onSelectTile, onHoverTile }: PixiStageProps) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const appRef = useRef<Application | null>(null)
  const terrainSpritesRef = useRef<Container | null>(null)
  const terrainRef = useRef<Graphics | null>(null)
  const overlayRef = useRef<Graphics | null>(null)
  const tilesRef = useRef<WorldTile[]>(tiles)
  const occupiedTilesRef = useRef<Set<string>>(occupiedTiles)
  const cameraRef = useRef<Camera>(camera)
  const selectedTileRef = useRef<TileCoord | null>(selectedTile)
  const hoveredTileRef = useRef<TileCoord | null>(hoveredTile)

  useEffect(() => {
    let app: Application | null = null
    let disposed = false

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
      app.ticker.maxFPS = 30
      terrainSpritesRef.current = new Container()
      terrainRef.current = new Graphics()
      overlayRef.current = new Graphics()
      app.stage.addChild(terrainSpritesRef.current)
      app.stage.addChild(terrainRef.current)
      app.stage.addChild(overlayRef.current)
      hostRef.current.appendChild(app.canvas)
      drawStage(
        nextApp,
        terrainSpritesRef.current,
        terrainRef.current,
        overlayRef.current,
        tilesRef.current,
        occupiedTilesRef.current,
        cameraRef.current,
        selectedTileRef.current,
        hoveredTileRef.current,
      )
      void preloadTerrainPngTextures().then(() => {
        if (!disposed && terrainSpritesRef.current && terrainRef.current && overlayRef.current) {
          drawStage(
            nextApp,
            terrainSpritesRef.current,
            terrainRef.current,
            overlayRef.current,
            tilesRef.current,
            occupiedTilesRef.current,
            cameraRef.current,
            selectedTileRef.current,
            hoveredTileRef.current,
          )
        }
      })
    }

    void mount()

    return () => {
      disposed = true
      app?.destroy()
      appRef.current = null
      terrainSpritesRef.current = null
      terrainRef.current = null
      overlayRef.current = null
      app = null
    }
  }, [])

  useEffect(() => {
    tilesRef.current = tiles
    occupiedTilesRef.current = occupiedTiles
    cameraRef.current = camera
    selectedTileRef.current = selectedTile
    hoveredTileRef.current = hoveredTile
    const app = appRef.current
    const terrainSprites = terrainSpritesRef.current
    const terrain = terrainRef.current
    const overlay = overlayRef.current
    if (app && terrainSprites && terrain && overlay) {
      drawStage(app, terrainSprites, terrain, overlay, tiles, occupiedTiles, camera, selectedTile, hoveredTile)
    }
  }, [camera, hoveredTile, occupiedTiles, selectedTile, tiles])

  return (
    <div
      className="pixi-stage"
      ref={hostRef}
      role="presentation"
      onClick={(event) => {
        const tile = eventToTile(event, hostRef.current, cameraRef.current)
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
  terrain: Graphics,
  overlay: Graphics,
  tiles: WorldTile[],
  occupiedTiles: Set<string>,
  camera: Camera,
  selectedTile: TileCoord | null,
  hoveredTile: TileCoord | null,
) {
  const width = app.screen.width
  const height = app.screen.height
  const origin = { x: width * 0.48 + camera.x, y: height * 0.16 + camera.y }
  const screenTarget = { x: (width / 2 - origin.x) / camera.zoom, y: (height / 2 - origin.y) / camera.zoom }
  for (const child of terrainSprites.removeChildren()) {
    child.destroy()
  }
  terrain.clear()
  overlay.clear()

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

  visibleTiles.sort((a, b) => a.y - b.y || a.x - b.x)
  for (const { tile, x, y } of visibleTiles) {
    if (occupiedTiles.has(tileOccupancyKey(tile))) {
      continue
    }
    const textureUrl = terrainTextureUrl(tile)
    if (textureUrl) {
      drawTerrainSprite(terrainSprites, textureUrl, x, y, camera.zoom)
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
}

function drawTerrainSprite(target: Container, textureUrl: string, x: number, y: number, zoom: number) {
  const sprite = new Sprite(Texture.from(textureUrl))
  sprite.anchor.set(TERRAIN_SPRITE.anchorX, TERRAIN_SPRITE.anchorY)
  sprite.position.set(x, y)
  const scale = TILE_WIDTH * zoom / TERRAIN_SPRITE.footprintWidth
  sprite.width = TERRAIN_SPRITE.width * scale
  sprite.height = TERRAIN_SPRITE.height * scale
  target.addChild(sprite)
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
  drawDiamond(target, origin.x + pos.x * zoom, origin.y + pos.y * zoom, zoom, color, color, alpha)
  target.alpha = alpha
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
  return wrapGridCoord(roundGridCoord(screenToGrid(screen)))
}
