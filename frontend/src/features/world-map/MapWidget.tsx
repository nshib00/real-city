import { Landmark, Map as MapIcon, X } from 'lucide-react'
import { useState } from 'react'
import type { PointerEvent } from 'react'

import { buildingCatalog } from '../../../../shared/catalog/buildings'
import type { BuildingCatalogItem } from '../../../../shared/catalog/buildings'
import { WORLD_WRAP_TILES } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'

const DISTRICT_COUNT = 5
const DISTRICT_SIZE = WORLD_WRAP_TILES / DISTRICT_COUNT
const buildingCategoryByKind = new Map(buildingCatalog.map((item) => [item.type, item.category]))

type BuildingCategory = BuildingCatalogItem['category']

const markerClassByCategory: Record<BuildingCategory, string> = {
  center: 'world-building-marker-center',
  housing: 'world-building-marker-housing',
  fields: 'world-building-marker-fields',
  industry: 'world-building-marker-industry',
  defense: 'world-building-marker-defense',
  roads: 'world-building-marker-roads',
  storage: 'world-building-marker-storage',
  social: 'world-building-marker-social',
  trade: 'world-building-marker-trade',
}

export function MapWidget() {
  const [open, setOpen] = useState(false)
  const buildings = useGameStore((state) => state.buildings)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const viewport = useGameStore((state) => state.viewport)
  const focusTile = useGameStore((state) => state.focusTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const townHall = buildings.find((building) => building.kind === 'town_hall' && building.status === 'active')

  return (
    <aside className="map-widget" aria-label="Мини-карта мира">
      <IconButton
        label="К ратуше"
        icon={Landmark}
        disabled={!townHall}
        onClick={() => {
          if (!townHall) {
            return
          }
          focusTile({ tile: townHall.tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight })
          selectBuilding(townHall.id)
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
                const active = selectedTile ? tileInDistrict(selectedTile, districtX, districtY) : tileInDistrict(viewport.center, districtX, districtY)
                return (
                  <button
                    aria-label={`Район ${districtX + 1}:${districtY + 1}`}
                    className={active ? 'world-district world-district-active' : 'world-district'}
                    key={`${districtX}:${districtY}`}
                    type="button"
                    onPointerDown={(event) => {
                      const tile = tileFromDistrictClick(event, districtX, districtY)
                      focusTile({ tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight })
                      setOpen(false)
                    }}
                  />
                )
              })}
            </div>
            <div className="world-building-markers" aria-label="Постройки игрока на карте мира">
              {buildings.map((building, index) => (
                <button
                  aria-label={building.name}
                  className={`world-building-marker ${markerClassByCategory[buildingCategory(building.kind)]}`}
                  key={building.id}
                  style={buildingMarkerStyle(building, index)}
                  title={building.name}
                  type="button"
                  onClick={() => {
                    focusTile({ tile: building.tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight })
                    selectBuilding(building.id)
                    setOpen(false)
                  }}
                />
              ))}
            </div>
          </div>
          <footer>
            <span>{selectedTile ? `${selectedTile.x}:${selectedTile.y}` : `${viewport.center.x}:${viewport.center.y}`}</span>
          </footer>
        </section>
      ) : null}
    </aside>
  )
}

function buildingCategory(kind: BuildingKind) {
  return buildingCategoryByKind.get(kind) ?? 'center'
}

function buildingMarkerStyle(building: PlacedBuilding, index: number) {
  const offset = markerOffset(building, index)
  return {
    left: `${(building.tile.x / WORLD_WRAP_TILES) * 100}%`,
    top: `${(building.tile.y / WORLD_WRAP_TILES) * 100}%`,
    transform: `translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px))`,
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

function tileInDistrict(tile: { x: number; y: number }, districtX: number, districtY: number) {
  return Math.floor(tile.x / DISTRICT_SIZE) === districtX && Math.floor(tile.y / DISTRICT_SIZE) === districtY
}

function tileFromDistrictClick(event: PointerEvent<HTMLButtonElement>, districtX: number, districtY: number) {
  const rect = event.currentTarget.getBoundingClientRect()
  const localX = clamp((event.clientX - rect.left) / rect.width, 0, 0.999)
  const localY = clamp((event.clientY - rect.top) / rect.height, 0, 0.999)
  return {
    x: Math.floor(districtX * DISTRICT_SIZE + localX * DISTRICT_SIZE),
    y: Math.floor(districtY * DISTRICT_SIZE + localY * DISTRICT_SIZE),
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}
