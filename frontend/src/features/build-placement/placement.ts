import type { BuildingKind, MonsterEntity, PlacedBuilding } from '../../game/state/useGameStore'
import type { TerrainType, WorldTile } from '../../shared/contracts'

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
  monsters?: MonsterEntity[]
}): PlacementPreview {
  if (!input.tile) {
    return { valid: false, reason: 'Выберите клетку на карте' }
  }
  const hasTownHall = input.buildings.some((building) => building.kind === 'town_hall')
  if (input.kind !== 'town_hall' && !hasTownHall) {
    return { valid: false, reason: 'Сначала нужна ратуша' }
  }
  if (input.kind === 'town_hall' && hasTownHall) {
    return { valid: false, reason: 'Ратуша может быть только одна' }
  }
  const footprint = footprintTiles(input.tile, input.footprint)
  if (input.buildings.some((building) => footprint.some((tile) => tile.x === building.tile.x && tile.y === building.tile.y))) {
    return { valid: false, reason: 'Клетка уже занята' }
  }
  if (input.monsters?.some((monster) => footprint.some((tile) => tile.x === monster.tile.x && tile.y === monster.tile.y))) {
    return { valid: false, reason: 'На клетке находится монстр' }
  }
  const terrainTiles = footprint.map((coord) => input.worldTiles?.find((tile) => tile.x === coord.x && tile.y === coord.y)?.terrain ?? (coord.x === input.tile?.x && coord.y === input.tile.y ? input.terrain : null))
  if (terrainTiles.some((terrain) => terrain === 'forest')) {
    return { valid: false, reason: isMultiTileFootprint(input.footprint) ? 'Сначала срубите лес на клетках под постройкой' : 'Сначала срубите лес на этой клетке' }
  }
  if (terrainTiles.some((terrain) => terrain === 'water' || terrain === 'mountain')) {
    return { valid: false, reason: 'На реках и горах строить нельзя' }
  }
  if (terrainTiles.some((terrain) => terrain === 'ruins' || terrain === 'oil_well')) {
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
      tiles.push({ x: origin.x + x, y: origin.y + y })
    }
  }
  return tiles
}
