import { describe, expect, it } from 'vitest'

import { validatePlacementPreview } from './placement'

describe('validatePlacementPreview', () => {
  it('requires town hall before other buildings', () => {
    expect(validatePlacementPreview({ kind: 'dugout', tile: { x: 1, y: 1 }, buildings: [] })).toEqual({
      valid: false,
      reason: 'Сначала нужна ратуша',
    })
  })

  it('allows town hall on an empty tile', () => {
    expect(validatePlacementPreview({ kind: 'town_hall', tile: { x: 0, y: 0 }, buildings: [] })).toEqual({
      valid: true,
      reason: null,
    })
  })

  it('blocks building on forest, water and mountain tiles', () => {
    expect(validatePlacementPreview({ kind: 'town_hall', tile: { x: 0, y: 0 }, terrain: 'forest', buildings: [] })).toEqual({
      valid: false,
      reason: 'Сначала срубите лес на этой клетке',
    })
    expect(validatePlacementPreview({ kind: 'town_hall', tile: { x: 0, y: 0 }, terrain: 'water', buildings: [] })).toEqual({
      valid: false,
      reason: 'На реках и горах строить нельзя',
    })
  })

  it('blocks multi-tile buildings when forest is inside footprint', () => {
    expect(
      validatePlacementPreview({
        kind: 'town_hall',
        tile: { x: 0, y: 0 },
        terrain: 'grass',
        footprint: { width: 2, height: 2 },
        worldTiles: [
          { x: 0, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 0, safe_zone: false, forest_density: 0 },
          { x: 1, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
        ],
        buildings: [],
      }),
    ).toEqual({
      valid: false,
      reason: 'Сначала срубите лес на клетках под постройкой',
    })
  })
})
