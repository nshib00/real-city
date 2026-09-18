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

  it('blocks target tile forest for 1x1 buildings', () => {
    expect(
      validatePlacementPreview({
        kind: 'town_hall',
        tile: { x: 0, y: 0 },
        terrain: 'grass',
        footprint: { width: 1, height: 1 },
        worldTiles: [
          { x: 0, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
        ],
        buildings: [],
      }),
    ).toEqual({
      valid: false,
      reason: 'Сначала срубите лес на этой клетке',
    })
  })

  it('blocks monster, ruins and oil well tiles', () => {
    expect(
      validatePlacementPreview({
        kind: 'town_hall',
        tile: { x: 2, y: 2 },
        terrain: 'grass',
        buildings: [],
        monsters: [{ id: 'm1', type: 'roaming_melee', state: 'wandering', tile: { x: 2, y: 2 }, targetId: '', targetType: '', health: 10, maxHealth: 10, damage: 1, aggroRadius: 1, updatedAt: 0 }],
      }),
    ).toEqual({ valid: false, reason: 'На клетке находится монстр' })
    expect(validatePlacementPreview({ kind: 'town_hall', tile: { x: 0, y: 0 }, terrain: 'ruins', buildings: [] })).toEqual({
      valid: false,
      reason: 'На руинах и нефтяных скважинах строить нельзя',
    })
    expect(validatePlacementPreview({ kind: 'town_hall', tile: { x: 0, y: 0 }, terrain: 'oil_well', buildings: [] })).toEqual({
      valid: false,
      reason: 'На руинах и нефтяных скважинах строить нельзя',
    })
  })
})
