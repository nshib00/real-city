import { describe, expect, it } from 'vitest'

import { canChopForestTile } from './forestActions'

describe('forest actions', () => {
  it('allows chopping only non-empty forest tiles', () => {
    expect(canChopForestTile({ x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 2 })).toBe(true)
    expect(canChopForestTile({ x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 0 })).toBe(false)
    expect(canChopForestTile({ x: 1, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 0, safe_zone: false, forest_density: 0 })).toBe(false)
    expect(canChopForestTile(null)).toBe(false)
  })
})
