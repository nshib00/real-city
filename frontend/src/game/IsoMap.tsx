import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { flattenChunkTiles, useVisibleChunks } from '../features/world/useVisibleChunks'
import { canChopForestTile } from '../features/world/forestActions'
import { gridToScreen, nearestWrappedScreenCoord, roundGridCoord, screenToGrid, tileToChunk, wrapGridCoord } from './coordinates/iso'
import { PixiStage } from './renderer/PixiStage'
import { filterVisibleMapObjects, isMapObjectVisible, occupiedTileKeys } from './renderer/visibleObjects'
import { DugoutModel } from './renderers/DugoutModel'
import { LumberYardModel } from './renderers/LumberYardModel'
import { TownHallModel } from './renderers/TownHallModel'
import { WindleafBedModel } from './renderers/WindleafBedModel'
import { WoodHouseModel } from './renderers/WoodHouseModel'
import { monsterClassName, monsterLabel } from './renderers/monsters'
import { resourceNodeClassName, resourceNodeLabel } from './renderers/resources'
import { useGameStore } from './state/useGameStore'
import { chopForest } from '../shared/api/world'

export function IsoMap() {
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const camera = useGameStore((state) => state.camera)
  const viewport = useGameStore((state) => state.viewport)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const monsters = useGameStore((state) => state.monsters)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const selectedMonsterId = useGameStore((state) => state.selectedMonsterId)
  const selectTile = useGameStore((state) => state.selectTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const selectMonster = useGameStore((state) => state.selectMonster)
  const hoverTile = useGameStore((state) => state.hoverTile)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const setWorldTiles = useGameStore((state) => state.setWorldTiles)
  const updateWorldTile = useGameStore((state) => state.updateWorldTile)
  const panCamera = useGameStore((state) => state.panCamera)
  const setZoom = useGameStore((state) => state.setZoom)
  const setViewportCenter = useGameStore((state) => state.setViewportCenter)
  const queryClient = useQueryClient()
  const mapStageRef = useRef<HTMLElement | null>(null)
  const dragStart = useRef<{ x: number; y: number } | null>(null)
  const pendingDragRef = useRef<{ screen: { x: number; y: number }; grid: { x: number; y: number } } | null>(null)
  const dragFrameRef = useRef<number | null>(null)
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 })
  const viewportCenterRef = useRef(viewport.center)
  const centerChunk = useMemo(() => tileToChunk(wrapGridCoord(viewport.center)), [viewport.center])
  const chunksQuery = useVisibleChunks(centerChunk, 1)
  const tiles = useMemo(() => flattenChunkTiles(chunksQuery.data?.chunks), [chunksQuery.data?.chunks])
  const mapTiles = worldTiles.length > 0 ? worldTiles : tiles
  const visibilityOptions = useMemo(
    () => ({ camera, viewportCenter: viewport.center, viewportSize: stageSize }),
    [camera, stageSize, viewport.center],
  )
  const visibleBuildings = useMemo(() => filterVisibleMapObjects(buildings, visibilityOptions), [buildings, visibilityOptions])
  const buildingOccupiedTiles = useMemo(() => occupiedTileKeys(buildings.filter(hasFullCellSprite)), [buildings])
  const visibleResourceNodes = useMemo(() => filterVisibleMapObjects(resourceNodes, visibilityOptions), [resourceNodes, visibilityOptions])
  const visibleMonsters = useMemo(() => filterVisibleMapObjects(monsters, visibilityOptions), [monsters, visibilityOptions])
  const showDebugResource = isMapObjectVisible({ x: -5, y: 6 }, visibilityOptions)
  const chopMutation = useMutation({
    mutationFn: chopForest,
    onSuccess: (result) => {
      updateWorldTile(result.tile)
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      void queryClient.invalidateQueries({ queryKey: ['world'] })
    },
  })

  function handleSelectTile(tile: { x: number; y: number }) {
    const worldTile = mapTiles.find((item) => item.x === tile.x && item.y === tile.y)
    if (canChopForestTile(worldTile) && !chopMutation.isPending) {
      selectTile(tile)
      chopMutation.mutate({ x: tile.x, y: tile.y })
      return
    }
    selectTile(tile)
  }

  function flushDragFrame() {
    if (dragFrameRef.current !== null) {
      cancelAnimationFrame(dragFrameRef.current)
      dragFrameRef.current = null
    }
    const pending = pendingDragRef.current
    pendingDragRef.current = null
    if (!pending) {
      return
    }

    viewportCenterRef.current = wrapGridCoord({
      x: viewportCenterRef.current.x + pending.grid.x,
      y: viewportCenterRef.current.y + pending.grid.y,
    })
    setViewportCenter(roundGridCoord(viewportCenterRef.current))
    panCamera(pending.screen)
  }

  function scheduleDragFrame(delta: { x: number; y: number }) {
    const gridDelta = screenToGrid({ x: -delta.x / camera.zoom, y: -delta.y / camera.zoom })
    pendingDragRef.current = pendingDragRef.current
      ? {
          screen: {
            x: pendingDragRef.current.screen.x + delta.x,
            y: pendingDragRef.current.screen.y + delta.y,
          },
          grid: {
            x: pendingDragRef.current.grid.x + gridDelta.x,
            y: pendingDragRef.current.grid.y + gridDelta.y,
          },
        }
      : { screen: delta, grid: gridDelta }

    if (dragFrameRef.current === null) {
      dragFrameRef.current = requestAnimationFrame(flushDragFrame)
    }
  }

  useEffect(() => {
    if (!dragStart.current) {
      viewportCenterRef.current = viewport.center
    }
  }, [viewport.center])

  useEffect(() => {
    return () => {
      if (dragFrameRef.current !== null) {
        cancelAnimationFrame(dragFrameRef.current)
      }
    }
  }, [])

  useEffect(() => {
    setWorldTiles(tiles)
  }, [setWorldTiles, tiles])

  useEffect(() => {
    const element = mapStageRef.current
    if (!element || typeof ResizeObserver === 'undefined') {
      return
    }

    const observer = new ResizeObserver(([entry]) => {
      const width = entry.contentRect.width
      const height = entry.contentRect.height
      setStageSize((current) => (current.width === width && current.height === height ? current : { width, height }))
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return (
    <section
      className="map-stage"
      ref={mapStageRef}
      aria-label="Карта"
      onPointerDown={(event) => {
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerMove={(event) => {
        if (!dragStart.current || event.buttons !== 1) {
          return
        }
        const delta = { x: event.clientX - dragStart.current.x, y: event.clientY - dragStart.current.y }
        scheduleDragFrame(delta)
        dragStart.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerUp={() => {
        flushDragFrame()
        dragStart.current = null
      }}
      onPointerCancel={() => {
        flushDragFrame()
        dragStart.current = null
      }}
      onWheel={(event) => {
        event.preventDefault()
        setZoom(camera.zoom + (event.deltaY > 0 ? -0.08 : 0.08))
      }}
    >
      <PixiStage
        tiles={mapTiles}
        occupiedTiles={buildingOccupiedTiles}
        camera={camera}
        selectedTile={selectedTile}
        hoveredTile={hoveredTile}
        onSelectTile={handleSelectTile}
        onHoverTile={hoverTile}
      />
      <div
        className="map-origin"
        style={{
          transform: `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})`,
        }}
      >
        {visibleBuildings.map((building) => (
          <MapObject
            key={building.id}
            id={building.id}
            x={building.tile.x}
            y={building.tile.y}
            viewportCenter={viewport.center}
            className={`map-building map-building-${building.kind} ${building.status === 'construction' ? 'map-building-construction' : ''} ${selectedBuildingId === building.id ? 'map-building-selected' : ''}`}
            label={building.name}
            onSelect={() => selectBuilding(building.id)}
          >
            {building.kind === 'town_hall' ? <TownHallModel building={building} /> : null}
            {building.kind === 'dugout' ? <DugoutModel building={building} /> : null}
            {building.kind === 'wood_house' ? <WoodHouseModel building={building} /> : null}
            {building.kind === 'lumber_yard' ? <LumberYardModel building={building} /> : null}
            {building.kind === 'field_bed' ? <WindleafBedModel building={building} /> : null}
            {building.status === 'construction' && building.completesAt ? <span className="construction-timer">{formatRemaining(building.completesAt - constructionNow)}</span> : null}
          </MapObject>
        ))}
        {visibleResourceNodes.map((node) => (
          <MapObject
            key={node.id}
            id={node.id}
            x={node.tile.x}
            y={node.tile.y}
            viewportCenter={viewport.center}
            className={resourceNodeClassName(node)}
            label={resourceNodeLabel(node)}
          />
        ))}
        {visibleMonsters.map((monster) => (
          <MapObject
            key={monster.id}
            id={monster.id}
            x={monster.tile.x}
            y={monster.tile.y}
            viewportCenter={viewport.center}
            className={`${monsterClassName(monster)} ${selectedMonsterId === monster.id ? 'map-monster-selected' : ''}`}
            label={monsterLabel(monster)}
            onSelect={() => selectMonster(monster.id)}
          >
            <span className="monster-health" style={{ transform: `scaleX(${Math.max(0, Math.min(1, monster.health / monster.maxHealth))})` }} />
          </MapObject>
        ))}
        {showDebugResource ? <MapObject id="resource-wood" x={-5} y={6} viewportCenter={viewport.center} className="map-resource" /> : null}
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
  viewportCenter,
}: {
  id: string
  x: number
  y: number
  className: string
  label?: string
  onSelect?: () => void
  children?: ReactNode
  viewportCenter: { x: number; y: number }
}) {
  const pos = nearestWrappedScreenCoord({ x, y }, gridToScreen(viewportCenter))
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

function hasFullCellSprite(building: { kind: string }) {
  return building.kind === 'town_hall' || building.kind === 'dugout' || building.kind === 'wood_house' || building.kind === 'lumber_yard'
}
