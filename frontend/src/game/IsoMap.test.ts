import { describe, expect, it } from 'vitest'

import { gridToScreen } from './coordinates/iso'
import { mapObjectZIndex } from './renderer/depth'

describe('isometric map object depth', () => {
  it('draws lower screen objects above upper screen objects', () => {
    const upper = gridToScreen({ x: 4, y: 4 })
    const lower = gridToScreen({ x: 5, y: 4 })

    expect(mapObjectZIndex(lower.y)).toBeGreaterThan(mapObjectZIndex(upper.y))
  })

  it('keeps fractional wrapped positions in a stable integer layer', () => {
    expect(mapObjectZIndex(120.4)).toBe(mapObjectZIndex(120.49))
  })
})
