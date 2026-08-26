import { useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { tileToChunk } from '../../game/coordinates/iso'
import { useGameStore } from '../../game/state/useGameStore'
import { realtimeClient } from '../../shared/realtime/client'
import { toPlacedBuilding, type BuildingResponse } from '../../shared/api/buildings'
import type { ResourceNodeResponse } from '../../shared/api/economy'
import type { RealtimeEnvelope, TileChangedPayload, BuildingPayload, BuildingRemovedPayload, ResourceChangedPayload } from '../../../../shared/events/world'

const DEFAULT_WORLD_ID = 'dev-world'

export function useWorldRealtime() {
  const queryClient = useQueryClient()
  const viewport = useGameStore((state) => state.viewport)
  const updateWorldTile = useGameStore((state) => state.updateWorldTile)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const deleteBuilding = useGameStore((state) => state.deleteBuilding)
  const upsertResourceNode = useGameStore((state) => state.upsertResourceNode)
  const setRealtimeStatus = useGameStore((state) => state.setRealtimeStatus)
  const centerChunk = useMemo(() => tileToChunk(viewport.center), [viewport.center])
  const chunkIDs = useMemo(() => chunksAround(centerChunk, viewport.radius).map((chunk) => `${DEFAULT_WORLD_ID}:${chunk.x}:${chunk.y}`), [centerChunk, viewport.radius])

  useEffect(() => {
    const offStatus = realtimeClient.onStatus(setRealtimeStatus)
    const offEvent = realtimeClient.onEvent((event) => {
      applyRealtimeEvent(event, { queryClient, updateWorldTile, addBuilding, deleteBuilding, upsertResourceNode })
    })
    realtimeClient.connect()
    return () => {
      offStatus()
      offEvent()
    }
  }, [addBuilding, deleteBuilding, queryClient, setRealtimeStatus, upsertResourceNode, updateWorldTile])

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
  },
) {
  switch (event.type) {
    case 'world.tile.changed': {
      const payload = event.payload as TileChangedPayload | undefined
      if (payload?.tile) {
        handlers.updateWorldTile(payload.tile)
        void handlers.queryClient.invalidateQueries({ queryKey: ['world'] })
      }
      return
    }
    case 'world.building.placed':
    case 'world.building.updated': {
      const payload = event.payload as BuildingPayload | undefined
      if (payload?.building) {
        handlers.addBuilding(toPlacedBuilding(payload.building as BuildingResponse))
        void handlers.queryClient.invalidateQueries({ queryKey: ['buildings'] })
      }
      return
    }
    case 'world.building.removed': {
      const payload = event.payload as BuildingRemovedPayload | undefined
      if (payload?.building_id) {
        handlers.deleteBuilding(payload.building_id)
        void handlers.queryClient.invalidateQueries({ queryKey: ['buildings'] })
      }
      return
    }
    case 'world.resource.changed': {
      const payload = event.payload as ResourceChangedPayload | undefined
      if (payload?.node) {
        handlers.upsertResourceNode(toResourceNode(payload.node))
        void handlers.queryClient.invalidateQueries({ queryKey: ['resources'] })
      }
      return
    }
  }
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
