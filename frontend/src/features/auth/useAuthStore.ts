import { create } from 'zustand'

import { getAccessToken } from '../../shared/api/client'
import type { Player } from './types'

type AuthState = {
  player: Player | null
  isAuthenticated: boolean
  setPlayer: (player: Player | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  player: null,
  isAuthenticated: Boolean(getAccessToken()),
  setPlayer: (player) => set({ player, isAuthenticated: Boolean(player) }),
}))
