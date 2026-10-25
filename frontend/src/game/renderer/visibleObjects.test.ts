import { describe, expect, it } from 'vitest'

import { filterVisibleMapObjects, isMapObjectVisible, occupiedTileKeys, tileOccupancyKey } from './visibleObjects'

const camera = { x: 0, y: 0, zoom: 1 }
const viewportSize = { width: 1280, height: 720 }

describe('visible map objects', () => {
  it('keeps objects inside the current stage bounds', () => {
    expect(isMapObjectVisible({ x: 0, y: 0 }, { camera, viewportSize })).toBe(true)
  })

  it('filters out objects far outside the current stage bounds', () => {
    const objects = [
      { id: 'near', tile: { x: 0, y: 0 } },
      { id: 'far', tile: { x: 60, y: 0 } },
    ]

    expect(filterVisibleMapObjects(objects, { camera, viewportSize }).map((object) => object.id)).toEqual(['near'])
  })

  it('keeps wrapped objects near the viewport center', () => {
    expect(isMapObjectVisible({ x: 159, y: 159 }, { camera, viewportSize })).toBe(true)
  })

  it('uses the actual camera position for buildings near the lower world seam', () => {
    expect(isMapObjectVisible({ x: 150, y: 150 }, {
      camera: { x: 24, y: 2192, zoom: 1.6 },
      viewportSize: { width: 1200, height: 800 },
    })).toBe(true)
  })

  it('keeps edge objects mounted at high zoom while large sprites can overlap the viewport', () => {
    expect(isMapObjectVisible({ x: 6, y: 0 }, { camera: { ...camera, zoom: 1.6 }, viewportSize })).toBe(true)
  })

  it('still filters distant objects at high zoom', () => {
    expect(isMapObjectVisible({ x: 20, y: 0 }, { camera: { ...camera, zoom: 1.6 }, viewportSize })).toBe(false)
  })

  it('uses smaller visibility bounds for compact objects', () => {
    const tile = { x: 11, y: 0 }
    expect(isMapObjectVisible(tile, { camera, viewportSize })).toBe(true)
    expect(isMapObjectVisible(tile, { camera, viewportSize, maxScreenExtent: 96 })).toBe(false)
  })

  it('does not filter before the stage is measured', () => {
    const objects = [
      { id: 'near', tile: { x: 0, y: 0 } },
      { id: 'far', tile: { x: 60, y: 0 } },
    ]

    expect(filterVisibleMapObjects(objects, { camera, viewportSize: { width: 0, height: 0 } })).toHaveLength(2)
  })

  it('builds stable occupancy keys for hiding terrain under map objects', () => {
    const objects = [
      { id: 'town-hall', tile: { x: 4, y: 8 } },
      { id: 'dugout', tile: { x: 5, y: 8 } },
    ]

    expect(tileOccupancyKey({ x: 4, y: 8 })).toBe('4:8')
    expect(occupiedTileKeys(objects)).toEqual(new Set(['4:8', '5:8']))
  })
})
