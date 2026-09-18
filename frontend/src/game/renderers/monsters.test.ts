import { describe, expect, it } from 'vitest'

import { monsterClassName, monsterLabel } from './monsters'
import type { MonsterEntity } from '../state/useGameStore'

const baseMonster: MonsterEntity = {
  id: 'm1',
  type: 'resource_guardian',
  state: 'aggro',
  tile: { x: 1, y: 2 },
  targetId: 'b1',
  targetType: 'building',
  health: 35,
  maxHealth: 140,
  damage: 12,
  aggroRadius: 4,
  updatedAt: Date.now(),
}

describe('monster renderer helpers', () => {
  it('builds stable class names and labels', () => {
    expect(monsterClassName(baseMonster)).toContain('map-monster-resource_guardian')
    expect(monsterClassName(baseMonster)).toContain('map-monster-aggro')
    expect(monsterLabel(baseMonster)).toContain('35/140')
  })
})
