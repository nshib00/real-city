import { buildingCatalog } from '../../../shared/catalog/buildings'
import { WORLD_WRAP_TILES } from './coordinates/iso'
import type { PlacedBuilding } from './state/useGameStore'
import { ownershipOf, type Ownership } from '../shared/ui/ownership'

export type TerritoryCell = { x: number; y: number; owner: string; ownership: Ownership; edges: boolean[] }
const footprints = new Map(buildingCatalog.map(item => [item.type as string, item.footprint]))
const wrap = (n: number) => ((n % WORLD_WRAP_TILES) + WORLD_WRAP_TILES) % WORLD_WRAP_TILES

/** Только известные занятые клетки, без выдуманного радиуса влияния или прав на соседний лес. */
export function occupiedTerritory(buildings: readonly PlacedBuilding[], viewer?: string | null, allies: ReadonlySet<string> = new Set()): TerritoryCell[] {
  const cells = new Map<string, TerritoryCell>()
  for (const building of buildings) {
    if (building.state === 'ruined' || !building.owner) continue
    const size = footprints.get(building.kind)
    for (let dy = 0; dy < (building.footprintH ?? size?.height ?? 1); dy++) for (let dx = 0; dx < (building.footprintW ?? size?.width ?? 1); dx++) {
      const x = wrap(building.tile.x + dx), y = wrap(building.tile.y + dy)
      cells.set(`${x}:${y}`, { x, y, owner: building.owner, ownership: ownershipOf(building.owner, viewer, allies), edges: [] })
    }
  }
  return [...cells.values()].map(cell => ({ ...cell, edges: [[0, -1], [1, 0], [0, 1], [-1, 0]].map(([dx, dy]) => cells.get(`${wrap(cell.x + dx)}:${wrap(cell.y + dy)}`)?.owner !== cell.owner) }))
}
