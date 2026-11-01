import { buildingCatalog } from '../../../shared/catalog/buildings'
import type { WorldTile } from '../shared/contracts'
import { WORLD_WRAP_TILES } from './coordinates/iso'
import type { PlacedBuilding } from './state/useGameStore'

type Coord = { x: number; y: number }
export type DefenseRangeCell = Coord & { edges: boolean[] }
const wrap = (n: number) => ((n % WORLD_WRAP_TILES) + WORLD_WRAP_TILES) % WORLD_WRAP_TILES
const key = ({ x, y }: Coord) => `${wrap(x)}:${wrap(y)}`
const footprints = new Map(buildingCatalog.map(item => [item.type as string, item.footprint]))
const transparent = new Set(['road', 'standard_road', 'paved_road', 'defense_stakes', 'defense_resin_snare'])

/** Та же линия Брезенхэма и квадратная дальность, что на сервере; конечная клетка не блокирует саму себя. */
export function defenseRangeCells(cannon: PlacedBuilding, buildings: readonly PlacedBuilding[], tiles: readonly WorldTile[]): DefenseRangeCell[] {
  const radius = cannon.cannonRange ?? 0
  if (radius <= 0) return []
  const terrain = new Map(tiles.map(tile => [key(tile), tile.terrain]))
  const blocked = new Set<string>()
  for (const building of buildings) {
    if (building.state === 'ruined' || transparent.has(building.kind)) continue
    const size = footprints.get(building.kind)
    for (let y = 0; y < Math.max(1, building.footprintH ?? size?.height ?? 1); y++) {
      for (let x = 0; x < Math.max(1, building.footprintW ?? size?.width ?? 1); x++) {
        blocked.add(key({ x: building.tile.x + x, y: building.tile.y + y }))
      }
    }
  }
  const cells = new Map<string, Coord>()
  for (let dx = -radius; dx <= radius; dx++) for (let dy = -radius; dy <= radius; dy++) {
    const target = { x: cannon.tile.x + dx, y: cannon.tile.y + dy }
    // Не обещаем видимость через ещё не загруженные участки карты.
    if (!terrain.has(key(target))) continue
    let x = cannon.tile.x, y = cannon.tile.y
    const ax = Math.abs(dx), ay = Math.abs(dy), sx = dx < 0 ? -1 : 1, sy = dy < 0 ? -1 : 1
    let error = ax - ay, clear = true
    while (x !== target.x || y !== target.y) {
      const twice = 2 * error
      if (twice > -ay) { error -= ay; x += sx }
      if (twice < ax) { error += ax; y += sy }
      if (x === target.x && y === target.y) break
      const cellKey = key({ x, y })
      if (!terrain.has(cellKey) || terrain.get(cellKey) === 'mountain' || blocked.has(cellKey)) { clear = false; break }
    }
    if (clear) cells.set(key(target), { x: wrap(target.x), y: wrap(target.y) })
  }
  return [...cells.values()].map(cell => ({ ...cell, edges: [[0, -1], [1, 0], [0, 1], [-1, 0]].map(([dx, dy]) => !cells.has(key({ x: cell.x + dx, y: cell.y + dy }))) }))
}
