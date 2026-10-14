import { useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'

import { tileToChunk } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import { realtimeClient } from '../../shared/realtime/client'
import { toPlacedBuilding, type BuildingResponse } from '../../shared/api/buildings'
import type { ResourceNodeResponse } from '../../shared/api/economy'
import type { ChunksResponse } from '../../shared/api/world'
import type { MonsterResponse } from '../../shared/api/monsters'
import type { WorldTile } from '../../shared/contracts'
import type { MonsterPayload } from '../../../../shared/events/monster'
import type { RealtimeEnvelope, TileChangedPayload, BuildingPayload, BuildingRemovedPayload, ResourceChangedPayload } from '../../../../shared/events/world'

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
  const centerChunk = useMemo(() => tileToChunk(viewport.center), [viewport.center])
  const chunkIDs = useMemo(() => chunksAround(centerChunk, viewport.radius).map((chunk) => `${DEFAULT_WORLD_ID}:${chunk.x}:${chunk.y}`), [centerChunk, viewport.radius])

  useEffect(() => {
    const offStatus = realtimeClient.onStatus(setRealtimeStatus)
    const offEvent = realtimeClient.onEvent((event) => {
      applyRealtimeEvent(event, { queryClient, updateWorldTile, addBuilding, deleteBuilding, upsertResourceNode, upsertMonster })
    })
    realtimeClient.connect()
    return () => {
      offStatus()
      offEvent()
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
  switch (event.type) {
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
        const building = payload.building as BuildingResponse
        handlers.addBuilding(toPlacedBuilding(building))
        patchBuildingInQueryCache(handlers.queryClient, building)
      }
      return
    }
    case 'world.building.removed': {
      const payload = event.payload as BuildingRemovedPayload | undefined
      if (payload?.building_id) {
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
        handlers.upsertMonster(toMonsterEntity(payload.monster))
        patchMonsterInQueryCache(handlers.queryClient, payload.monster)
      }
      return
    }
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
  queryClient.setQueryData<{ buildings: BuildingResponse[] }>(['buildings'], (current) => {
    if (!current) {
      return current
    }
    return { ...current, buildings: upsertById(current.buildings, building) }
  })
}

function removeBuildingFromQueryCache(queryClient: QueryClient, buildingId: string) {
  queryClient.setQueryData<{ buildings: BuildingResponse[] }>(['buildings'], (current) => {
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

function chunksAround(center: { x: number; y: number }, radius: number) {
  const safeRadius = Math.max(1, Math.min(4, Math.round(radius)))
  const chunks: { x: number; y: number }[] = []
  for (let y = center.y - safeRadius; y <= center.y + safeRadius; y += 1) {
    for (let x = center.x - safeRadius; x <= center.x + safeRadius; x += 1) {
      chunks.push({ x, y })
    }
  }
  return chunks
}
