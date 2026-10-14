import { describe, expect, it } from 'vitest'

import { buildingHitAtTile } from './mapHitTarget'

describe('map hit target', () => {
  it('prefers the building standing on the clicked tile over overlapping sprite bounds', () => {
    const windleafBed = { id: 'windleaf-bed', tile: { x: 3, y: 2 } }
    const dugout = { id: 'dugout', tile: { x: 4, y: 2 } }

    expect(buildingHitAtTile({ x: 4, y: 2 }, [
      { building: windleafBed, sortKey: 100 },
      { building: dugout, sortKey: 90 },
    ])).toBe(dugout)
  })

  it('uses draw order when multiple buildings share a tile during transient updates', () => {
    const lower = { id: 'lower', tile: { x: 4, y: 2 } }
    const upper = { id: 'upper', tile: { x: 4, y: 2 } }

    expect(buildingHitAtTile({ x: 4, y: 2 }, [
      { building: lower, sortKey: 10 },
      { building: upper, sortKey: 20 },
    ])).toBe(upper)
  })
})
