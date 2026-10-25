import { describe, expect, it } from 'vitest'

import { damageSound, placementMaterialVariant, placementSound } from './buildingAudio'

describe('building audio decisions', () => {
  it('distinguishes road, wall and staged construction', () => {
    expect(placementSound('road', 'building')).toBe('build.road.placed')
    expect(placementSound('paved_road', 'building')).toBe('build.road.placed')
    expect(placementSound('stone_wall', 'building')).toBe('build.wall.placed')
    expect(placementSound('dugout', 'building')).toBe('build.started')
    expect(placementSound('dugout', 'active')).toBe('build.placed')
    expect(placementMaterialVariant('wooden_wall')).toBe(0)
    expect(placementMaterialVariant('stone_wall')).toBe(1)
    expect(placementMaterialVariant('modern_wall')).toBe(2)
  })

  it('uses confirmed HP loss and ignores state refreshes', () => {
    const before = { health: 100, maxHealth: 100, state: 'active' as const }
    expect(damageSound(undefined, { health: 50, state: 'damaged' })).toBeNull()
    expect(damageSound(before, { health: 100, state: 'active' })).toBeNull()
    expect(damageSound(before, { health: 90, state: 'damaged' })).toBe('build.damaged.light')
    expect(damageSound(before, { health: 60, state: 'damaged' })).toBe('build.damaged.heavy')
    expect(damageSound(before, { health: 0, state: 'ruined' })).toBe('build.damaged.ruined')
  })
})
