import { expect, it } from 'vitest'
import { defenseRangeCells, towerDetectionRangeCells } from './defenseRange'
import type { PlacedBuilding } from './state/useGameStore'
import type { WorldTile } from '../shared/contracts'
import { toPlacedBuilding } from '../shared/api/buildings'

const cannon = { id: 'c', kind: 'defense_cannon', tile: { x: 6, y: 137 }, cannonRange: 4 } as PlacedBuilding
const ground = Array.from({ length: 9 }, (_, x) => Array.from({ length: 9 }, (_, y) => ({ x: x + 2, y: y + 133, terrain: 'grass' } as WorldTile))).flat()
const contains = (cells: ReturnType<typeof defenseRangeCells>, x: number, y: number) => cells.some(c => c.x === x && c.y === y)

it('показывает квадратную дальность сервера и только внешние рёбра', () => {
  const cells = defenseRangeCells(cannon, [cannon], ground)
  expect(cells).toHaveLength(81)
  expect(contains(cells, 10, 141)).toBe(true)
  expect(cells.find(c => c.x === 6 && c.y === 137)?.edges).toEqual([false, false, false, false])
  expect(cells.find(c => c.x === 10 && c.y === 141)?.edges).toEqual([false, true, true, false])
})

it('вырезает тень строящейся стены и возвращает её после разрушения', () => {
  const wall = { id: 'wall', kind: 'modern_wall', tile: { x: 8, y: 136 }, state: 'building' } as PlacedBuilding
  expect(contains(defenseRangeCells(cannon, [cannon, wall], ground), 9, 135)).toBe(false)
  expect(contains(defenseRangeCells(cannon, [cannon, wall], ground), 8, 136)).toBe(true)
  expect(contains(defenseRangeCells(cannon, [cannon, { ...wall, state: 'ruined' }], ground), 9, 135)).toBe(true)
})

it('учитывает горы, но не дороги и ловушки', () => {
  const mountain = ground.map(tile => tile.x === 7 && tile.y === 136 ? { ...tile, terrain: 'mountain' as const } : tile)
  expect(contains(defenseRangeCells(cannon, [cannon], mountain), 9, 135)).toBe(false)
  for (const kind of ['road', 'standard_road', 'paved_road', 'defense_stakes', 'defense_resin_snare'] as const) {
    expect(contains(defenseRangeCells(cannon, [cannon, { ...cannon, id: kind, kind, tile: { x: 7, y: 136 } }], ground), 9, 135)).toBe(true)
  }
})

it('учитывает всю площадь здания и замыкание мира', () => {
  const wall = { ...cannon, id: 'wall', kind: 'modern_wall' as const, tile: { x: 7, y: 135 }, footprintW: 1, footprintH: 2 }
  expect(contains(defenseRangeCells(cannon, [cannon, wall], ground), 9, 135)).toBe(false)
  const edge = { ...cannon, tile: { x: 159, y: 0 }, cannonRange: 2 }
  const tiles = [157, 158, 159, 0, 1].flatMap(x => [158, 159, 0, 1, 2].map(y => ({ x, y, terrain: 'grass' } as WorldTile)))
  expect(defenseRangeCells(edge, [edge], tiles)).toHaveLength(25)
  expect(contains(defenseRangeCells(edge, [edge, { ...wall, tile: { x: 0, y: 0 }, footprintH: 1 }], tiles), 1, 0)).toBe(false)
})

it('не обещает видимость через незагруженный участок и обрабатывает отсутствие радиуса', () => {
  expect(defenseRangeCells({ ...cannon, cannonRange: undefined }, [], ground)).toEqual([])
  const partial = ground.filter(tile => tile.x !== 7 || tile.y !== 136)
  expect(contains(defenseRangeCells(cannon, [cannon], partial), 9, 135)).toBe(false)
})

it('показывает геометрическую зону дозора башни по уровням с замыканием карты', () => {
  const tiles = Array.from({ length: 33 }, (_, x) => Array.from({ length: 33 }, (_, y) => ({ x: (x + 144) % 160, y: (y + 144) % 160, terrain: 'grass' } as WorldTile))).flat()
  for (let level = 1; level <= 6; level++) {
    const tower = { ...cannon, kind: 'tower' as const, towerWatchkeeperAssigned: true, state: 'active' as const, tile: { x: 0, y: 0 }, level, health: 520 }
    const radius = level * 2 + 4
    const cells = towerDetectionRangeCells(tower, tiles)
    expect(cells).toHaveLength(1 + 2 * radius * (radius + 1))
    expect(contains(cells, 160 - radius, 0)).toBe(true)
    expect(contains(cells, radius, radius)).toBe(false)
    expect(contains(cells, radius + 1, 0)).toBe(false)
  }
  expect(towerDetectionRangeCells({ ...cannon, kind: 'tower', level: 1, health: 0 }, tiles)).toEqual([])
  expect(towerDetectionRangeCells({ ...cannon, kind: 'tower', level: 1, state: 'active', health: 100 }, tiles)).toEqual([])
  expect(towerDetectionRangeCells({ ...cannon, kind: 'tower', level: 6, state: 'active', health: 130 }, tiles)).toEqual([])
  expect(towerDetectionRangeCells({ ...cannon, kind: 'tower', level: 1, state: 'building', health: 100 }, tiles)).toEqual([])
})

it('отображает дозор только после назначения жителя из REST DTO', () => {
  const tiles = [{ x: 0, y: 0, terrain: 'grass' } as WorldTile]
  const response = { id: 'tower', owner_id: 'owner', type: 'tower' as const, name: 'Сторожевая башня', level: 1,
    state: 'active' as const, health: 100, tile_x: 0, tile_y: 0, started_at: '2026-11-05T00:00:00Z', completes_at: null }
  expect(towerDetectionRangeCells(toPlacedBuilding(response), tiles)).toEqual([])
  expect(towerDetectionRangeCells(toPlacedBuilding({ ...response, tower_watchkeeper_assigned: false }), tiles)).toEqual([])
  expect(towerDetectionRangeCells(toPlacedBuilding({ ...response, tower_watchkeeper_assigned: true }), tiles)).toHaveLength(1)
})
