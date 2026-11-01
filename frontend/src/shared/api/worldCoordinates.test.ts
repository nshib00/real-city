import { beforeEach, describe, expect, it, vi } from 'vitest'
const { request } = vi.hoisted(() => ({ request: vi.fn() }))
vi.mock('./client', () => ({ request }))
import { chopForest, getChunks, getViewport } from './world'
import { placeBuilding, relocateBuilding, listVisibleBuildings } from './buildings'
import { updatePlayerPresence, listNearbyPlayers } from './playerPresence'
import { listMonsterLoot, listMonsters, listThreats } from './monsters'

describe('canonical coordinates at the API boundary', () => {
  beforeEach(() => request.mockClear())
  it('uses chunk units for chunk reads and tile units for the viewport', () => {
    getChunks({ x: -1, y: 5 })
    expect(request).toHaveBeenLastCalledWith('/world/chunks?x=4&y=0&radius=1')
    getViewport({ x: -1, y: 320 })
    expect(request).toHaveBeenLastCalledWith('/world/viewport?x=159&y=0&radius=48')
  })
  it.each([{ x: -1, y: 320 }, { x: 159, y: 0 }, { x: 319, y: -160 }])('normalizes equivalent corners %j', (tile) => {
    chopForest(tile)
    expect(JSON.parse(request.mock.calls.at(-1)![1].body)).toEqual({ tile_x: 159, tile_y: 0 })
    placeBuilding({ type: 'dugout', tile_x: tile.x, tile_y: tile.y })
    expect(JSON.parse(request.mock.calls.at(-1)![1].body)).toEqual({ type: 'dugout', tile_x: 159, tile_y: 0 })
    relocateBuilding('b', tile, 90)
    expect(JSON.parse(request.mock.calls.at(-1)![1].body)).toEqual({ action: 'relocate', tile_x: 159, tile_y: 0, rotation: 90 })
    updatePlayerPresence(tile)
    expect(JSON.parse(request.mock.calls.at(-1)![1].body)).toEqual({ tile_x: 159, tile_y: 0 })
    listNearbyPlayers(tile, 10)
    expect(request).toHaveBeenLastCalledWith('/players/nearby?x=159&y=0&radius=10')
    listVisibleBuildings(tile, 10)
    expect(request).toHaveBeenLastCalledWith('/buildings?scope=visible&x=159&y=0&radius=10')
    listMonsters({ ...tile, radius: 10 })
    expect(request).toHaveBeenLastCalledWith('/monsters?x=159&y=0&radius=10')
    listMonsterLoot({ ...tile, radius: 10 })
    expect(request).toHaveBeenLastCalledWith('/monster-loot?x=159&y=0&radius=10')
    listThreats({ ...tile, radius: 10 })
    expect(request).toHaveBeenLastCalledWith('/threats?x=159&y=0&radius=10')
  })
})
