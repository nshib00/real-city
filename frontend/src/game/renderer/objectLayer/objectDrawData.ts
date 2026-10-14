import type { PlacedBuilding } from '../../state/useGameStore'
import { buildingRegistryEntry, resolveBuildingSpriteAsset } from '../../renderers/buildingRegistry'
import { isModularPathKind, modularPathShapeFor } from '../../renderers/groundRoad'
import { objectLayerSortKey } from './objectDepth'

export type BuildingDrawCommand = {
  id: string
  building: PlacedBuilding
  label: string
  tile: { x: number; y: number }
  textureUrl: string | null
  anchor: { x: number; y: number }
  size: { width: number; height: number }
  sortKey: number
  selected: boolean
}

const DEFAULT_BUILDING_SPRITE = {
  width: 512,
  height: 384,
  anchorX: 256 / 512,
  anchorY: 292 / 384,
}

export function buildingDrawCommands(
  buildings: readonly PlacedBuilding[],
  options: {
    allBuildings?: readonly PlacedBuilding[]
    selectedBuildingId?: string | null
  } = {},
): BuildingDrawCommand[] {
  const allBuildings = options.allBuildings ?? buildings
  return buildings
    .map((building) => buildingDrawCommand(building, allBuildings, options.selectedBuildingId ?? null))
    .filter((command): command is BuildingDrawCommand => command !== null)
    .sort((left, right) => left.sortKey - right.sortKey || left.id.localeCompare(right.id))
}

export function canDrawBuildingInObjectLayer(building: PlacedBuilding, allBuildings: readonly PlacedBuilding[] = [building]) {
  return buildingDrawCommand(building, allBuildings, null) !== null
}

export function buildingDrawCommand(
  building: PlacedBuilding,
  allBuildings: readonly PlacedBuilding[],
  selectedBuildingId: string | null,
): BuildingDrawCommand {
  const shape = isModularPathKind(building.kind) ? modularPathShapeFor(building, [...allBuildings]) : undefined
  const textureUrl = resolveBuildingSpriteAsset(building, { shape })
  const spriteMetrics = buildingSpriteMetrics(building)

  return {
    id: building.id,
    building,
    label: building.name,
    tile: building.tile,
    textureUrl,
    anchor: spriteMetrics.anchor,
    size: spriteMetrics.size,
    sortKey: objectLayerSortKey(building.tile),
    selected: building.id === selectedBuildingId,
  }
}

function buildingSpriteMetrics(building: PlacedBuilding) {
  const manifest = buildingRegistryEntry(building.kind)
  const [width, height] = manifest?.render?.size ?? [DEFAULT_BUILDING_SPRITE.width, DEFAULT_BUILDING_SPRITE.height]
  const [anchorX, anchorY] = manifest?.anchor ?? [
    DEFAULT_BUILDING_SPRITE.anchorX * DEFAULT_BUILDING_SPRITE.width,
    DEFAULT_BUILDING_SPRITE.anchorY * DEFAULT_BUILDING_SPRITE.height,
  ]

  return {
    anchor: { x: anchorX / width, y: anchorY / height },
    size: { width, height },
  }
}
