import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getPublicProfile } from '../../shared/api/playerProfile'
import { Modal } from '../../shared/ui/Modal'
import { useAuthStore } from '../auth/useAuthStore'
import { ProfileScores } from './ProfileScores'

export function PublicProfileButton({ playerId }: { playerId: string }) {
  const [open, setOpen] = useState(false)
  const viewerId = useAuthStore((state) => state.player?.id)
  const query = useQuery({
    queryKey: ['public-profile', viewerId, playerId], queryFn: () => getPublicProfile(playerId),
    enabled: open && Boolean(viewerId), retry: false, staleTime: 0,
  })
  const profile = query.data?.profile
  return <>
    <button type="button" onClick={() => setOpen(true)}>Профиль владельца</button>
    <Modal title="Публичный профиль" open={open} onClose={() => setOpen(false)}>
      {query.isPending ? <p role="status">Загружаем профиль…</p> : null}
      {query.error ? <p role="alert">Не удалось загрузить профиль. <button type="button" onClick={() => void query.refetch()}>Повторить</button></p> : null}
      {profile && !query.error ? <>
        <h3>{profile.display_name}</h3>
        <p>Уровень {profile.level}</p>
        {profile.title ? <p>{profile.title}</p> : null}
        {profile.group_id ? <p>Союз: {profile.group_id}</p> : null}
        <ProfileScores scores={profile.scores} />
      </> : null}
    </Modal>
  </>
}
