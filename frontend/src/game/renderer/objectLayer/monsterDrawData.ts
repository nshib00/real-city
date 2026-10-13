import type { MonsterEntity } from '../../state/useGameStore'
import type { AssetDirection, MonsterAnimationKey } from '../../renderers/assetManifestTypes'
import { monsterDisplayName, resolveMonsterAnimation, resolveMonsterAtlasSource } from '../../renderers/monsterAssetRegistry'
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
  healthRatio: number
  sortKey: number
  selected: boolean
}

const DEFAULT_MONSTER_SPRITE = {
  width: 180,
  height: 210,
  anchorX: 0.5,
  anchorY: 0.9,
}

const MOVEMENT_INTERPOLATION_MS = 420

export function monsterDrawCommands(
  monsters: readonly MonsterEntity[],
  options: {
    selectedMonsterId?: string | null
    previous?: ReadonlyMap<string, MonsterRenderMemory>
    nowMs?: number
  } = {},
): MonsterDrawCommand[] {
  const nowMs = options.nowMs ?? Date.now()
  return monsters
    .map((monster) => monsterDrawCommand(monster, {
      selectedMonsterId: options.selectedMonsterId ?? null,
      previous: options.previous?.get(monster.id),
      nowMs,
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
  },
): MonsterDrawCommand {
  const direction = monsterDirection(monster, options.previous)
  const selection = resolveMonsterAnimation(monster, direction)
  const animationKey = selection?.key ?? 'idle'
  const animation = selection?.animation
  const phaseOffsetMs = animationPhaseOffsetMs(`${monster.id}:${animationKey}`, animation ? (animation.frames ?? 1) * (1000 / animation.fps) : 1000)
  const frameIndex = animation
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
  const displayTile = interpolatedMonsterTile(monster, options.previous, options.nowMs)

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
    anchor: { x: DEFAULT_MONSTER_SPRITE.anchorX, y: DEFAULT_MONSTER_SPRITE.anchorY },
    size: { width: monster.type === 'ancient_colossus' ? 230 : DEFAULT_MONSTER_SPRITE.width, height: monster.type === 'ancient_colossus' ? 270 : DEFAULT_MONSTER_SPRITE.height },
    healthRatio: healthRatio(monster),
    sortKey: objectLayerSortKey(displayTile, 0.35),
    selected: monster.id === options.selectedMonsterId,
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

function healthRatio(monster: MonsterEntity) {
  if (monster.maxHealth <= 0) {
    return 0
  }
  return Math.max(0, Math.min(1, monster.health / monster.maxHealth))
}
