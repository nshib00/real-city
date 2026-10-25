import { describe, expect, it } from 'vitest'

import { nearestWrappedScreenCoord } from '../coordinates/iso'
import { useGameStore } from './useGameStore'

describe('useGameStore', () => {
  it('selects a tile without recentering the loaded viewport', () => {
    useGameStore.setState({ viewport: { center: { x: 3, y: 4 }, radius: 1 } })

    useGameStore.getState().selectTile({ x: 12, y: -4 })

    expect(useGameStore.getState().selectedTile).toEqual({ x: 12, y: -4 })
    expect(useGameStore.getState().viewport.center).toEqual({ x: 3, y: 4 })
  })

  it('clamps viewport radius', () => {
    useGameStore.getState().setViewportRadius(99)
    expect(useGameStore.getState().viewport.radius).toBe(3)
  })

  it('keeps indexed world tile updates on the exact tile key', () => {
    useGameStore.getState().setWorldTiles([
      { x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 0, safe_zone: false, forest_density: 0 },
      { x: -1, y: 1, chunk_x: -1, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
    ])

    useGameStore.getState().updateWorldTile({ x: -1, y: 1, chunk_x: -1, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 2 })

    const state = useGameStore.getState()
    expect(state.worldTiles).toHaveLength(2)
    expect(state.worldTiles[1].forest_density).toBe(2)
    expect(state.worldTileIndexByKey['-1:1']).toBe(1)
  })

  it('keeps building indexes in sync for select and delete operations', () => {
    useGameStore.setState({ buildings: [], buildingIndexById: {}, selectedBuildingId: null, selectedTile: null })
    useGameStore.getState().addBuilding(testBuilding('b1', { x: 1, y: 1 }))
    useGameStore.getState().addBuilding(testBuilding('b2', { x: 2, y: 2 }))

    useGameStore.getState().selectBuilding('b2')
    expect(useGameStore.getState().selectedTile).toEqual({ x: 2, y: 2 })

    useGameStore.getState().deleteBuilding('b1')
    const state = useGameStore.getState()
    expect(state.buildings.map((building) => building.id)).toEqual(['b2'])
    expect(state.buildingIndexById.b2).toBe(0)
  })

  it('persists collapsed chat and notification preferences', () => {
    localStorage.clear()

    useGameStore.getState().setChatCollapsed(true)
    useGameStore.getState().setNotificationsCollapsed(true)

    expect(useGameStore.getState().uiPreferences.isChatCollapsed).toBe(true)
    expect(useGameStore.getState().uiPreferences.areNotificationsCollapsed).toBe(true)
    expect(JSON.parse(localStorage.getItem('real-city.ui-preferences') ?? '{}')).toMatchObject({
      isChatCollapsed: true,
      areNotificationsCollapsed: true,
    })
  })

  it('focuses map camera on a selected world tile', () => {
    useGameStore.getState().focusTile({ tile: { x: 40, y: 80 }, viewportWidth: 1200, viewportHeight: 800 })

    expect(useGameStore.getState().selectedTile).toEqual({ x: 40, y: 80 })
    expect(useGameStore.getState().viewport.center).toEqual({ x: 40, y: 80 })
  })

  it('keeps the focused building tile on screen at non-default zoom near the world seam', () => {
    useGameStore.setState({ camera: { x: 0, y: 0, zoom: 1.6 } })
    const tile = { x: 150, y: 150 }
    const viewportSize = { width: 1200, height: 800 }

    useGameStore.getState().focusTile({ tile, viewportWidth: viewportSize.width, viewportHeight: viewportSize.height })

    const { camera } = useGameStore.getState()
    const origin = { x: viewportSize.width * 0.48 + camera.x, y: viewportSize.height * 0.16 + camera.y }
    const screenTarget = { x: (viewportSize.width / 2 - origin.x) / camera.zoom, y: (viewportSize.height / 2 - origin.y) / camera.zoom }
    const pos = nearestWrappedScreenCoord(tile, screenTarget)
    expect(origin.x + pos.x * camera.zoom).toBeCloseTo(viewportSize.width / 2)
    expect(origin.y + pos.y * camera.zoom).toBeCloseTo(viewportSize.height / 2)
  })

  it('keeps the map point under the cursor stable while zooming', () => {
    useGameStore.setState({ camera: { x: 24, y: -12, zoom: 1 } })

    useGameStore.getState().setZoomAt({
      zoom: 1.2,
      focalScreen: { x: 360, y: 240 },
      viewportSize: { width: 960, height: 640 },
    })

    const camera = useGameStore.getState().camera
    const originBase = { x: 960 * 0.48, y: 640 * 0.16 }
    const before = {
      x: (360 - (originBase.x + 24)) / 1,
      y: (240 - (originBase.y - 12)) / 1,
    }
    const after = {
      x: (360 - (originBase.x + camera.x)) / camera.zoom,
      y: (240 - (originBase.y + camera.y)) / camera.zoom,
    }

    expect(after.x).toBeCloseTo(before.x)
    expect(after.y).toBeCloseTo(before.y)
  })

  it('moves the camera continuously across its former wrap boundary', () => {
    useGameStore.setState({ camera: { x: 0, y: 15_350, zoom: 1.6 } })

    useGameStore.getState().panCamera({ x: 0, y: 20 })

    expect(useGameStore.getState().camera.y).toBe(15_370)
  })

  it('completes construction when timer expires', () => {
    const now = 2000
    useGameStore.setState({
      buildings: [
        {
          id: 'dugout-test',
          kind: 'dugout',
          name: 'Землянка',
          level: 1,
          tile: { x: 1, y: 1 },
          status: 'construction',
          state: 'building',
          health: 100,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: now,
        },
      ],
    })

    useGameStore.getState().tickConstructions(now)

    expect(useGameStore.getState().buildings[0].status).toBe('active')
    expect(useGameStore.getState().buildings[0].state).toBe('active')
    expect(useGameStore.getState().buildings[0].completesAt).toBeNull()
    expect(useGameStore.getState().constructionNow).toBe(now)
  })

  it('keeps building collection stable when the timer has no new work', () => {
    const building = { ...testBuilding('ready-field', { x: 1, y: 1 }), fieldStageReadyAt: 1000, fieldStageReady: false }
    useGameStore.setState({ buildings: [building] })
    useGameStore.getState().tickConstructions(999)
    expect(useGameStore.getState().buildings[0]).toBe(building)

    useGameStore.getState().tickConstructions(1000)
    const completed = useGameStore.getState().buildings
    expect(completed[0].fieldStageReady).toBe(true)

    useGameStore.getState().tickConstructions(2000)
    expect(useGameStore.getState().buildings).toBe(completed)
  })
})

function testBuilding(id: string, tile: { x: number; y: number }) {
  return {
    id,
    kind: 'dugout' as const,
    name: id,
    level: 1,
    tile,
    status: 'active' as const,
    health: 100,
    owner: 'p1',
    startedAt: 0,
    completesAt: null,
  }
}
