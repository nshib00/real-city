import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { listMonsters, toMonster } from '../../shared/api/monsters'

export function MonsterSync() {
  const viewport = useGameStore((state) => state.viewport)
  const setMonsters = useGameStore((state) => state.setMonsters)
  const query = useQuery({
    queryKey: ['monsters', viewport.center.x, viewport.center.y, viewport.radius],
    queryFn: () => listMonsters({ x: viewport.center.x, y: viewport.center.y, radius: viewport.radius * 48 }),
    retry: false,
    refetchInterval: 8000,
  })

  useEffect(() => {
    if (query.data) {
      setMonsters(query.data.monsters.map(toMonster))
    }
  }, [query.data, setMonsters])

  return null
}
