import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAllianceProfile } from '../../shared/api/social'
import { useAuthStore } from '../auth/useAuthStore'

/** Только отображение подтверждённого состава союза; права действий проверяет сервер. */
export function useOwnershipContext() {
  const player = useAuthStore(state => state.player)
  const groupId = player?.profile?.group_id
  const profile = useQuery({ queryKey: ['alliances', 'me', player?.id], queryFn: getAllianceProfile, enabled: Boolean(groupId), staleTime: 60_000, retry: false })
  const alliedIds = useMemo(() => new Set(groupId && profile.data?.profile.alliance?.id === groupId
    ? profile.data.profile.members.map(member => member.player_id) : []), [groupId, profile.data])
  return { viewerId: player?.id, alliedIds }
}
