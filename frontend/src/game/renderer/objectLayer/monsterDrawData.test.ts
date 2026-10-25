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
      atlasUrl: '/assets/monsters/resource_guardian/resource_guardian.webp?v=blender-rig-v1',
    })
    expect(command.frameName).toMatch(/^resource_guardian_attack_se_\d{4}\.png$/)
  })

  it('keeps deterministic sorting and resolves atlas frames for every monster', () => {
    const commands = monsterDrawCommands([
      monster({ id: 'b', type: 'forest_stalker', tile: { x: 4, y: 4 } }),
      monster({ id: 'a', type: 'spore_beast', tile: { x: 1, y: 1 } }),
    ], { nowMs: 1_000 })

    expect(commands.map((command) => command.id)).toEqual(['a', 'b'])
    expect(commands[0].atlasUrl).toBe('/assets/monsters/spore_beast/spore_beast.webp?v=blender-rig-v1')
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

  it('starts attack, hit and death clips when the corresponding state changes', () => {
    const idle = monster({ updatedAt: 1 })
    const idleMemory = nextMonsterRenderMemory([idle], new Map(), 1_000)
    const attacking = monster({ state: 'attacking', updatedAt: 2 })
    const attackMemory = nextMonsterRenderMemory([attacking], idleMemory, 1_100)
    expect(monsterDrawCommand(attacking, { selectedMonsterId: null, previous: attackMemory.get('m1'), nowMs: 1_100 }).frameName)
      .toBe('resource_guardian_attack_se_0000.png')
    expect(monsterDrawCommand(attacking, { selectedMonsterId: null, previous: attackMemory.get('m1'), nowMs: 1_350 }).frameName)
      .toBe('resource_guardian_attack_se_0003.png')

    const wounded = monster({ state: 'attacking', health: 20, updatedAt: 3 })
    const hitMemory = nextMonsterRenderMemory([wounded], attackMemory, 1_400)
    expect(monsterDrawCommand(wounded, { selectedMonsterId: null, previous: hitMemory.get('m1'), nowMs: 1_400 }).frameName)
      .toBe('resource_guardian_hit_se_0000.png')

    const dead = monster({ state: 'dead', health: 0, updatedAt: 4 })
    const deathMemory = nextMonsterRenderMemory([dead], hitMemory, 1_500)
    expect(monsterDrawCommand(dead, { selectedMonsterId: null, previous: deathMemory.get('m1'), nowMs: 1_500 }).frameName)
      .toBe('resource_guardian_death_se_0000.png')
  })

  it('places grounded monster feet on the map surface for atlas and preview sprites', () => {
    const contacts = {
      roaming_melee: { near: 121, far: 114, preview: 431 },
      resource_guardian: { near: 134, far: 125, preview: 477 },
      ruins_guardian: { near: 116, far: 110, preview: 412 },
      forest_stalker: { near: 124, far: 117, preview: 442 },
      spore_beast: { near: 131, far: 124, preview: 469 },
      ironback_brute: { near: 135, far: 125, preview: 480 },
      ancient_colossus: { near: 118, far: 111, preview: 421 },
    } as const

    for (const [type, contact] of Object.entries(contacts) as [keyof typeof contacts, typeof contacts[keyof typeof contacts]][]) {
      for (const [direction, atlasContact] of [['se', contact.near], ['nw', contact.far]] as const) {
        const command = monsterDrawCommand(monster({ type }), {
          selectedMonsterId: null,
          previous: { tile: { x: 1, y: 2 }, observedAtMs: 0, direction, state: 'idle', health: 35, updatedAt: 0, actionStartedAtMs: 0 },
          nowMs: 1_000,
        })
        const atlasFootY = command.groundOffsetY.atlas + command.size.height * (atlasContact / 144 - command.anchor.y)
        const previewFootY = command.groundOffsetY.preview + command.size.height * (contact.preview / 512 - command.anchor.y)
        expect(atlasFootY).toBeCloseTo(5)
        expect(previewFootY).toBeCloseTo(5)
      }
    }

    const wisp = monsterDrawCommand(monster({ type: 'ember_wisp' }), { selectedMonsterId: null, nowMs: 1_000 })
    expect(wisp.groundOffsetY).toEqual({ atlas: 0, preview: 0 })
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
