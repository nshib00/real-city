import { useEffect } from 'react'

import { useGameStore } from '../../game/state/useGameStore'

export function ConstructionTicker() {
  const tickConstructions = useGameStore((state) => state.tickConstructions)

  useEffect(() => {
    const interval = window.setInterval(() => tickConstructions(Date.now()), 1000)
    tickConstructions(Date.now())
    return () => window.clearInterval(interval)
  }, [tickConstructions])

  return null
}
