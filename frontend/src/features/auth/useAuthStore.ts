import { create } from 'zustand'

import { getAccessToken } from '../../shared/api/client'
import type { Player } from './types'
import { useGameStore } from '../../game/state/useGameStore'
import { clientTelemetry } from '../../shared/telemetry/clientTelemetry'

type AuthState = {
  player: Player | null
  isAuthenticated: boolean
  setPlayer: (player: Player | null) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  player: null,
  isAuthenticated: Boolean(getAccessToken()),
  setPlayer: (player) => {
    if (get().player?.id !== player?.id) {
      useGameStore.setState({ cannonShots: [] })
      clientTelemetry.reset()
    }
    set({ player, isAuthenticated: Boolean(player) })
  },
}))
