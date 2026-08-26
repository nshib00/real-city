import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { listResourceNodes } from '../../shared/api/economy'

export function ResourceNodeSync() {
  const setResourceNodes = useGameStore((state) => state.setResourceNodes)
  const query = useQuery({
    queryKey: ['resources', 'nodes'],
    queryFn: listResourceNodes,
    retry: false,
    refetchInterval: 15000,
  })

  useEffect(() => {
    if (query.data) {
      setResourceNodes(query.data.nodes.map((node) => ({
        id: node.id,
        type: node.type,
        resource: node.resource,
        amount: node.amount,
        maxAmount: node.max_amount,
        state: node.state,
        ownerId: node.owner_id,
        tile: { x: node.tile_x, y: node.tile_y },
        respawnAt: node.respawn_at ? Date.parse(node.respawn_at) : null,
      })))
    }
  }, [query.data, setResourceNodes])

  return null
}

