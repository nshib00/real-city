import type { MarketOrderPayload } from '../../../shared/events/market'
import type { BuildingPayload, BuildingRemovedPayload, RealtimeEnvelope, ResourceChangedPayload, TileChangedPayload } from '../../../shared/events/world'
import { CHUNK_SIZE, WORLD_WRAP_TILES, tileToChunk } from '../game/coordinates/iso'
import { useGameStore } from '../game/state/useGameStore'
import { playCombatEvent } from '../features/world/combatAudio'
import { damageSound, placementMaterialVariant, placementSound, playBuildingSound } from '../features/buildings/buildingAudio'
import { useAuthStore } from '../features/auth/useAuthStore'
import { buildingImpactSound } from './soundPolicy'
import { spatialSound } from './spatialAudio'
import { playCombatSound } from './voiceManager'
import { playUiSound } from './playUiSound'

import { AudioEventWindow } from './eventWindow'

const seen = new AudioEventWindow(2000, 120_000)

function nearby(x: number, y: number): boolean {
  if (typeof document !== 'undefined' && document.hidden) return false
  const { viewport } = useGameStore.getState()
  const a = tileToChunk(viewport.center)
  const b = tileToChunk({ x, y })
  const chunks = WORLD_WRAP_TILES / CHUNK_SIZE
  const distance = (first: number, second: number) => {
    const delta = Math.abs(first - second) % chunks
    return Math.min(delta, chunks - delta)
  }
  return distance(a.x, b.x) <= viewport.radius && distance(a.y, b.y) <= viewport.radius
}

function buildingData(payload: BuildingPayload): { id: string; owner_id: string; type: string; state: string; health: number; max_health?: number; tile_x: number; tile_y: number } | null {
  const raw = payload.building as unknown as Record<string, unknown>
  if (!raw) return null
  const tile = raw.Tile as { X: number; Y: number } | undefined
  return {
    id: String(raw.id ?? raw.ID), owner_id: String(raw.owner_id ?? raw.OwnerID),
    type: String(raw.type ?? raw.Type), state: String(raw.state ?? raw.State),
    health: Number(raw.health ?? raw.Health),
    max_health: typeof raw.max_health === 'number' ? raw.max_health : undefined,
    tile_x: Number(raw.tile_x ?? tile?.X), tile_y: Number(raw.tile_y ?? tile?.Y),
  }
}

/** Один мост WS → звук. Вызывается до обновления authoritative state. */
export function playRealtimeAudio(event: RealtimeEnvelope): void {
  if (!event.event_id || event.type === 'ack' || event.type === 'error') return
  if (!seen.accept(event.event_id)) return
  const ownerId = useAuthStore.getState().player?.id
  const { viewport, camera } = useGameStore.getState()

  if (event.type.startsWith('monster.') || event.type === 'cannon.shot' || event.type === 'defense.triggered') {
    playCombatEvent(event)
    return
  }
  if (event.type === 'world.tile.changed') {
    const payload = event.payload as TileChangedPayload | undefined
    if (payload?.reason === 'forest_cut' && payload.tile && event.player_id !== ownerId) {
      const position = spatialSound(payload.tile, viewport.center, viewport.radius, camera.zoom)
      if (position.gain > 0) playCombatSound('world.forest.cut', position.gain, `${event.event_id}:forest`, position.pan)
    }
    return
  }
  if (event.type === 'world.building.placed' || event.type === 'world.building.updated') {
    const payload = event.payload as BuildingPayload | undefined
    if (!payload?.building) return
    const building = buildingData(payload)
    if (!building) return
    const previous = useGameStore.getState().buildings.find((item) => item.id === building.id)
    const owner = building.owner_id === ownerId
    const visible = nearby(building.tile_x, building.tile_y)
    if (payload.reason && (owner || visible)) {
      if (event.type === 'world.building.placed' && payload.reason === 'placed' && visible)
        playBuildingSound(placementSound(building.type, building.state), building.id, 'placed', 1200, placementMaterialVariant(building.type))
      if (payload.reason === 'upgrade_started' && visible) playBuildingSound('build.upgrade.started', building.id, 'upgrade_started')
      if (payload.reason === 'completed' || payload.reason === 'upgrade_completed')
        playBuildingSound(payload.reason === 'completed' ? 'build.completed' : 'build.upgrade.completed', building.id, 'completion', 1200, undefined, owner ? 1 : 0.5)
      if (payload.reason === 'rushed') playBuildingSound('build.rushed', building.id, 'rushed')
      if (payload.reason === 'repaired' && visible) playBuildingSound('build.repaired', building.id, 'repaired')
      if (payload.reason === 'repair_started' && visible) playBuildingSound('build.repair.started', building.id, 'repair_started')
    }
    if (visible || owner) {
      const sound = payload.reason === 'monster_attack' && (payload.damage ?? 0) > 0
        ? building.health <= 0 || building.state === 'ruined' ? 'build.damaged.ruined'
          : (payload.damage ?? 0) / Math.max(building.max_health ?? previous?.maxHealth ?? building.health, 1) >= 0.25
            ? 'build.damaged.heavy' : 'build.damaged.light'
        : damageSound(previous, building as Parameters<typeof damageSound>[1])
      if (sound && (visible || sound === 'build.damaged.ruined')) {
        playBuildingSound(sound, building.id, `damage:${event.event_id}`, 0)
        if (visible) {
          const position = spatialSound({ x: building.tile_x, y: building.tile_y }, viewport.center, viewport.radius, camera.zoom)
          playCombatSound(buildingImpactSound(building.type), position.gain * 0.65, `${event.event_id}:building-impact`, position.pan)
        }
      }
    }
    return
  }
  if (event.type === 'world.building.removed') {
    const payload = event.payload as BuildingRemovedPayload | undefined
    const previous = useGameStore.getState().buildings.find((item) => item.id === payload?.building_id)
    if (payload?.reason === 'monster_attack' && (payload.damage ?? 0) > 0) {
      const tile = payload.tile_x !== undefined && payload.tile_y !== undefined
        ? { x: payload.tile_x, y: payload.tile_y } : previous?.tile
      if (previous?.owner === ownerId || tile && nearby(tile.x, tile.y)) {
        playBuildingSound('build.damaged.ruined', payload.building_id, `damage:${event.event_id}`, 0)
        if (tile) {
          const position = spatialSound(tile, viewport.center, viewport.radius, camera.zoom)
          playCombatSound(buildingImpactSound(payload.building_type ?? previous?.kind ?? ''), position.gain * 0.65, `${event.event_id}:building-impact`, position.pan)
        }
      }
    }
    if (payload?.building_id && previous?.owner === ownerId) {
      if (payload.reason === 'cancelled') playBuildingSound('build.cancelled', payload.building_id, 'cancelled')
      if (payload.reason === 'demolished') playBuildingSound('build.demolished', payload.building_id, 'demolished')
    }
    return
  }
  if (event.type === 'world.resource.changed') {
    const payload = event.payload as ResourceChangedPayload | undefined
    const node = payload?.node
    const previous = useGameStore.getState().resourceNodes.find((item) => item.id === node?.id)
    if (node && previous?.state === 'depleted' && node.state === 'neutral' && nearby(node.tile_x, node.tile_y)) playUiSound('economy.node.respawned')
    return
  }
  if (event.type === 'market.order.filled') {
    const order = (event.payload as { order?: MarketOrderPayload } | undefined)?.order
    if (order && order.player_id === ownerId) playUiSound(order.side === 'buy' ? 'economy.market.bought' : 'economy.market.sold')
  }
}
