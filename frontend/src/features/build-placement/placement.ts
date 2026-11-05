import type { BuildingKind, MonsterEntity, PlacedBuilding } from '../../game/state/useGameStore'
import type { TerrainType, WorldTile } from '../../shared/contracts'
import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { normalizeTile } from '../../../../shared/world/coordinates'

const buildingFootprints = new Map<string, { width: number; height: number }>(buildingCatalog.map((item) => [item.type, item.footprint]))
const trapKinds = new Set<BuildingKind>(['defense_stakes', 'defense_resin_snare'])
const roadKinds = new Set<BuildingKind>(['road', 'standard_road', 'paved_road'])

export type PlacementPreview = {
  valid: boolean
  reason: string | null
}

export function validatePlacementPreview(input: {
  kind: BuildingKind
  tile: { x: number; y: number } | null
  terrain?: TerrainType | null
  footprint?: { width: number; height: number }
  worldTiles?: WorldTile[]
  buildings: PlacedBuilding[]
  ownerId?: string | null
  monsters?: MonsterEntity[]
  ignoreBuildingId?: string
  skipTownHallCheck?: boolean
}): PlacementPreview {
  if (!input.tile) {
    return { valid: false, reason: 'Выберите клетку на карте' }
  }
  const catalogFootprint = buildingFootprints.get(input.kind)
  if (isMultiTileFootprint(catalogFootprint) || isMultiTileFootprint(input.footprint)) {
    return { valid: false, reason: 'Постройки больше одной клетки нельзя размещать или перемещать' }
  }
  const ownerBuildings = input.ownerId ? input.buildings.filter((building) => building.owner === input.ownerId) : input.buildings
  const hasTownHall = ownerBuildings.some((building) => building.kind === 'town_hall')
  if (!input.skipTownHallCheck && input.kind !== 'town_hall' && !hasTownHall) {
    return { valid: false, reason: 'Сначала нужна ратуша' }
  }
  if (!input.skipTownHallCheck && input.kind === 'town_hall' && hasTownHall) {
    return { valid: false, reason: 'Ратуша может быть только одна' }
  }
  const footprint = footprintTiles(input.tile)
  if (input.buildings.some((building) => {
    if (building.id === input.ignoreBuildingId) return false
    if (building.state === 'ruined') return false
    if ((trapKinds.has(input.kind) && roadKinds.has(building.kind)) || (roadKinds.has(input.kind) && trapKinds.has(building.kind))) return false
    const occupied = buildingFootprints.get(building.kind)
    return footprint.some((tile) => footprintTiles(building.tile, { width: building.footprintW ?? occupied?.width ?? 1,
      height: building.footprintH ?? occupied?.height ?? 1 }).some((other) => other.x === tile.x && other.y === tile.y))
  })) {
    return { valid: false, reason: 'Клетка уже занята' }
  }
  if (input.monsters?.some((monster) => footprint.some((tile) => tile.x === monster.tile.x && tile.y === monster.tile.y))) {
    return { valid: false, reason: 'На клетке находится монстр' }
  }
  const terrainTiles = footprint.map((coord) => input.worldTiles?.find((tile) => tile.x === coord.x && tile.y === coord.y)?.terrain ?? (coord.x === input.tile?.x && coord.y === input.tile.y ? input.terrain : null))
  if (terrainTiles.some((terrain) => terrain === 'forest')) {
    return { valid: false, reason: 'Сначала срубите лес на этой клетке' }
  }
  if (terrainTiles.some((terrain) => terrain === 'water' || terrain === 'mountain')) {
    return { valid: false, reason: 'На реках и горах строить нельзя' }
  }
  if (terrainTiles.some((terrain) => terrain === 'ruins')) {
    return { valid: false, reason: 'На руинах и нефтяных скважинах строить нельзя' }
  }
  if (input.kind === 'oil_well') {
    if (terrainTiles.some((terrain) => terrain !== 'oil_well')) {
      return { valid: false, reason: 'Нефтяную вышку можно строить только на нефтяной скважине' }
    }
    return { valid: true, reason: null }
  }
  if (terrainTiles.some((terrain) => terrain === 'oil_well')) {
    return { valid: false, reason: 'На руинах и нефтяных скважинах строить нельзя' }
  }
  return { valid: true, reason: null }
}

function isMultiTileFootprint(footprint?: { width: number; height: number }) {
  return Math.max(1, footprint?.width ?? 1) * Math.max(1, footprint?.height ?? 1) > 1
}

function footprintTiles(origin: { x: number; y: number }, footprint: { width: number; height: number } = { width: 1, height: 1 }) {
  const width = Math.max(1, footprint.width)
  const height = Math.max(1, footprint.height)
  const tiles: { x: number; y: number }[] = []
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      tiles.push(normalizeTile({ x: origin.x + x, y: origin.y + y }))
    }
  }
  return tiles
}
