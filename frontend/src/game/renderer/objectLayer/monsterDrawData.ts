import type { MonsterEntity } from '../../state/useGameStore'
import { healthRatio } from '../../health'
import type { AssetDirection, MonsterAnimationKey } from '../../renderers/assetManifestTypes'
import { monsterAssetRegistryEntry, monsterDisplayName, resolveMonsterAnimation, resolveMonsterAtlasSource } from '../../renderers/monsterAssetRegistry'
import { animationFrameIndex, animationPhaseOffsetMs } from './animationClock'
import { objectLayerSortKey } from './objectDepth'

type TileCoord = {
  x: number
  y: number
}

export type MonsterRenderMemory = {
  tile: TileCoord
  previousTile?: TileCoord
  observedAtMs: number
  direction: AssetDirection
  state: MonsterEntity['state']
  health: number
  updatedAt: number
  actionStartedAtMs: number
  hitStartedAtMs?: number
}

export type MonsterDrawCommand = {
  id: string
  monster: MonsterEntity
  label: string
  tile: TileCoord
  previousTile?: TileCoord
  displayTile: TileCoord
  direction: AssetDirection
  animationKey: MonsterAnimationKey
  frameName: string | null
  atlasUrl: string | null
  anchor: { x: number; y: number }
  size: { width: number; height: number }
  groundOffsetY: { atlas: number; preview: number }
  healthRatio: number
  sortKey: number
  selected: boolean
}

const DEFAULT_MONSTER_SPRITE = {
  width: 190,
  height: 190,
  anchorX: 0.5,
  anchorY: 0.9,
}

// The widest Colossus animation frame is 82 of 144 atlas pixels. At 420 px
// it projects to 239 px, inside the map's 240 px tile width.
const ANCIENT_COLOSSUS_SPRITE_SIZE = 420

// Opaque foot baselines measured from the idle/walk atlas frames (144 px) and
// preview PNGs (512 px). The atlas camera projects the far-facing feet higher.
// Recheck these values when monster images are regenerated.
const GROUND_CONTACT_PIXELS: Partial<Record<MonsterEntity['type'], { near: number; far: number; preview: number }>> = {
  roaming_melee: { near: 121, far: 114, preview: 431 },
  resource_guardian: { near: 134, far: 125, preview: 477 },
  ruins_guardian: { near: 116, far: 110, preview: 412 },
  forest_stalker: { near: 124, far: 117, preview: 442 },
  spore_beast: { near: 131, far: 124, preview: 469 },
  ironback_brute: { near: 135, far: 125, preview: 480 },
  ancient_colossus: { near: 118, far: 111, preview: 421 },
}

const MONSTER_ATLAS_FRAME_SIZE = 144
const MONSTER_PREVIEW_SIZE = 512
const MONSTER_MARKER_GROUND_Y = 5

const MOVEMENT_INTERPOLATION_MS = 420

export function monsterDrawCommands(
  monsters: readonly MonsterEntity[],
  options: {
    selectedMonsterId?: string | null
    previous?: ReadonlyMap<string, MonsterRenderMemory>
    nowMs?: number
    reducedMotion?: boolean
  } = {},
): MonsterDrawCommand[] {
  const nowMs = options.nowMs ?? Date.now()
  return monsters
    .map((monster) => monsterDrawCommand(monster, {
      selectedMonsterId: options.selectedMonsterId ?? null,
      previous: options.previous?.get(monster.id),
      nowMs,
      reducedMotion: options.reducedMotion,
    }))
    .sort((left, right) => left.sortKey - right.sortKey || left.id.localeCompare(right.id))
}

export function nextMonsterRenderMemory(
  monsters: readonly MonsterEntity[],
  previous: ReadonlyMap<string, MonsterRenderMemory>,
  nowMs = Date.now(),
): Map<string, MonsterRenderMemory> {
  const next = new Map<string, MonsterRenderMemory>()
  for (const monster of monsters) {
    const earlier = previous.get(monster.id)
    const direction = monsterDirection(monster, earlier)
    const tileChanged = !earlier || earlier.tile.x !== monster.tile.x || earlier.tile.y !== monster.tile.y
    next.set(monster.id, {
      tile: monster.tile,
      previousTile: tileChanged ? earlier?.tile : earlier.previousTile,
      observedAtMs: tileChanged ? nowMs : earlier.observedAtMs,
      direction,
      state: monster.state,
      health: monster.health,
      updatedAt: monster.updatedAt,
      actionStartedAtMs: !earlier || earlier.state !== monster.state || (monster.state === 'attacking' && earlier.updatedAt !== monster.updatedAt)
        ? nowMs : earlier.actionStartedAtMs,
      hitStartedAtMs: earlier && monster.health < earlier.health && monster.state !== 'dead' ? nowMs : earlier?.hitStartedAtMs,
    })
  }
  return next
}

export function monsterDrawCommand(
  monster: MonsterEntity,
  options: {
    selectedMonsterId: string | null
    previous?: MonsterRenderMemory
    nowMs: number
    reducedMotion?: boolean
  },
): MonsterDrawCommand {
  const direction = monsterDirection(monster, options.previous)
  const selection = resolveMonsterAnimation(monster, direction)
  const stateKey = selection?.key ?? 'idle'
  const hitDefinition = monsterAssetRegistryEntry(monster.type)?.animations.hit
  const hitStartedAtMs = options.previous?.hitStartedAtMs
  const showHit = monster.state !== 'dead' && hitDefinition && hitStartedAtMs !== undefined
    && options.nowMs - hitStartedAtMs < (hitDefinition.frames ?? 0) * 1000 / hitDefinition.fps
  const animationKey = showHit ? 'hit' : stateKey
  const animation = showHit ? hitDefinition : selection?.animation
  const phaseOffsetMs = animation?.loop
    ? animationPhaseOffsetMs(`${monster.id}:${animationKey}`, (animation.frames ?? 1) * (1000 / animation.fps))
    : -(showHit ? hitStartedAtMs ?? options.nowMs : options.previous?.actionStartedAtMs ?? options.nowMs)
  const frameIndex = animation && !options.reducedMotion
    ? animationFrameIndex({
      nowMs: options.nowMs,
      fps: animation.fps,
      frames: animation.frames,
      loop: animation.loop,
      phaseOffsetMs,
    })
    : 0
  const frameName = animation ? monsterFrameName(monster.type, animationKey, selection?.direction ?? direction, frameIndex, animation.framePrefix) : null
  const source = resolveMonsterAtlasSource(monster.type)
  const displayTile = options.reducedMotion ? monster.tile : interpolatedMonsterTile(monster, options.previous, options.nowMs)
  const isColossus = monster.type === 'ancient_colossus'
  // During death the body falls to one side. Center those two poses so their
  // 82 px wide silhouette still stays inside the 240 px tile width.
  const colossusAnchorX = animationKey === 'death' && direction === 'se' ? 63 / 144
    : animationKey === 'death' && direction === 'nw' ? 81 / 144
      : DEFAULT_MONSTER_SPRITE.anchorX

  return {
    id: monster.id,
    monster,
    label: `${monsterDisplayName(monster.type)} · ${monster.health}/${monster.maxHealth}`,
    tile: monster.tile,
    previousTile: options.previous?.previousTile,
    displayTile,
    direction,
    animationKey,
    frameName,
    atlasUrl: source?.fallbackUrl ?? null,
    anchor: { x: isColossus ? colossusAnchorX : DEFAULT_MONSTER_SPRITE.anchorX, y: isColossus ? 0.87 : DEFAULT_MONSTER_SPRITE.anchorY },
    size: { width: isColossus ? ANCIENT_COLOSSUS_SPRITE_SIZE : DEFAULT_MONSTER_SPRITE.width, height: isColossus ? ANCIENT_COLOSSUS_SPRITE_SIZE : DEFAULT_MONSTER_SPRITE.height },
    groundOffsetY: monsterGroundOffsetY(monster.type, direction),
    healthRatio: healthRatio(monster.health, monster.maxHealth),
    sortKey: objectLayerSortKey(displayTile, 0.35),
    selected: monster.id === options.selectedMonsterId,
  }
}

function monsterGroundOffsetY(type: MonsterEntity['type'], direction: AssetDirection) {
  const contact = GROUND_CONTACT_PIXELS[type]
  if (!contact) return { atlas: 0, preview: 0 } // The ember wisp flies above its ground marker.
  const height = type === 'ancient_colossus' ? ANCIENT_COLOSSUS_SPRITE_SIZE : DEFAULT_MONSTER_SPRITE.height
  const anchorY = type === 'ancient_colossus' ? 0.87 : DEFAULT_MONSTER_SPRITE.anchorY
  const farFacing = direction === 'nw' || direction === 'sw' || direction === 'n' || direction === 'w'
  return {
    atlas: MONSTER_MARKER_GROUND_Y + height * (anchorY - (farFacing ? contact.far : contact.near) / MONSTER_ATLAS_FRAME_SIZE),
    preview: MONSTER_MARKER_GROUND_Y + height * (anchorY - contact.preview / MONSTER_PREVIEW_SIZE),
  }
}

export function monsterDirection(monster: MonsterEntity, previous?: MonsterRenderMemory): AssetDirection {
  const from = previous?.previousTile ?? previous?.tile
  if (!from || (from.x === monster.tile.x && from.y === monster.tile.y)) {
    return previous?.direction ?? 'se'
  }

  const dx = monster.tile.x - from.x
  const dy = monster.tile.y - from.y
  if (dx > 0 && dy <= 0) {
    return 'ne'
  }
  if (dx >= 0 && dy > 0) {
    return 'se'
  }
  if (dx < 0 && dy >= 0) {
    return 'sw'
  }
  return 'nw'
}

function interpolatedMonsterTile(monster: MonsterEntity, previous: MonsterRenderMemory | undefined, nowMs: number): TileCoord {
  if (!previous?.previousTile) {
    return monster.tile
  }
  const progress = Math.min(1, Math.max(0, (nowMs - previous.observedAtMs) / MOVEMENT_INTERPOLATION_MS))
  if (progress >= 1) {
    return monster.tile
  }
  return {
    x: previous.previousTile.x + (monster.tile.x - previous.previousTile.x) * progress,
    y: previous.previousTile.y + (monster.tile.y - previous.previousTile.y) * progress,
  }
}

function monsterFrameName(type: MonsterEntity['type'], key: MonsterAnimationKey, direction: AssetDirection, frameIndex: number, framePrefix?: string) {
  const prefix = framePrefix?.replace('{direction}', direction) ?? `${type}_${key}_${direction}_`
  return `${prefix}${String(frameIndex).padStart(4, '0')}.png`
}
