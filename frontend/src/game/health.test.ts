import { describe, expect, it } from 'vitest'

import { healthBarColor, healthRatio, maxHealthForBuilding } from './health'
import type { PlacedBuilding } from './state/useGameStore'

describe('health bars', () => {
  it('uses the six requested colors at their boundaries', () => {
    expect([1, 0.85, 0.849, 0.65, 0.649, 0.45, 0.449, 0.25, 0.249, 0.05, 0.049, 0]
      .map(healthBarColor)).toEqual([
      0xa8f0a0, 0xa8f0a0, 0x66d17a, 0x66d17a,
      0xf2d64b, 0xf2d64b, 0xf29338, 0xf29338,
      0xe44848, 0xe44848, 0x751b32, 0x751b32,
    ])
  })

  it('uses actual maximum health for the filled share and clamps invalid values', () => {
    expect(healthRatio(45, 180)).toBe(0.25)
    expect(healthRatio(150, 100)).toBe(1)
    expect(healthRatio(-5, 100)).toBe(0)
    expect(healthRatio(20, 0)).toBe(0)
  })

  it('resolves building level health when an older payload omits maxHealth', () => {
    const building = { kind: 'town_hall', level: 1, health: 50 } as PlacedBuilding
    expect(maxHealthForBuilding(building)).toBeGreaterThan(0)
    expect(maxHealthForBuilding({ ...building, maxHealth: 250 })).toBe(250)
  })
})
