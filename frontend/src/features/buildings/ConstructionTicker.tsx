import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useGameStore } from '../../game/state/useGameStore'

export function ConstructionTicker() {
  const tickConstructions = useGameStore((state) => state.tickConstructions)
  const queryClient = useQueryClient()

  useEffect(() => {
    const tick = () => {
      const now = Date.now()
      const hasNewReadyFieldStage = useGameStore
        .getState()
        .buildings
        .some((building) => building.fieldStageReadyAt && building.fieldStageReadyAt <= now && !building.fieldStageReady)
      tickConstructions(now)
      if (hasNewReadyFieldStage) {
        void queryClient.invalidateQueries({ queryKey: ['buildings'] })
        void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      }
    }
    const interval = window.setInterval(tick, 1000)
    tick()
    return () => window.clearInterval(interval)
  }, [queryClient, tickConstructions])

  return null
}
