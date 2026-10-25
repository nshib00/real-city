import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'
import { playUiSound } from '../../audio/playUiSound'
import { fieldCropSpec } from '../fields/fieldGrowth'

export function ConstructionTicker() {
  const tickConstructions = useGameStore((state) => state.tickConstructions)
  const queryClient = useQueryClient()
  const lastTickRef = useRef(Date.now())

  useEffect(() => {
    const tick = () => {
      const now = Date.now()
      const lastTick = lastTickRef.current
      lastTickRef.current = now
      const playerId = useAuthStore.getState().player?.id
      if (playerId && useGameStore.getState().buildings.some((building) => building.owner === playerId && fieldCropSpec(building.kind)
        && !building.fieldStageReady && building.fieldStageReadyAt && building.fieldStageReadyAt > lastTick && building.fieldStageReadyAt <= now)) {
        playUiSound('economy.crop.ready')
      }
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
