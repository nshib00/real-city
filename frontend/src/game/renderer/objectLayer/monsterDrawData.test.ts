import { describe, expect, it } from 'vitest'

import type { MonsterEntity } from '../../state/useGameStore'
import { monsterDirection, monsterDrawCommand, monsterDrawCommands, nextMonsterRenderMemory } from './monsterDrawData'

describe('monster draw data', () => {
  it('maps domain state to atlas-ready animation frames', () => {
    const command = monsterDrawCommand(monster({ state: 'attacking' }), {
      selectedMonsterId: 'm1',
      nowMs: 1_000,
    })

    expect(command).toMatchObject({
      id: 'm1',
      animationKey: 'attack',
      direction: 'se',
      selected: true,
      healthRatio: 0.25,
      atlasUrl: '/assets/monsters/resource_guardian/resource_guardian.webp?v=manifest-contract-2026-10-12',
    })
    expect(command.frameName).toMatch(/^resource_guardian_attack_se_\d{4}\.png$/)
  })

  it('keeps deterministic sorting and falls back to procedural data without atlas', () => {
    const commands = monsterDrawCommands([
      monster({ id: 'b', type: 'forest_stalker', tile: { x: 4, y: 4 } }),
      monster({ id: 'a', type: 'spore_beast', tile: { x: 1, y: 1 } }),
    ], { nowMs: 1_000 })

    expect(commands.map((command) => command.id)).toEqual(['a', 'b'])
    expect(commands[0].atlasUrl).toBeNull()
    expect(commands[0].frameName).toMatch(/^spore_beast_idle_se_\d{4}\.png$/)
  })

  it('infers direction and interpolation memory from server tile changes', () => {
    const firstMemory = nextMonsterRenderMemory([monster({ tile: { x: 1, y: 1 } })], new Map(), 1_000)
    const nextMemory = nextMonsterRenderMemory([monster({ tile: { x: 2, y: 1 } })], firstMemory, 1_100)
    const memory = nextMemory.get('m1')

    expect(memory).toMatchObject({
      tile: { x: 2, y: 1 },
      previousTile: { x: 1, y: 1 },
      direction: 'ne',
      observedAtMs: 1_100,
    })
    expect(monsterDirection(monster({ tile: { x: 2, y: 1 } }), memory)).toBe('ne')

    const command = monsterDrawCommand(monster({ tile: { x: 2, y: 1 }, state: 'wandering' }), {
      selectedMonsterId: null,
      previous: memory,
      nowMs: 1_310,
    })
    expect(command.displayTile.x).toBeGreaterThan(1)
    expect(command.displayTile.x).toBeLessThan(2)
    expect(command.animationKey).toBe('walk')
  })
})

function monster(overrides: Partial<MonsterEntity> = {}): MonsterEntity {
  return {
    id: 'm1',
    type: 'resource_guardian',
    state: 'idle',
    tile: { x: 1, y: 2 },
    targetId: '',
    targetType: '',
    health: 35,
    maxHealth: 140,
    damage: 12,
    aggroRadius: 4,
    updatedAt: Date.now(),
    ...overrides,
  }
}
