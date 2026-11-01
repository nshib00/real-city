import { useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'

import { visibleChunks } from '../../../../shared/world/coordinates'
import { CHUNK_SIZE, WORLD_WRAP_TILES, tileToChunk, wrappedGridDistance } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import { realtimeClient } from '../../shared/realtime/client'
import { toPlacedBuilding, type BuildingResponse } from '../../shared/api/buildings'
import type { ResourceNodeResponse } from '../../shared/api/economy'
import type { ChunksResponse } from '../../shared/api/world'
import type { MonsterResponse } from '../../shared/api/monsters'
import type { NearbyPlayer } from '../../shared/api/playerPresence'
import type { WorldTile } from '../../shared/contracts'
import type { MonsterPayload } from '../../../../shared/events/monster'
import { playRealtimeAudio } from '../../audio/realtimeAudio'
import { useAuthStore } from '../auth/useAuthStore'
import { showToast } from '../notifications/toast'
import type { CombatRecord } from '../../../../shared/events/combat'
import type { MarketOrderPayload } from '../../../../shared/events/market'
import type { RealtimeEnvelope, TileChangedPayload, BuildingPayload, BuildingRemovedPayload, ResourceChangedPayload, PresenceMovedPayload } from '../../../../shared/events/world'

const DEFAULT_WORLD_ID = 'dev-world'

export function useWorldRealtime() {
  const queryClient = useQueryClient()
  const viewport = useGameStore((state) => state.viewport)
  const updateWorldTile = useGameStore((state) => state.updateWorldTile)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const deleteBuilding = useGameStore((state) => state.deleteBuilding)
  const upsertResourceNode = useGameStore((state) => state.upsertResourceNode)
  const upsertMonster = useGameStore((state) => state.upsertMonster)
  const setRealtimeStatus = useGameStore((state) => state.setRealtimeStatus)
  const centerChunk = useMemo(() => tileToChunk(viewport.center), [viewport.center.x, viewport.center.y])
  const chunkIDs = useMemo(() => chunksAround(centerChunk, viewport.radius).map((chunk) => `${DEFAULT_WORLD_ID}:${chunk.x}:${chunk.y}`), [centerChunk.x, centerChunk.y, viewport.radius])

  useEffect(() => {
    const pending: RealtimeEnvelope[] = []
    let frame: number | null = null
    let resyncTimer: number | null = null
    let lastResyncAt = 0
    let resyncAll = false
    const flush = () => {
      frame = null
      for (const event of pending.splice(0)) {
        playRealtimeAudio(event)
        applyRealtimeEvent(event, { queryClient, updateWorldTile, addBuilding, deleteBuilding, upsertResourceNode, upsertMonster })
      }
    }
    const resync = (reason: 'reconnect' | 'gap' | 'subscription') => {
      if (reason !== 'subscription') resyncAll = true
      if (resyncTimer !== null) return
      resyncTimer = window.setTimeout(() => {
        resyncTimer = null
        lastResyncAt = Date.now()
        const worldQueries = [
          ['world', 'chunks'], ['buildings'], ['resources', 'nodes'], ['monsters'], ['players', 'nearby'],
          ['monster-loot'],
        ]
        for (const queryKey of !resyncAll ? worldQueries : [
          ...worldQueries, ['economy', 'inventory'], ['economy', 'population'], ['production', 'jobs'], ['repairs'], ['chat'], ['alliances', 'me'], ['combat', 'history'],
        ]) {
          void queryClient.invalidateQueries({ queryKey, refetchType: 'active' })
        }
        resyncAll = false
      }, Math.max(0, 1000 - (Date.now() - lastResyncAt)))
    }
    const offStatus = realtimeClient.onStatus(setRealtimeStatus)
    const offResync = realtimeClient.onResync(resync)
    const offEvent = realtimeClient.onEvent((event) => {
      if (event.type === 'ack') return
      pending.push(event)
      if (document.hidden) {
        if (frame !== null) window.cancelAnimationFrame(frame)
        flush()
      } else if (frame === null) {
        frame = window.requestAnimationFrame(flush)
      }
    })
    realtimeClient.connect()
    return () => {
      offStatus()
      offResync()
      offEvent()
      if (frame !== null) window.cancelAnimationFrame(frame)
      if (resyncTimer !== null) window.clearTimeout(resyncTimer)
    }
  }, [addBuilding, deleteBuilding, queryClient, setRealtimeStatus, upsertMonster, upsertResourceNode, updateWorldTile])

  useEffect(() => {
    realtimeClient.subscribeChunks(chunkIDs)
  }, [chunkIDs])
}

export function applyRealtimeEvent(
  event: RealtimeEnvelope,
  handlers: {
    queryClient: ReturnType<typeof useQueryClient>
    updateWorldTile: ReturnType<typeof useGameStore.getState>['updateWorldTile']
    addBuilding: ReturnType<typeof useGameStore.getState>['addBuilding']
    deleteBuilding: ReturnType<typeof useGameStore.getState>['deleteBuilding']
    upsertResourceNode: ReturnType<typeof useGameStore.getState>['upsertResourceNode']
    upsertMonster: ReturnType<typeof useGameStore.getState>['upsertMonster']
  },
) {
  if (event.type.startsWith('chat.')) {
    void handlers.queryClient.invalidateQueries({ queryKey: ['chat'] })
    return
  }
  if (event.type.startsWith('alliance.')) {
    void handlers.queryClient.invalidateQueries({ queryKey: ['alliances', 'me'] })
    if (event.type === 'alliance.member.left' || event.type === 'alliance.member.kicked') {
      handlers.queryClient.setQueriesData({ queryKey: ['chat', 'alliance'] }, { messages: [], read_state: { unread: 0, read_at: '' } })
      handlers.queryClient.removeQueries({ queryKey: ['chat', 'alliance'] })
    }
    void handlers.queryClient.invalidateQueries({ queryKey: ['chat'] })
    return
  }
  if (event.type.startsWith('market.order.')) {
    void handlers.queryClient.invalidateQueries({ queryKey: ['market', 'orders'] })
    void handlers.queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
  }
  switch (event.type) {
    case 'combat.resolved': {
      const record = event.payload as CombatRecord | undefined
      void handlers.queryClient.invalidateQueries({ queryKey: ['combat', 'history'] })
      if (record && record.owner_id === useAuthStore.getState().player?.id) {
        if (useAuthStore.getState().player?.profile.settings.notifications.attack_alerts !== false) {
          showToast('warning', `${record.destroyed ? 'Уничтожена' : 'Атакована'} ваша постройка: ${record.building_type}. Урон: ${record.damage}.`)
        }
      }
      return
    }
    case 'presence.moved': {
      const player = (event.payload as PresenceMovedPayload | undefined)?.player
      if (!player?.player_id || player.player_id === useAuthStore.getState().player?.id) return
      for (const [key] of handlers.queryClient.getQueriesData<{ players: NearbyPlayer[] }>({ queryKey: ['players', 'nearby'] })) {
        const [, , x, y, radius] = key
        handlers.queryClient.setQueryData<{ players: NearbyPlayer[] }>(key, (current) => {
          if (!current) return current
          const remaining = current.players.filter((item) => item.player_id !== player.player_id)
          const inRange = typeof x === 'number' && typeof y === 'number' && typeof radius === 'number'
            && wrappedGridDistance(x, player.tile_x) <= radius && wrappedGridDistance(y, player.tile_y) <= radius
          return { players: inRange ? [...remaining, player] : remaining }
        })
      }
      return
    }
    case 'world.tile.changed': {
      const payload = event.payload as TileChangedPayload | undefined
      if (payload?.tile) {
        handlers.updateWorldTile(payload.tile)
        patchWorldTileInQueryCache(handlers.queryClient, payload.tile)
      }
      return
    }
    case 'world.building.placed':
    case 'world.building.updated': {
      const payload = event.payload as BuildingPayload | undefined
      if (payload?.building) {
        const rawBuilding = !('id' in payload.building)
        const building = normalizeBuildingEvent(payload.building)
        const previous = useGameStore.getState().buildings.find((item) => item.id === building.id)
        const damage = payload.damage ?? (previous ? Math.max(0, previous.health - building.health) : 0)
        if (payload.reason === 'monster_attack' && damage > 0) {
          useGameStore.getState().recordBuildingDamage({
            id: event.event_id, buildingId: building.id, tile: { x: building.tile_x, y: building.tile_y },
            damage, createdAt: Date.now(),
          })
        }
        handlers.addBuilding(toPlacedBuilding(building))
        patchBuildingInQueryCache(handlers.queryClient, building)
        void handlers.queryClient.invalidateQueries({ queryKey: ['repairs', building.id] })
        if (rawBuilding) void handlers.queryClient.invalidateQueries({ queryKey: ['buildings'] })
      }
      return
    }
    case 'world.building.removed': {
      const payload = event.payload as BuildingRemovedPayload | undefined
      if (payload?.building_id) {
        const previous = useGameStore.getState().buildings.find((item) => item.id === payload.building_id)
        const damage = payload.damage ?? previous?.health ?? 0
        const tile = payload.tile_x !== undefined && payload.tile_y !== undefined
          ? { x: payload.tile_x, y: payload.tile_y } : previous?.tile
        if (payload.reason === 'monster_attack' && damage > 0 && tile) {
          useGameStore.getState().recordBuildingDamage({
            id: event.event_id, buildingId: payload.building_id, tile,
            damage, createdAt: Date.now(),
          })
        }
        handlers.deleteBuilding(payload.building_id)
        removeBuildingFromQueryCache(handlers.queryClient, payload.building_id)
      }
      return
    }
    case 'world.resource.changed': {
      const payload = event.payload as ResourceChangedPayload | undefined
      if (payload?.node) {
        const node = payload.node
        handlers.upsertResourceNode(toResourceNode(node))
        patchResourceNodeInQueryCache(handlers.queryClient, node)
      }
      return
    }
    case 'monster.spawned':
    case 'monster.moved':
    case 'monster.attacked':
    case 'monster.damaged':
    case 'monster.died':
    case 'monster.despawned': {
      const payload = event.payload as MonsterPayload | undefined
      if (payload?.monster) {
        if ((event.type === 'monster.damaged' || event.type === 'monster.died') && payload.damage && payload.damage > 0) {
          const monster = payload.monster
          const tile = monster.Tile ? { x: monster.Tile.X, y: monster.Tile.Y } : { x: monster.tile_x ?? 0, y: monster.tile_y ?? 0 }
          useGameStore.getState().recordMonsterDamage({ id: event.event_id, monsterId: monster.id, tile, damage: payload.damage, createdAt: Date.now() })
        }
        if (payload.monster.state !== 'dead' && useGameStore.getState().deadMonsterIds.has(payload.monster.id)) return
        handlers.upsertMonster(toMonsterEntity(payload.monster))
        patchMonsterInQueryCache(handlers.queryClient, payload.monster)
      }
      return
    }
    case 'monster.loot.dropped':
    case 'monster.loot.claimed': {
      void handlers.queryClient.invalidateQueries({ queryKey: ['monster-loot'] })
      return
    }
    case 'cannon.shot': {
      const payload = event.payload as { building_id: string; building_type?: BuildingResponse['type']; monster_id: string; damage: number; ammo: string } | undefined
      if (payload) useGameStore.getState().recordCannonShot({
        id: event.event_id, buildingId: payload.building_id, monsterId: payload.monster_id,
        damage: payload.damage, ammo: payload.ammo,
        ...(payload.building_type ? { kind: payload.building_type } : {}),
      })
      return
    }
    case 'economy.inventory.changed': {
      void handlers.queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      return
    }
    case 'market.order.filled': {
      const order = (event.payload as { order?: MarketOrderPayload } | undefined)?.order
      if (order && order.player_id === useAuthStore.getState().player?.id) {
        void handlers.queryClient.invalidateQueries({ queryKey: ['market', 'orders'] })
        void handlers.queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      }
      return
    }
  }
}

function normalizeBuildingEvent(value: BuildingPayload['building']): BuildingResponse {
  if ('id' in value) return value as BuildingResponse
  const raw = value as unknown as Record<string, unknown>
  const tile = raw.Tile as { X: number; Y: number }
  const footprint = raw.Footprint as { Width?: number; Height?: number } | undefined
  const previous = useGameStore.getState().buildings.find((item) => item.id === raw.ID)
  return {
    id: String(raw.ID), owner_id: String(raw.OwnerID), type: raw.Type as BuildingResponse['type'],
    name: String(raw.Name), level: Number(raw.Level), state: raw.State as BuildingResponse['state'],
    health: Number(raw.Health), max_health: previous?.maxHealth,
    tile_x: tile.X, tile_y: tile.Y, rotation: Number(raw.Rotation ?? 0),
    footprint_w: Number(footprint?.Width ?? previous?.footprintW ?? 1),
    footprint_h: Number(footprint?.Height ?? previous?.footprintH ?? 1),
    started_at: String(raw.StartedAt),
    created_at: raw.CreatedAt ? String(raw.CreatedAt) : undefined,
    completes_at: raw.CompletesAt ? String(raw.CompletesAt) : null,
    cannon_enabled: Boolean(raw.CannonEnabled),
    cannon_next_attack_at: raw.CannonNextAttackAt ? String(raw.CannonNextAttackAt) : null,
    cannon_target_id: String(raw.CannonTargetID ?? ''),
    cannon_range: previous?.cannonRange, cannon_damage: previous?.cannonDamage,
    cannon_ammo: previous?.cannonAmmo, demolition_refund_coins: previous?.demolitionRefundCoins,
    cannon_cooldown_seconds: previous?.cannonCooldownSeconds, cannon_damage_type: previous?.cannonDamageType,
    trap_charges: Number(raw.TrapCharges ?? previous?.trapCharges ?? 0), trap_max_charges: previous?.trapMaxCharges, trap_damage: previous?.trapDamage,
    defense_slots: previous?.defenseSlots, defense_patrol_radius: previous?.defensePatrolRadius, defense_staff_role: previous?.defenseStaffRole,
  }
}

function patchWorldTileInQueryCache(queryClient: QueryClient, tile: WorldTile) {
  queryClient.setQueriesData<ChunksResponse>({ queryKey: ['world', 'chunks'] }, (current) => {
    if (!current) {
      return current
    }
    let changed = false
    const chunks = current.chunks.map((chunk) => {
      let chunkChanged = false
      const tiles = chunk.tiles.map((item) => {
        if (item.x !== tile.x || item.y !== tile.y) {
          return item
        }
        changed = true
        chunkChanged = true
        return { ...item, ...tile }
      })
      return chunkChanged ? { ...chunk, tiles } : chunk
    })
    return changed ? { ...current, chunks } : current
  })
}

function patchBuildingInQueryCache(queryClient: QueryClient, building: BuildingResponse) {
  queryClient.setQueriesData<{ buildings: BuildingResponse[] }>({ queryKey: ['buildings'] }, (current) => {
    if (!current) {
      return current
    }
    return { ...current, buildings: upsertById(current.buildings, building) }
  })
}

function removeBuildingFromQueryCache(queryClient: QueryClient, buildingId: string) {
  queryClient.setQueriesData<{ buildings: BuildingResponse[] }>({ queryKey: ['buildings'] }, (current) => {
    if (!current) {
      return current
    }
    return { ...current, buildings: removeById(current.buildings, buildingId) }
  })
}

function patchResourceNodeInQueryCache(queryClient: QueryClient, node: ResourceNodeResponse) {
  queryClient.setQueriesData<{ nodes: ResourceNodeResponse[] }>({ queryKey: ['resources', 'nodes'] }, (current) => {
    if (!current) {
      return current
    }
    return { ...current, nodes: upsertById(current.nodes, node) }
  })
}

function patchMonsterInQueryCache(queryClient: QueryClient, monster: MonsterPayload['monster']) {
  const normalized = toMonsterResponse(monster)
  queryClient.setQueriesData<{ monsters: MonsterResponse[] }>({ queryKey: ['monsters'] }, (current) => {
    if (!current) {
      return current
    }
    return {
      ...current,
      monsters: normalized.state === 'dead' ? removeById(current.monsters, normalized.id) : upsertById(current.monsters, normalized),
    }
  })
}

function toResourceNode(node: ResourceNodeResponse) {
  return {
    id: node.id,
    type: node.type,
    resource: node.resource,
    amount: node.amount,
    maxAmount: node.max_amount,
    state: node.state,
    ownerId: node.owner_id,
    tile: { x: node.tile_x, y: node.tile_y },
    respawnAt: node.respawn_at ? Date.parse(node.respawn_at) : null,
  }
}

function toMonsterEntity(monster: MonsterPayload['monster']) {
  const tile = monster.Tile ? { x: monster.Tile.X, y: monster.Tile.Y } : { x: monster.tile_x ?? 0, y: monster.tile_y ?? 0 }
  return {
    id: monster.id,
    creatorId: monster.creator_id,
    expiresAt: monster.expires_at ? Date.parse(monster.expires_at) : undefined,
    type: monster.type,
    state: monster.state,
    tile,
    targetId: monster.target_id ?? monster.TargetID ?? '',
    targetType: monster.target_type ?? monster.TargetType ?? '',
    health: monster.health,
    maxHealth: monster.max_health ?? monster.MaxHealth ?? monster.health,
    damage: monster.damage,
    aggroRadius: monster.aggro_radius ?? monster.AggroRadius ?? 0,
    updatedAt: Date.parse(monster.updated_at ?? monster.UpdatedAt ?? new Date().toISOString()),
  }
}

function toMonsterResponse(monster: MonsterPayload['monster']): MonsterResponse {
  return {
    id: monster.id,
    creator_id: monster.creator_id,
    expires_at: monster.expires_at,
    type: monster.type,
    state: monster.state,
    tile_x: monster.Tile?.X ?? monster.tile_x ?? 0,
    tile_y: monster.Tile?.Y ?? monster.tile_y ?? 0,
    target_id: monster.target_id ?? monster.TargetID ?? '',
    target_type: monster.target_type ?? monster.TargetType ?? '',
    health: monster.health,
    max_health: monster.max_health ?? monster.MaxHealth ?? monster.health,
    damage: monster.damage,
    aggro_radius: monster.aggro_radius ?? monster.AggroRadius ?? 0,
    updated_at: monster.updated_at ?? monster.UpdatedAt ?? new Date().toISOString(),
  }
}

function upsertById<T extends { id: string }>(items: T[], item: T) {
  const index = items.findIndex((current) => current.id === item.id)
  if (index === -1) {
    return [...items, item]
  }
  const next = items.slice()
  next[index] = item
  return next
}

function removeById<T extends { id: string }>(items: T[], id: string) {
  const index = items.findIndex((item) => item.id === id)
  if (index === -1) {
    return items
  }
  return [...items.slice(0, index), ...items.slice(index + 1)]
}

function chunksAroundLegacy(center: { x: number; y: number }, radius: number) {
  const safeRadius = Math.max(1, Math.min(3, Math.round(radius)))
  const worldChunks = WORLD_WRAP_TILES / CHUNK_SIZE
  const chunks: { x: number; y: number }[] = []
  const seen = new Set<string>()
  for (let y = center.y - safeRadius; y <= center.y + safeRadius; y += 1) {
    for (let x = center.x - safeRadius; x <= center.x + safeRadius; x += 1) {
      const chunk = { x: ((x % worldChunks) + worldChunks) % worldChunks, y: ((y % worldChunks) + worldChunks) % worldChunks }
      const key = `${chunk.x}:${chunk.y}`
      if (!seen.has(key)) {
        seen.add(key)
        chunks.push(chunk)
      }
    }
  }
  return chunks
}

function chunksAround(center: { x: number; y: number }, radius: number) { return visibleChunks(center, Math.max(1, Math.min(3, Math.round(radius)))) }
