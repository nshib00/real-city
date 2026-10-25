import { describe, expect, it } from 'vitest'

import { buildingHitAtTile, createRenderedTileLookup } from './mapHitTarget'

describe('map hit target', () => {
  it('resolves a click across the wrapped edge to the loaded terrain tile', () => {
    const grass = { x: 159, y: 1, terrain: 'grass' }
    const lookup = createRenderedTileLookup([grass], 160)
    expect(lookup({ x: -1, y: 1 })).toBe(grass)
    expect(lookup({ x: 319, y: 1 })).toBe(grass)
  })

  it('prefers the canonical world tile when duplicate chunks overlap', () => {
    const raw = { x: -1, y: 1, terrain: 'forest' }
    const wrapped = { x: 159, y: 1, terrain: 'grass' }
    const lookup = createRenderedTileLookup([wrapped, raw], 160)
    expect(lookup({ x: -1, y: 1 })).toBe(wrapped)
    expect(createRenderedTileLookup([raw], 160)({ x: -1, y: 1 })).toBe(raw)
    expect(lookup({ x: -2, y: 1 })).toBeNull()
  })

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
