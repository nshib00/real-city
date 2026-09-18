import type { WorldTile } from '../src'

export type WorldEventType =
  | 'world.tile.changed'
  | 'world.building.placed'
  | 'world.building.updated'
  | 'world.building.removed'
  | 'world.resource.changed'
  | 'presence.changed'
  | 'combat.resolved'
  | 'monster.spawned'
  | 'monster.moved'
  | 'monster.attacked'
  | 'monster.damaged'
  | 'monster.died'
  | 'monster.despawned'
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
}

export type BuildingPayload = {
  building: {
    id: string
    owner_id: string
    type: string
    name: string
    level: number
    state: 'planned' | 'building' | 'active' | 'damaged' | 'ruined'
    health: number
    tile_x: number
    tile_y: number
    started_at: string
    completes_at: string | null
  }
}

export type BuildingRemovedPayload = {
  building_id: string
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
