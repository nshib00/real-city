import { useQuery } from '@tanstack/react-query'

import { getPublicPlayer } from '../auth/api'
import { useAuthStore } from '../auth/useAuthStore'
import { LevelEmblem } from './LevelEmblem'

export function PlayerName({ playerId, fallback = 'Игрок', showLevelIcon = false }: { playerId: string; fallback?: string; showLevelIcon?: boolean }) {
  const viewer = useAuthStore((state) => state.player)
  const query = useQuery({
    queryKey: ['players', 'public', playerId],
    queryFn: () => getPublicPlayer(playerId),
    enabled: Boolean(playerId) && playerId !== viewer?.id,
    staleTime: 5 * 60_000,
    retry: false,
  })
  const name = playerId === viewer?.id
    ? viewer.profile?.display_name || viewer.name
    : query.data?.display_name
  const level = playerId === viewer?.id ? viewer.profile?.level : query.data?.level

  if (!showLevelIcon) return <>{name || fallback}</>
  return <span className="chat-author-identity">
    {level ? <LevelEmblem level={level} size="small" className="chat-author-level" /> : null}
    <span>{name || fallback}</span>
  </span>
}
