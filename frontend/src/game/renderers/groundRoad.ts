import { wrapGridCoord } from '../coordinates/iso'
import type { PlacedBuilding } from '../state/useGameStore'
import { resolveBuildingSpriteAsset } from './buildingRegistry'

export type ModularPathShape =
  | 'single'
  | 'end_n'
  | 'end_e'
  | 'end_s'
  | 'end_w'
  | 'straight_ns'
  | 'straight_ew'
  | 'corner_ne'
  | 'corner_es'
  | 'corner_sw'
  | 'corner_wn'
  | 't_nes'
  | 't_esw'
  | 't_swn'
  | 't_wne'
  | 'cross'

type ModularPathKind = Extract<PlacedBuilding['kind'], 'road' | 'standard_road' | 'paved_road' | 'wooden_wall' | 'stone_wall' | 'concrete_wall' | 'modern_wall'>

type RoadNeighborMask = {
  n: boolean
  e: boolean
  s: boolean
  w: boolean
}

const pathAssets: Record<ModularPathKind, { group: 'road' | 'wall' }> = {
  road: { group: 'road' },
  standard_road: { group: 'road' },
  paved_road: { group: 'road' },
  wooden_wall: { group: 'wall' },
  stone_wall: { group: 'wall' },
  concrete_wall: { group: 'wall' },
  modern_wall: { group: 'wall' },
}

export function modularPathSpriteAsset(building: PlacedBuilding, shape: ModularPathShape = 'single') {
  if (!isModularPathKind(building.kind)) {
    return null
  }
  return resolveBuildingSpriteAsset(building, { shape })
}

export function modularPathShapeFor(building: PlacedBuilding, buildings: readonly PlacedBuilding[]): ModularPathShape {
  return modularPathShapeFromIndex(building, buildModularPathIndex(buildings))
}

export type ModularPathIndex = { road: Set<string>; wall: Set<string> }

export function buildModularPathIndex(buildings: readonly PlacedBuilding[]): ModularPathIndex {
  const index: ModularPathIndex = { road: new Set(), wall: new Set() }
  for (const building of buildings) {
    if (isModularPathKind(building.kind)) {
      index[pathAssets[building.kind].group].add(tileKey(building.tile.x, building.tile.y))
    }
  }
  return index
}

export function modularPathShapeFromIndex(building: PlacedBuilding, index: ModularPathIndex): ModularPathShape {
  if (!isModularPathKind(building.kind)) return 'single'
  const connectedTiles = index[pathAssets[building.kind].group]
  const { x, y } = building.tile
  return modularPathShapeFromMask({
    n: connectedTiles.has(tileKey(x, y - 1)),
    e: connectedTiles.has(tileKey(x + 1, y)),
    s: connectedTiles.has(tileKey(x, y + 1)),
    w: connectedTiles.has(tileKey(x - 1, y)),
  })
}

export function modularPathShapeFromMask(mask: RoadNeighborMask): ModularPathShape {
  const count = Number(mask.n) + Number(mask.e) + Number(mask.s) + Number(mask.w)
  if (count === 0) return 'single'
  if (count === 1) {
    if (mask.n) return 'end_n'
    if (mask.e) return 'end_e'
    if (mask.s) return 'end_s'
    return 'end_w'
  }
  if (count === 2) {
    if (mask.n && mask.s) return 'straight_ns'
    if (mask.e && mask.w) return 'straight_ew'
    if (mask.n && mask.e) return 'corner_ne'
    if (mask.e && mask.s) return 'corner_es'
    if (mask.s && mask.w) return 'corner_sw'
    return 'corner_wn'
  }
  if (count === 3) {
    if (!mask.w) return 't_nes'
    if (!mask.n) return 't_esw'
    if (!mask.e) return 't_swn'
    return 't_wne'
  }
  return 'cross'
}

export function isModularPathKind(kind: PlacedBuilding['kind']): kind is ModularPathKind {
  return kind in pathAssets
}

export function groundRoadSpriteAsset(building: PlacedBuilding, shape: ModularPathShape = 'single') {
  return modularPathSpriteAsset(building, shape) ?? `/assets/buildings/roads/ground_road/ground_road_${shape}_${modularPathState(building)}.png`
}

export function groundRoadShapeFor(building: PlacedBuilding, buildings: PlacedBuilding[]): ModularPathShape {
  return modularPathShapeFor(building, buildings)
}

export function groundRoadShapeFromMask(mask: RoadNeighborMask): ModularPathShape {
  return modularPathShapeFromMask(mask)
}

function modularPathState(building: PlacedBuilding) {
  if (building.health <= 0 || building.state === 'ruined') {
    return 'ruined'
  }
  if (building.health < 50 || building.state === 'damaged') {
    return 'damaged'
  }
  return building.status === 'construction' || building.state === 'building' || building.state === 'planned' ? 'construction' : 'active'
}

function tileKey(x: number, y: number) {
  const wrapped = wrapGridCoord({ x, y })
  return `${wrapped.x}:${wrapped.y}`
}
