import { Application, Graphics } from 'pixi.js'
import { useEffect, useRef } from 'react'
import type { MouseEvent, PointerEvent } from 'react'

import type { WorldTile } from '../../shared/contracts'
import { nearestWrappedScreenCoord, roundGridCoord, screenToGrid, TILE_HEIGHT, TILE_WIDTH, wrapGridCoord } from '../coordinates/iso'

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

export function PixiStage({ tiles, camera, selectedTile, hoveredTile, onSelectTile, onHoverTile }: PixiStageProps) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const appRef = useRef<Application | null>(null)
  const terrainRef = useRef<Graphics | null>(null)
  const overlayRef = useRef<Graphics | null>(null)
  const tilesRef = useRef<WorldTile[]>(tiles)
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
      terrainRef.current = new Graphics()
      overlayRef.current = new Graphics()
      app.stage.addChild(terrainRef.current)
      app.stage.addChild(overlayRef.current)
      hostRef.current.appendChild(app.canvas)
      drawStage(nextApp, terrainRef.current, overlayRef.current, tilesRef.current, cameraRef.current, selectedTileRef.current, hoveredTileRef.current)
    }

    void mount()

    return () => {
      disposed = true
      app?.destroy()
      appRef.current = null
      terrainRef.current = null
      overlayRef.current = null
      app = null
    }
  }, [])

  useEffect(() => {
    tilesRef.current = tiles
    cameraRef.current = camera
    selectedTileRef.current = selectedTile
    hoveredTileRef.current = hoveredTile
    const app = appRef.current
    const terrain = terrainRef.current
    const overlay = overlayRef.current
    if (app && terrain && overlay) {
      drawStage(app, terrain, overlay, tiles, camera, selectedTile, hoveredTile)
    }
  }, [camera, hoveredTile, selectedTile, tiles])

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

function drawStage(app: Application, terrain: Graphics, overlay: Graphics, tiles: WorldTile[], camera: Camera, selectedTile: TileCoord | null, hoveredTile: TileCoord | null) {
  const width = app.screen.width
  const height = app.screen.height
  const origin = { x: width * 0.48 + camera.x, y: height * 0.16 + camera.y }
  const screenTarget = { x: (width / 2 - origin.x) / camera.zoom, y: (height / 2 - origin.y) / camera.zoom }
  terrain.clear()
  overlay.clear()

  for (const tile of tiles) {
    const pos = nearestWrappedScreenCoord(tile, screenTarget)
    const x = origin.x + pos.x * camera.zoom
    const y = origin.y + pos.y * camera.zoom
    const halfWidth = (TILE_WIDTH * camera.zoom) / 2
    const halfHeight = (TILE_HEIGHT * camera.zoom) / 2
    if (x + halfWidth < 0 || x - halfWidth > width || y + halfHeight < 0 || y - halfHeight > height) {
      continue
    }
    drawDiamond(terrain, x, y, camera.zoom, terrainColor(tile), tile.safe_zone ? 0xf2c14e : 0xffffff, tile.safe_zone ? 0.42 : 0.18)
    if (tile.terrain === 'forest' && tile.forest_density > 0) {
      drawForestCluster(terrain, x, y, camera.zoom, tile.forest_density)
    }
    if (tile.terrain === 'ruins') {
      drawRuinsMarker(terrain, x, y, camera.zoom)
    }
  }

  if (hoveredTile) {
    drawOverlay(overlay, hoveredTile, origin, screenTarget, camera.zoom, 0xffffff, 0.36)
  }
  if (selectedTile) {
    drawOverlay(overlay, selectedTile, origin, screenTarget, camera.zoom, 0xf2c14e, 0.9)
  }
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

function drawForestCluster(target: Graphics, x: number, y: number, zoom: number, density: number) {
  const count = Math.max(1, Math.min(3, density))
  const trees = [
    { x: 0, y: -11 },
    { x: -14, y: -2 },
    { x: 14, y: -2 },
  ].slice(0, count)
  for (const tree of trees) {
    const trunkWidth = 4 * zoom
    const trunkHeight = 9 * zoom
    const crownRadius = 9 * zoom
    const tx = x + tree.x * zoom
    const ty = y + tree.y * zoom
    target.rect(tx - trunkWidth / 2, ty + 4 * zoom, trunkWidth, trunkHeight).fill({ color: 0x5b3a24 })
    target.circle(tx, ty, crownRadius).fill({ color: count === 1 ? 0x6faa55 : 0x255f3f })
    target.circle(tx - 5 * zoom, ty + 3 * zoom, crownRadius * 0.65).fill({ color: 0x2f7449 })
  }
}

function drawRuinsMarker(target: Graphics, x: number, y: number, zoom: number) {
  const block = 9 * zoom
  target.rect(x - 16 * zoom, y - 8 * zoom, block, 18 * zoom).fill({ color: 0xc9b06a })
  target.rect(x - 4 * zoom, y - 14 * zoom, block, 24 * zoom).fill({ color: 0xd7c07a })
  target.rect(x + 9 * zoom, y - 6 * zoom, block, 16 * zoom).fill({ color: 0xb99b58 })
  target.circle(x, y - 19 * zoom, 4 * zoom).fill({ color: 0xf2c14e })
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
