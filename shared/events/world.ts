import type { WorldTile } from '../src'
import type { AllianceEventType } from './alliance'
import type { ChatEventType } from './chat'

export type WorldEventType =
  | AllianceEventType
  | ChatEventType
  | 'world.tile.changed'
  | 'world.building.placed'
  | 'world.building.updated'
  | 'world.building.removed'
  | 'world.resource.changed'
  | 'economy.inventory.changed'
  | 'presence.changed'
  | 'presence.moved'
  | 'combat.resolved'
  | 'monster.spawned'
  | 'monster.moved'
  | 'monster.attacked'
  | 'monster.damaged'
  | 'monster.died'
  | 'monster.despawned'
  | 'monster.loot.dropped'
  | 'monster.loot.claimed'
  | 'cannon.shot'
  | 'defense.triggered'
  | 'tower.threat.detected'
  | 'alliance.created'
  | 'alliance.invite.created'
  | 'alliance.invite.accepted'
  | 'alliance.invite.declined'
  | 'alliance.role.changed'
  | 'alliance.treasury.donated'
  | 'alliance.buff.upgraded'
  | 'alliance.territory_aid.added'
  | 'chat.message.created'
  | 'chat.message.flagged'
  | 'market.order.created'
  | 'market.order.filled'
  | 'market.order.cancelled'
  | 'realtime.resync_required'

export type RealtimeEnvelope<TPayload = unknown> = {
  type: WorldEventType | 'ack' | 'error'
  event_id: string
  seq: number
  sent_at: string
  chunk_id?: string
  payload_version: number
  payload?: TPayload
  player_id?: string
  alliance_channel?: string
}

export type TileChangedPayload = {
  tile: WorldTile
  reason?: 'forest_cut' | 'forest_regrown'
}

export type BuildingPayload = {
  reason?: 'placed' | 'completed' | 'upgrade_started' | 'upgrade_completed' | 'rushed' | 'repair_started' | 'repaired' | 'relocated' | 'monster_attack'
  damage?: number
  building: {
    id: string
    owner_id: string
    type: string
    name: string
    level: number
    state: 'planned' | 'building' | 'active' | 'damaged' | 'ruined'
    health: number
    tower_watchkeeper_assigned?: boolean
    tile_x: number
    tile_y: number
    rotation?: number
    started_at: string
    completes_at: string | null
  }
}

export type BuildingRemovedPayload = {
  building_id: string
  reason?: 'cancelled' | 'demolished' | 'ruined' | 'moved' | 'monster_attack'
  damage?: number
  tile_x?: number
  tile_y?: number
  building_type?: string
}

export type ResourceChangedPayload = {
  node: {
    id: string
    type: string
    resource: string
    amount: number
    max_amount: number
    state: 'neutral' | 'claimed' | 'depleted'
    owner_id: string
    tile_x: number
    tile_y: number
    respawn_at: string | null
  }
}

export type PresencePayload = {
  player_id: string
  online: boolean
}

export type PresenceMovedPayload = {
  player: {
    player_id: string
    name: string
    level: number
    tile_x: number
    tile_y: number
  }
}

export type CannonShotPayload = {
  building_id: string
  building_type?: string
  monster_id: string
  damage: number
  damage_type?: string
  ammo: string
  tile_x?: number
  tile_y?: number
  target_tile_x?: number
  target_tile_y?: number
}

export type DefenseTriggeredPayload = {
  building_id: string
  building_type: string
  monster_id: string
  tile_x: number
  tile_y: number
}

export type TowerThreatPayload = {
  tower_id: string
  monster_id: string
  monster_type: string
  tile_x: number
  tile_y: number
  target_building_id: string
  detected_at: string
}
