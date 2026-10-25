import type { MonsterEntity } from '../state/useGameStore'
import type { ObjectAtlasSource } from '../renderer/objectLayer/objectTextureCache'
import type { AssetAnchor, AssetAtlasManifest, AssetDirection, AssetGlbManifest, AssetAnimationManifest, MonsterAnimationKey } from './assetManifestTypes'
import { withAssetRevision } from './buildingRegistry'

export type MonsterAssetManifest = {
  monsterId: MonsterEntity['type']
  displayName: string
  anchor: AssetAnchor
  directions: readonly Extract<AssetDirection, 'ne' | 'nw' | 'se' | 'sw'>[]
  atlas?: AssetAtlasManifest
  animations: Partial<Record<MonsterAnimationKey, AssetAnimationManifest>>
  glb?: AssetGlbManifest
}

export type MonsterAnimationSelection = {
  key: MonsterAnimationKey
  direction: MonsterAssetManifest['directions'][number]
  animation: AssetAnimationManifest
}

const defaultDirections = ['ne', 'nw', 'se', 'sw'] as const

const monsterAssetManifests: readonly MonsterAssetManifest[] = [
  {
    monsterId: 'roaming_melee',
    displayName: 'Бродячий налетчик',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: {
      image: 'roaming_melee.webp',
      json: 'roaming_melee.atlas.json',
      revision: 'blender-rig-v1',
    },
    animations: defaultMonsterAnimations(),
    glb: {
      preview: 'roaming_melee_preview.glb',
    },
  },
  {
    monsterId: 'resource_guardian',
    displayName: 'Страж залежи',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: {
      image: 'resource_guardian.webp',
      json: 'resource_guardian.atlas.json',
      revision: 'blender-rig-v1',
    },
    animations: defaultMonsterAnimations(),
    glb: {
      preview: 'resource_guardian_preview.glb',
    },
  },
  {
    monsterId: 'ruins_guardian',
    displayName: 'Сторож руин',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: {
      image: 'ruins_guardian.webp',
      json: 'ruins_guardian.atlas.json',
      revision: 'blender-rig-v1',
    },
    animations: defaultMonsterAnimations(),
    glb: {
      preview: 'ruins_guardian_preview.glb',
    },
  },
  {
    monsterId: 'forest_stalker',
    displayName: 'Лесной следопыт',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: monsterAtlas('forest_stalker'),
    animations: defaultMonsterAnimations(),
    glb: { preview: 'forest_stalker_preview.glb' },
  },
  {
    monsterId: 'spore_beast',
    displayName: 'Споровый зверь',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: monsterAtlas('spore_beast'),
    animations: defaultMonsterAnimations(),
    glb: { preview: 'spore_beast_preview.glb' },
  },
  {
    monsterId: 'ironback_brute',
    displayName: 'Железоспин',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: monsterAtlas('ironback_brute'),
    animations: defaultMonsterAnimations(),
    glb: { preview: 'ironback_brute_preview.glb' },
  },
  {
    monsterId: 'ember_wisp',
    displayName: 'Тлеющий огонек',
    anchor: [128, 190],
    directions: defaultDirections,
    atlas: monsterAtlas('ember_wisp'),
    animations: defaultMonsterAnimations(),
    glb: { preview: 'ember_wisp_preview.glb' },
  },
  {
    monsterId: 'ancient_colossus',
    displayName: 'Древний колосс',
    anchor: [128, 210],
    directions: defaultDirections,
    atlas: monsterAtlas('ancient_colossus'),
    animations: defaultMonsterAnimations(),
    glb: { preview: 'ancient_colossus_preview.glb' },
  },
]

const registry = new Map(monsterAssetManifests.map((manifest) => [manifest.monsterId, manifest]))

function monsterAtlas(id: MonsterEntity['type']): AssetAtlasManifest {
  return { image: `${id}.webp`, json: `${id}.atlas.json`, revision: 'blender-rig-v1' }
}

export function monsterAssetRegistryEntry(type: MonsterEntity['type']) {
  return registry.get(type) ?? null
}

export function registeredMonsterAssetFamilies() {
  return [...monsterAssetManifests]
}

export function monsterDisplayName(type: MonsterEntity['type']) {
  return monsterAssetRegistryEntry(type)?.displayName ?? type
}

export function monsterAnimationKeyForState(state: MonsterEntity['state']): MonsterAnimationKey {
  switch (state) {
    case 'wandering':
    case 'aggro':
      return 'walk'
    case 'attacking':
      return 'attack'
    case 'dead':
      return 'death'
    case 'idle':
    default:
      return 'idle'
  }
}

export function resolveMonsterAnimation(monster: MonsterEntity, direction: AssetDirection = 'se'): MonsterAnimationSelection | null {
  const manifest = monsterAssetRegistryEntry(monster.type)
  if (!manifest) {
    return null
  }

  const animationKey = monsterAnimationFallback(monsterAnimationKeyForState(monster.state), manifest)
  const animation = manifest.animations[animationKey]
  if (!animation) {
    return null
  }

  return {
    key: animationKey,
    direction: monsterDirectionFallback(direction, manifest),
    animation,
  }
}

export function resolveMonsterAtlasAsset(type: MonsterEntity['type']) {
  const manifest = monsterAssetRegistryEntry(type)
  if (!manifest?.atlas) {
    return null
  }

  const asset = `/assets/monsters/${manifest.monsterId}/${manifest.atlas.image}`
  return manifest.atlas.revision ? withAssetRevision(asset, manifest.atlas.revision) : asset
}

export function resolveMonsterAtlasSource(type: MonsterEntity['type']): ObjectAtlasSource | null {
  const manifest = monsterAssetRegistryEntry(type)
  if (!manifest) {
    return null
  }

  return {
    assetId: manifest.monsterId,
    basePath: `/assets/monsters/${manifest.monsterId}`,
    atlas: manifest.atlas,
    fallbackUrl: resolveMonsterAtlasAsset(type),
    requiredFrames: monsterAnimationFrameNames(manifest),
  }
}

export function monsterAnimationFallback(key: MonsterAnimationKey, manifest: Pick<MonsterAssetManifest, 'animations'>): MonsterAnimationKey {
  if (manifest.animations[key]) {
    return key
  }

  if (key === 'death' && manifest.animations.hit) {
    return 'hit'
  }

  if ((key === 'attack' || key === 'hit' || key === 'roar') && manifest.animations.walk) {
    return 'walk'
  }

  return manifest.animations.idle ? 'idle' : Object.keys(manifest.animations)[0] as MonsterAnimationKey
}

function monsterDirectionFallback(direction: AssetDirection, manifest: MonsterAssetManifest): MonsterAnimationSelection['direction'] {
  if (manifest.directions.includes(direction as MonsterAnimationSelection['direction'])) {
    return direction as MonsterAnimationSelection['direction']
  }

  if (direction === 'n' || direction === 'e') {
    return 'ne'
  }

  if (direction === 's' || direction === 'w') {
    return 'sw'
  }

  return 'se'
}

function defaultMonsterAnimations(): MonsterAssetManifest['animations'] {
  return {
    idle: { fps: 6, frames: 8, loop: true },
    walk: { fps: 10, frames: 12, loop: true },
    attack: { fps: 12, frames: 10, loop: false },
    hit: { fps: 10, frames: 5, loop: false },
    death: { fps: 10, frames: 14, loop: false },
  }
}

function monsterAnimationFrameNames(manifest: MonsterAssetManifest): string[] {
  return Object.entries(manifest.animations).flatMap(([key, animation]) => {
    const frameCount = animation?.frames
    if (typeof frameCount !== 'number') {
      return []
    }
    const directions = animation.directions?.length ? animation.directions : manifest.directions
    return directions.flatMap((direction) => {
      const prefix = animation.framePrefix?.replace('{direction}', direction) ?? `${manifest.monsterId}_${key}_${direction}_`
      return Array.from({ length: frameCount }, (_, index) => `${prefix}${String(index).padStart(4, '0')}.png`)
    })
  })
}
