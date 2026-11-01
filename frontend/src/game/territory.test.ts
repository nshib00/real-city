import { expect, it } from 'vitest'
import { occupiedTerritory } from './territory'
import type { PlacedBuilding } from './state/useGameStore'
import { WORLD_WRAP_TILES } from './coordinates/iso'

const building = (owner: string, x: number, y: number, more: Partial<PlacedBuilding> = {}) => ({ id: `${owner}-${x}-${y}`, kind: 'dugout', owner, tile: { x, y }, state: 'active', ...more }) as PlacedBuilding
it('объединяет только соседние клетки одного владельца и сохраняет границу союзников', () => {
  const cells = occupiedTerritory([building('me', 0, 0), building('me', 1, 0), building('ally', 2, 0)], 'me', new Set(['ally']))
  expect(cells[0].edges).toEqual([true, false, true, true])
  expect(cells[1].edges).toEqual([true, true, true, false])
  expect(cells[2].ownership).toBe('ally')
  expect(cells).toHaveLength(3)
})
it('учитывает серверный размер и замыкание мира, исключает руины, не расширяет влияние', () => {
  const cells = occupiedTerritory([building('me', WORLD_WRAP_TILES-1, 0, { footprintW: 2, footprintH: 1 }), building('other', 5, 5, { state: 'ruined' })], 'me')
  expect(cells.map(cell => cell.x)).toEqual([WORLD_WRAP_TILES-1, 0])
  expect(cells[0].edges[1]).toBe(false)
  expect(cells[1].edges[3]).toBe(false)
})
