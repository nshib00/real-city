import { describe, expect, it } from 'vitest'

import { cellLabel, districtFromTile, districtLabel } from './district'

describe('district coordinates', () => {
  it('numbers cells from the top-left corner of each district', () => {
    expect(cellLabel({ x: 0, y: 0 })).toBe('A1')
    expect(cellLabel({ x: 31, y: 31 })).toBe('A1024')
    expect(cellLabel({ x: 32, y: 0 })).toBe('B1')
    expect(cellLabel({ x: 34, y: 70 })).toBe('L195')
    expect(cellLabel({ x: 159, y: 159 })).toBe('Y1024')
  })

  it('wraps coordinates with the world', () => {
    expect(cellLabel({ x: 160, y: 160 })).toBe('A1')
    expect(cellLabel({ x: -1, y: -1 })).toBe('Y1024')
    expect(districtLabel(districtFromTile({ x: 34, y: 70 }))).toBe('L')
  })
})
