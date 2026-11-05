import type { MonsterPayload } from '../../../../shared/events/monster'
import type { CannonShotPayload, DefenseTriggeredPayload, RealtimeEnvelope } from '../../../../shared/events/world'
import { combatDistanceGain, defenseSound, weaponSound } from '../../audio/soundPolicy'
import { spatialSound } from '../../audio/spatialAudio'
import { playCombatSound } from '../../audio/voiceManager'
import type { SoundId } from '../../audio/soundEvents'
import { wrappedGridDistance } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'

const monsterKinds = new Set(['roaming_melee', 'resource_guardian', 'ruins_guardian', 'forest_stalker', 'spore_beast', 'ironback_brute', 'ember_wisp', 'ancient_colossus'])
const MONSTER_AUDIO_RADIUS_TILES = 6

function gainAt(tile: { x: number; y: number } | undefined): number {
  if (typeof document !== 'undefined' && document.hidden) return 0
  const { viewport } = useGameStore.getState()
  return combatDistanceGain(tile, viewport.center, viewport.radius)
}

function monsterGainAt(tile: { x: number; y: number } | undefined): number {
  if (!tile || (typeof document !== 'undefined' && document.hidden)) return 0
  const { viewport } = useGameStore.getState()
  const distance = Math.hypot(
    wrappedGridDistance(tile.x, viewport.center.x),
    wrappedGridDistance(tile.y, viewport.center.y),
  )
  if (distance > MONSTER_AUDIO_RADIUS_TILES) return 0
  return Math.max(0.12, 1 - distance / MONSTER_AUDIO_RADIUS_TILES)
}

function panAt(tile: { x: number; y: number } | undefined): number {
  const { viewport, camera } = useGameStore.getState()
  return spatialSound(tile, viewport.center, viewport.radius, camera.zoom).pan
}

export function monsterActionSound(type: string, action: 'aggro' | 'attack' | 'hit' | 'death'): SoundId {
  return monsterKinds.has(type) ? `combat.monster.${type}.${action}` as SoundId : `combat.monster.${action}`
}

export function playCombatEvent(event: RealtimeEnvelope): void {
  if (event.type === 'cannon.shot') {
    const shot = event.payload as CannonShotPayload | undefined
    if (!shot?.building_id) return
    const known = useGameStore.getState().buildings.find((item) => item.id === shot.building_id)
    const tile = shot.tile_x !== undefined && shot.tile_y !== undefined ? { x: shot.tile_x, y: shot.tile_y } : known?.tile
    playCombatSound(weaponSound(shot.building_type ?? known?.kind ?? ''), gainAt(tile), `${event.event_id}:shot`, panAt(tile))
    if (shot.target_tile_x !== undefined && shot.target_tile_y !== undefined) {
      const target = { x: shot.target_tile_x, y: shot.target_tile_y }
      playCombatSound('combat.impact.flesh', gainAt(target), `${event.event_id}:impact`, panAt(target))
    }
    return
  }
  if (event.type === 'defense.triggered') {
    const trigger = event.payload as DefenseTriggeredPayload | undefined
    if (!trigger) return
    const id = defenseSound(trigger.building_type)
    if (id) {
      const tile = { x: trigger.tile_x, y: trigger.tile_y }
      playCombatSound(id, gainAt(tile), `${event.event_id}:trigger`, panAt(tile))
    }
    return
  }
  if (event.type === 'monster.loot.dropped' || event.type === 'monster.loot.claimed') {
    const payload = event.payload as { loot?: { Tile?: { X: number; Y: number }; tile_x?: number; tile_y?: number } } | undefined
    const loot = payload?.loot
    if (event.type === 'monster.loot.dropped' && loot) {
      const tile = loot.Tile ? { x: loot.Tile.X, y: loot.Tile.Y } : loot.tile_x !== undefined && loot.tile_y !== undefined ? { x: loot.tile_x, y: loot.tile_y } : undefined
      playCombatSound('combat.loot.dropped', gainAt(tile), `${event.event_id}:loot`, panAt(tile))
    }
    return
  }
  if (!event.type.startsWith('monster.')) return
  const payload = event.payload as MonsterPayload | undefined
  const monster = payload?.monster
  if (!monster) return
  const tile = monster.Tile ? { x: monster.Tile.X, y: monster.Tile.Y } : monster.tile_x !== undefined && monster.tile_y !== undefined ? { x: monster.tile_x, y: monster.tile_y } : undefined
  const gain = monsterGainAt(tile)
  if (!gain) return
  const pan = panAt(tile)
  const previous = useGameStore.getState().monsters.find((item) => item.id === monster.id)
  const ownerId = useAuthStore.getState().player?.id
  const targetId = monster.target_id ?? monster.TargetID
  const ownTarget = useGameStore.getState().buildings.some((item) => item.id === targetId && item.owner === ownerId)
  if (payload.source === 'player' && event.player_id !== ownerId && (event.type === 'monster.damaged' || event.type === 'monster.died')) {
    playCombatSound('combat.player.attack', gain, `${event.event_id}:player-attack`, pan)
  }
  if (event.type === 'monster.moved') {
    if (monster.state === 'aggro' && previous && (previous.state === 'idle' || previous.state === 'wandering')) {
      playCombatSound(monsterActionSound(monster.type, 'aggro'), gain, `${event.event_id}:aggro`, pan)
      if (ownTarget) playCombatSound('combat.threat.nearby', 1, `${event.event_id}:threat`)
    } else if (monster.state === 'wandering' && previous?.state === 'aggro' && previous.targetId) {
      const wasOwnTarget = useGameStore.getState().buildings.some((item) => item.id === previous.targetId && item.owner === ownerId)
      if (wasOwnTarget) playCombatSound('combat.retreat', gain, `${event.event_id}:retreat`, pan)
    } else if (previous && tile && (previous.tile.x !== tile.x || previous.tile.y !== tile.y)) {
      playCombatSound('combat.monster.step', gain * 0.55, `${event.event_id}:step`, pan)
    } else if (monster.state === 'idle') {
      playCombatSound('combat.monster.idle', gain * 0.3, `${event.event_id}:idle`, pan)
    }
  } else if (event.type === 'monster.attacked') {
    playCombatSound(monsterActionSound(monster.type, 'attack'), gain, `${event.event_id}:attack`, pan)
    if (ownTarget) playCombatSound('combat.threat.nearby', 1, `${event.event_id}:threat-attack`)
  } else if (event.type === 'monster.damaged') {
    if (!ownerId || event.player_id !== ownerId) playCombatSound(monsterActionSound(monster.type, 'hit'), gain, `${event.event_id}:hit`, pan)
  } else if (event.type === 'monster.died') {
    playCombatSound(monsterActionSound(monster.type, 'death'), gain, `${event.event_id}:death`, pan)
    if (ownerId && event.player_id === ownerId) playCombatSound('combat.victory', 1, `${event.event_id}:victory`)
  }
}
