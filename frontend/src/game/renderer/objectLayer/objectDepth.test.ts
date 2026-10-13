import { describe, expect, it } from 'vitest'

import { objectLayerSortKey } from './objectDepth'

describe('object layer depth', () => {
  it('sorts isometric objects by their base tile diagonal', () => {
    expect(objectLayerSortKey({ x: 5, y: 5 })).toBeGreaterThan(objectLayerSortKey({ x: 4, y: 4 }))
  })

  it('keeps layer and footprint offsets centralized', () => {
    expect(objectLayerSortKey({ x: 2, y: 3 }, 20, 4)).toBe(objectLayerSortKey({ x: 2, y: 3 }) + 24)
  })
})

