import { Landmark, Map as MapIcon, X } from '../../shared/ui/icons'
import { useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useQueryClient } from '@tanstack/react-query'

import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { cellLabel, DISTRICT_COUNT, DISTRICT_SIZE, districtFromTile, districtLabel } from '../../game/coordinates/district'
import { tileToChunk, WORLD_WRAP_TILES, wrapGridCoord } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import type { PlacedBuilding } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { useAuthStore } from '../auth/useAuthStore'
import { useOwnershipContext } from '../alliance/useOwnership'
import { visibleChunksQueryOptions } from '../world/useVisibleChunks'
import { showToast } from '../notifications/toast'

const buildingColorByKind = new Map(buildingCatalog.map((building, index) => [building.type, `hsl(${(index * 137) % 360} 72% 56%)`]))

export function MapWidget() {
  const [open, setOpen] = useState(false)
  const selectedBuildingId = useGameStore(state => state.selectedBuildingId)
  const queryClient = useQueryClient()
  const navigationRequestRef = useRef(0)
  const player = useAuthStore((state) => state.player)
  const { alliedIds } = useOwnershipContext()
  const buildings = useGameStore((state) => state.buildings)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const viewport = useGameStore((state) => state.viewport)
  const focusTile = useGameStore((state) => state.focusTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const townHall = buildings.find((building) => building.owner === player?.id && building.kind === 'town_hall' && building.status === 'active')
  const mapBuildings = buildings.filter((building) => building.owner === player?.id
    || (alliedIds.has(building.owner) && (building.kind === 'town_hall' || building.kind === 'alliance_house')))
  const activeTile = selectedTile ?? viewport.center
  const activeDistrict = districtFromTile(activeTile)
  const activeDistrictLabel = districtLabel(activeDistrict)

  async function navigateTo(tile: { x: number; y: number }, buildingId?: string) {
    const requestId = ++navigationRequestRef.current
    const startingCamera = useGameStore.getState().camera
    try {
      await queryClient.ensureQueryData(visibleChunksQueryOptions(tileToChunk(wrapGridCoord(tile)), viewport.radius))
      if (requestId !== navigationRequestRef.current || useGameStore.getState().camera !== startingCamera) return
      focusTile({ tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight })
      if (buildingId) selectBuilding(buildingId)
      setOpen(false)
    } catch {
      if (requestId === navigationRequestRef.current) showToast('warning', 'Не удалось загрузить район карты')
    }
  }

  return (
    <div className="map-widget" aria-label="Мини-карта мира">
      <IconButton
        label="К ратуше"
        icon={Landmark}
        disabled={!townHall}
        onClick={() => {
          if (!townHall) {
            return
          }
          void navigateTo(townHall.tile, townHall.id)
        }}
      />
      <IconButton label="Карта мира" icon={MapIcon} active={open} onClick={() => setOpen(!open)} />
      {open ? createPortal(
        <div className="world-map-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false) }}>
        <section className="map-widget-panel world-map-modal" aria-label="Районы мира" role="dialog" aria-modal="true">
          <header>
            <span>Карта мира</span>
            <IconButton label="Закрыть карту мира" icon={X} onClick={() => setOpen(false)} />
          </header>
          <div className="world-miniature" aria-label="25 районов мира">
            <div className="world-district-grid">
              {Array.from({ length: DISTRICT_COUNT * DISTRICT_COUNT }, (_, index) => {
                const districtX = index % DISTRICT_COUNT
                const districtY = Math.floor(index / DISTRICT_COUNT)
                const label = districtLabel({ x: districtX, y: districtY })
                const active = activeDistrict.x === districtX && activeDistrict.y === districtY
                return (
                  <button
                    aria-label={`Район ${label}`}
                    className={active ? 'world-district world-district-active' : 'world-district'}
                    key={`${districtX}:${districtY}`}
                    type="button"
                    onClick={() => void navigateTo({ x: districtX * DISTRICT_SIZE + DISTRICT_SIZE / 2, y: districtY * DISTRICT_SIZE + DISTRICT_SIZE / 2 })}
                  />
                )
              })}
            </div>
            <div
              className="world-position-marker"
              aria-label={`Текущая позиция: клетка ${cellLabel(activeTile)}`}
              style={{
                left: `${((wrappedTile(activeTile).x + 0.5) / WORLD_WRAP_TILES) * 100}%`,
                top: `${((wrappedTile(activeTile).y + 0.5) / WORLD_WRAP_TILES) * 100}%`,
              }}
            />
            <div className="world-building-markers" aria-label="Известные постройки на карте мира">
              {mapBuildings.map((building, index) => (
                <button
                  aria-label={building.name}
                  data-selected={building.id === selectedBuildingId || undefined}
                  data-owner={building.kind === 'alliance_house' && alliedIds.has(building.owner) ? 'alliance' : building.owner === player?.id ? 'own' : 'ally'}
                  className={buildingMarkerClass(building)}
                  key={building.id}
                  style={buildingMarkerStyle(building, index)}
                  title={building.name}
                  type="button"
                  onClick={() => {
                    void navigateTo(building.tile, building.id)
                  }}
                />
              ))}
            </div>
          </div>
          <footer>
            <span>{`Район ${activeDistrictLabel} · клетка ${cellLabel(activeTile)}`}</span>
          </footer>
          <small>Показаны ваши постройки и главные постройки союзников. Дом союза отмечен отдельным цветом.</small>
        </section>
        </div>, document.body,
      ) : null}
    </div>
  )
}

function buildingMarkerStyle(building: PlacedBuilding, index: number) {
  const offset = markerOffset(building, index)
  const tile = wrappedTile(building.tile)
  return {
    left: `${(tile.x / WORLD_WRAP_TILES) * 100}%`,
    top: `${(tile.y / WORLD_WRAP_TILES) * 100}%`,
    transform: `translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px))`,
    backgroundColor: building.kind === 'alliance_house' ? 'var(--color-alliance-map, #c277ff)' : buildingColorByKind.get(building.kind) ?? `hsl(${Math.abs(hashString(building.kind)) % 360} 72% 56%)`,
  }
}

function buildingMarkerClass(building: PlacedBuilding) {
  if (building.kind === 'alliance_house') return 'world-building-marker world-building-marker-alliance'
  const category = buildingCatalog.find((item) => item.type === building.kind)?.category ?? 'center'
  return `world-building-marker world-building-marker-${category}`
}

function markerOffset(building: PlacedBuilding, index: number) {
  const slot = Math.abs(hashString(building.id) + index) % 9
  const step = 5
  return {
    x: ((slot % 3) - 1) * step,
    y: (Math.floor(slot / 3) - 1) * step,
  }
}

function hashString(value: string) {
  let hash = 0
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) | 0
  }
  return hash
}

function wrappedTile(tile: { x: number; y: number }) {
  return {
    x: wrapNumber(tile.x, WORLD_WRAP_TILES),
    y: wrapNumber(tile.y, WORLD_WRAP_TILES),
  }
}

function wrapNumber(value: number, size: number) {
  return ((value % size) + size) % size
}
