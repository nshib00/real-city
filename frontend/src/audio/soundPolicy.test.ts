import { describe, expect, it } from 'vitest'

import { buildingImpactSound, combatDistanceGain, defenseSound, weaponSound } from './soundPolicy'

describe('combat sound policy', () => {
  it('mutes distant events and attenuates nearby ones', () => {
    expect(combatDistanceGain({ x: 0, y: 0 }, { x: 0, y: 0 }, 1)).toBe(1)
    expect(combatDistanceGain({ x: 8, y: 0 }, { x: 0, y: 0 }, 1)).toBeLessThan(1)
    expect(combatDistanceGain({ x: 80, y: 0 }, { x: 0, y: 0 }, 1)).toBe(0)
    expect(combatDistanceGain(undefined, { x: 0, y: 0 }, 1)).toBe(0)
  })

  it('selects confirmed weapon, trap and impact material', () => {
    expect(weaponSound('defense_bolt_thrower')).toBe('combat.weapon.bolt_thrower')
    expect(defenseSound('defense_resin_snare')).toBe('combat.defense.resin_snare')
    expect(defenseSound('decoration')).toBeNull()
    expect(buildingImpactSound('wooden_wall')).toBe('combat.impact.wood')
    expect(buildingImpactSound('stone_wall')).toBe('combat.impact.stone')
  })
})
