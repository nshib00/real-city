import { Landmark, Map as MapIcon, X } from '../../shared/ui/icons'
import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { cellLabel, DISTRICT_COUNT, DISTRICT_SIZE, districtFromTile, districtLabel } from '../../game/coordinates/district'
import { tileToChunk, WORLD_WRAP_TILES, wrapGridCoord } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import type { PlacedBuilding } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { useAuthStore } from '../auth/useAuthStore'
import { visibleChunksQueryOptions } from '../world/useVisibleChunks'
import { showToast } from '../notifications/toast'

const buildingColorByKind = new Map(buildingCatalog.map((building, index) => [building.type, `hsl(${(index * 137) % 360} 72% 56%)`]))

export function MapWidget() {
  const [open, setOpen] = useState(false)
  const selectedBuildingId = useGameStore(state => state.selectedBuildingId)
  const queryClient = useQueryClient()
  const navigationRequestRef = useRef(0)
  const player = useAuthStore((state) => state.player)
  const buildings = useGameStore((state) => state.buildings)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const viewport = useGameStore((state) => state.viewport)
  const focusTile = useGameStore((state) => state.focusTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const townHall = buildings.find((building) => building.owner === player?.id && building.kind === 'town_hall' && building.status === 'active')
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
      {open ? (
        <section className="map-widget-panel" aria-label="Районы мира">
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
            <div className="world-building-markers" aria-label="Известные постройки на карте мира">
              {buildings.map((building, index) => (
                <button
                  aria-label={building.name}
                  data-selected={building.id === selectedBuildingId || undefined}
                  className="world-building-marker"
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
          <small>Каждый тип построек отмечен своим цветом. Показаны загруженные постройки мира.</small>
        </section>
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
    backgroundColor: buildingColorByKind.get(building.kind) ?? `hsl(${Math.abs(hashString(building.kind)) % 360} 72% 56%)`,
  }
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
