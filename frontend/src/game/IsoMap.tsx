import { useEffect, useMemo, useRef } from 'react'
import type { ReactNode } from 'react'

import { flattenChunkTiles, useVisibleChunks } from '../features/world/useVisibleChunks'
import { gridToScreen, roundGridCoord, screenToGrid, tileToChunk, wrapGridCoord } from './coordinates/iso'
import { PixiStage } from './renderer/PixiStage'
import { resourceNodeClassName, resourceNodeLabel } from './renderers/resources'
import { useGameStore } from './state/useGameStore'

export function IsoMap() {
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const camera = useGameStore((state) => state.camera)
  const viewport = useGameStore((state) => state.viewport)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const selectTile = useGameStore((state) => state.selectTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const hoverTile = useGameStore((state) => state.hoverTile)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const setWorldTiles = useGameStore((state) => state.setWorldTiles)
  const panCamera = useGameStore((state) => state.panCamera)
  const setZoom = useGameStore((state) => state.setZoom)
  const setViewportCenter = useGameStore((state) => state.setViewportCenter)
  const dragStart = useRef<{ x: number; y: number } | null>(null)
  const viewportCenterRef = useRef(viewport.center)
  const centerChunk = useMemo(() => tileToChunk(wrapGridCoord(viewport.center)), [viewport.center])
  const chunksQuery = useVisibleChunks(centerChunk, 1)
  const tiles = useMemo(() => flattenChunkTiles(chunksQuery.data?.chunks), [chunksQuery.data?.chunks])

  useEffect(() => {
    if (!dragStart.current) {
      viewportCenterRef.current = viewport.center
    }
  }, [viewport.center])

  useEffect(() => {
    setWorldTiles(tiles)
  }, [setWorldTiles, tiles])

  return (
    <section
      className="map-stage"
      aria-label="Карта"
      onPointerDown={(event) => {
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerMove={(event) => {
        if (!dragStart.current || event.buttons !== 1) {
          return
        }
        const delta = { x: event.clientX - dragStart.current.x, y: event.clientY - dragStart.current.y }
        const tileDelta = screenToGrid({ x: -delta.x / camera.zoom, y: -delta.y / camera.zoom })
        viewportCenterRef.current = wrapGridCoord({
          x: viewportCenterRef.current.x + tileDelta.x,
          y: viewportCenterRef.current.y + tileDelta.y,
        })
        setViewportCenter(roundGridCoord(viewportCenterRef.current))
        panCamera(delta)
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerUp={() => {
        dragStart.current = null
      }}
      onPointerCancel={() => {
        dragStart.current = null
      }}
      onWheel={(event) => {
        event.preventDefault()
        setZoom(camera.zoom + (event.deltaY > 0 ? -0.08 : 0.08))
      }}
    >
      <PixiStage tiles={worldTiles.length > 0 ? worldTiles : tiles} camera={camera} selectedTile={selectedTile} hoveredTile={hoveredTile} onSelectTile={selectTile} onHoverTile={hoverTile} />
      <div
        className="map-origin"
        style={{
          transform: `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})`,
        }}
      >
        {buildings.map((building) => (
          <MapObject
            key={building.id}
            id={building.id}
            x={building.tile.x}
            y={building.tile.y}
            className={`map-building map-building-${building.kind} ${building.status === 'construction' ? 'map-building-construction' : ''} ${selectedBuildingId === building.id ? 'map-building-selected' : ''}`}
            label={building.name}
            onSelect={() => selectBuilding(building.id)}
          >
            {building.status === 'construction' && building.completesAt ? <span className="construction-timer">{formatRemaining(building.completesAt - constructionNow)}</span> : null}
          </MapObject>
        ))}
        {resourceNodes.map((node) => (
          <MapObject
            key={node.id}
            id={node.id}
            x={node.tile.x}
            y={node.tile.y}
            className={resourceNodeClassName(node)}
            label={resourceNodeLabel(node)}
          />
        ))}
        <MapObject id="resource-wood" x={-5} y={6} className="map-resource" />
        <MapObject id="threat" x={9} y={-4} className="map-threat" />
      </div>
      <div className="map-debug" aria-live="polite">
        <span>chunk {centerChunk.x}:{centerChunk.y}</span>
        <span>zoom {camera.zoom.toFixed(2)}</span>
        <span>{chunksQuery.isFetching ? 'loading' : `${tiles.length} tiles`}</span>
      </div>
    </section>
  )
}

function MapObject({
  id,
  x,
  y,
  className,
  label,
  onSelect,
  children,
}: {
  id: string
  x: number
  y: number
  className: string
  label?: string
  onSelect?: () => void
  children?: ReactNode
}) {
  const pos = gridToScreen({ x, y })
  return (
    <button
      className={className}
      key={id}
      type="button"
      title={label}
      aria-label={label ?? id}
      style={{ transform: `translate(${pos.x}px, ${pos.y - 30}px)` }}
      onClick={(event) => {
        event.stopPropagation()
        onSelect?.()
      }}
    >
      {children}
    </button>
  )
}

function formatRemaining(ms: number) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}
