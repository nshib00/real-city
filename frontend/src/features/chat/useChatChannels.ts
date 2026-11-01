import { useQueries } from '@tanstack/react-query'
import { listChatMessages } from '../../shared/api/social'
import { useAuthStore } from '../auth/useAuthStore'
import { useGameStore } from '../../game/state/useGameStore'

export const chatChannels = [
  { id: 'global', label: 'Общий' },
  { id: 'nearby', label: 'Рядом' },
  { id: 'alliance', label: 'Союз' },
] as const

// Keep polling while the panel is collapsed; the server owns read cursors.
export function useChatChannels() {
  const playerId = useAuthStore((state) => state.player?.id)
  const groupId = useAuthStore((state) => state.player?.profile?.group_id)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  return useQueries({ queries: chatChannels.map((channel) => ({
    queryKey: ['chat', channel.id, playerId],
    queryFn: () => listChatMessages(channel.id),
    enabled: Boolean(playerId) && (channel.id !== 'alliance' || Boolean(groupId)),
    refetchInterval: realtimeStatus === 'connected' ? 60_000 : 15_000,
    retry: false,
  })) })
}
