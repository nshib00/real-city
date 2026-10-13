import { describe, expect, it } from 'vitest'

import type { MonsterEntity } from '../state/useGameStore'
import {
  monsterAnimationFallback,
  monsterAnimationKeyForState,
  monsterAssetRegistryEntry,
  registeredMonsterAssetFamilies,
  resolveMonsterAnimation,
  resolveMonsterAtlasAsset,
  resolveMonsterAtlasSource,
} from './monsterAssetRegistry'

describe('monster asset registry', () => {
  it('registers all current domain monster types', () => {
    expect(registeredMonsterAssetFamilies().map((manifest) => manifest.monsterId).sort()).toEqual([
      'ancient_colossus',
      'ember_wisp',
      'forest_stalker',
      'ironback_brute',
      'resource_guardian',
      'roaming_melee',
      'ruins_guardian',
      'spore_beast',
    ])
    expect(monsterAssetRegistryEntry('resource_guardian')).toMatchObject({ displayName: 'Страж залежи', anchor: [128, 190] })
  })

  it('maps domain states to visual animation keys', () => {
    expect(monsterAnimationKeyForState('idle')).toBe('idle')
    expect(monsterAnimationKeyForState('wandering')).toBe('walk')
    expect(monsterAnimationKeyForState('aggro')).toBe('walk')
    expect(monsterAnimationKeyForState('attacking')).toBe('attack')
    expect(monsterAnimationKeyForState('dead')).toBe('death')
  })

  it('selects animation and direction with safe fallbacks', () => {
    expect(resolveMonsterAnimation(monster({ state: 'attacking' }), 'e')).toMatchObject({ key: 'attack', direction: 'ne', animation: { fps: 12 } })
    expect(monsterAnimationFallback('attack', { animations: { idle: { fps: 6, loop: true } } })).toBe('idle')
  })

  it('resolves atlas URLs through manifest metadata', () => {
    expect(resolveMonsterAtlasAsset('ruins_guardian')).toBe('/assets/monsters/ruins_guardian/ruins_guardian.webp?v=manifest-contract-2026-10-12')
    expect(resolveMonsterAtlasSource('ruins_guardian')).toMatchObject({
      assetId: 'ruins_guardian',
      basePath: '/assets/monsters/ruins_guardian',
      fallbackUrl: '/assets/monsters/ruins_guardian/ruins_guardian.webp?v=manifest-contract-2026-10-12',
    })
  })
})

function monster(overrides: Partial<MonsterEntity>): MonsterEntity {
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
