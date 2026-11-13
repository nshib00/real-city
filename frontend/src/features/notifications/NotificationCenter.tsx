import { Bell } from '../../shared/ui/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { Modal } from '../../shared/ui'
import { useGameStore } from '../../game/state/useGameStore'
import { request } from '../../shared/api/client'
import { useAuthStore } from '../auth/useAuthStore'
import type { CombatRecord } from '../../../../shared/events/combat'
import { PlayerName } from '../player/PlayerName'
import { getBuilding, toPlacedBuilding } from '../../shared/api/buildings'
import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { tileToChunk, wrapGridCoord } from '../../game/coordinates/iso'
import { visibleChunksQueryOptions } from '../world/useVisibleChunks'
import { showToast } from './toast'
import { monsterDisplayName } from '../../game/renderers/monsterAssetRegistry'
import type { MonsterEntity } from '../../game/state/useGameStore'

export function NotificationCenter() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const player = useAuthStore((state) => state.player)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const buildings = useGameStore((state) => state.buildings)
  const focusTile = useGameStore((state) => state.focusTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const viewport = useGameStore((state) => state.viewport)
  const [read, setRead] = useState<{ playerId?: string; ids: string[] }>({ ids: [] })
  const history = useQuery({
    queryKey: ['combat', 'history', player?.id],
    queryFn: () => request<{ records: CombatRecord[] }>('/combat/history?limit=50'),
    enabled: Boolean(player),
    refetchInterval: 30_000,
  })
  const records = history.data?.records ?? []
  const seen = useRef<{ playerId: string | undefined; ids: Set<string> } | null>(null)
  const [announcement, setAnnouncement] = useState('')
  const threatCount = useRef(0)
  useEffect(() => {
    if (!history.data) return
    const current = history.data.records
    const previous = seen.current
    if (previous && previous.playerId === player?.id) {
      const threats = current.filter((record) => record.owner_id === player?.id && !previous.ids.has(record.id))
      if (threats.length) {
        threatCount.current += threats.length
        setAnnouncement(`Новые атаки на ваши постройки: ${threats.length}. Всего за сеанс: ${threatCount.current}. Подробности в уведомлениях.`)
      }
    } else { threatCount.current = 0; setAnnouncement('') }
    seen.current = { playerId: player?.id, ids: new Set(current.map((record) => record.id)) }
  }, [history.data, player?.id])
  const unread = records.filter((record) => read.playerId !== player?.id || !read.ids.includes(record.id)).length
  const groups = new Map<string, { record: CombatRecord; count: number; damage: number; unread: boolean }>()
  for (const record of records) {
    const key = `${record.building_id}:${record.attacker_id}:${record.destroyed}`
    const group = groups.get(key)
    const isUnread = read.playerId !== player?.id || !read.ids.includes(record.id)
    if (group) { group.count++; group.damage += record.damage; group.unread ||= isUnread; if (Date.parse(record.created_at) > Date.parse(group.record.created_at)) group.record = record }
    else groups.set(key, { record, count: 1, damage: record.damage, unread: isUnread })
  }
  const notifications = [...groups.values()].sort((a, b) => Number(b.record.owner_id === player?.id) - Number(a.record.owner_id === player?.id) || Number(b.record.destroyed) - Number(a.record.destroyed) || Date.parse(b.record.created_at) - Date.parse(a.record.created_at))

  async function navigateToBuilding(buildingId: string) {
    try {
      const building = buildings.find((item) => item.id === buildingId)
        ?? toPlacedBuilding((await getBuilding(buildingId)).building)
      await queryClient.ensureQueryData(visibleChunksQueryOptions(tileToChunk(wrapGridCoord(building.tile)), viewport.radius))
      focusTile({ tile: building.tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight })
      selectBuilding(building.id)
      setOpen(false)
    } catch {
      showToast('warning', 'Не удалось перейти к постройке: она могла быть уничтожена или больше недоступна')
    }
  }

  return (
    <>
      <p className="ui-sr-only" role="status" aria-atomic="true">{announcement}</p>
      <div className="notification-launcher">
        <button className="notification-launcher-button" type="button" aria-label={`Уведомления${unread ? `: ${unread} непрочитанных` : ''}`} title="Уведомления" onClick={() => setOpen(true)}>
          <Bell size={22} aria-hidden="true" />
          {unread > 0 ? <span className="notification-launcher-count" aria-hidden="true">{unread > 99 ? '99+' : unread}</span> : null}
        </button>
      </div>
      {createPortal(<Modal title="Уведомления" open={open} onClose={() => setOpen(false)} className="notification-modal">
        <div className="notification-dialog-content">
          {realtimeStatus !== 'connected' ? <p className="connection-note" role="status">Нет связи с миром. История может обновляться с задержкой.</p> : null}
          <div className="notification-list">
          {history.isPending && player ? <p role="status">Загружаем боевые события…</p> : null}
          {history.error ? <p role="alert">Не удалось загрузить журнал боя. <button type="button" onClick={() => void history.refetch()}>Повторить</button></p> : null}
          {unread ? <button type="button" onClick={() => setRead({ playerId: player?.id, ids: records.map((record) => record.id) })}>Отметить прочитанными</button> : null}
          {!history.isPending && !history.error && !records.length ? <p>Боевых событий пока нет.</p> : null}
          {notifications.map(({ record, count, damage, unread }) => (
            <article className={`notification notification-${record.owner_id === player?.id ? 'danger' : 'info'}`} key={record.id}>
              <button className="notification-target" type="button" disabled={record.destroyed} aria-label={`Перейти к постройке ${buildingName(record.building_type)}`} onClick={() => void navigateToBuilding(record.building_id)}>
                <strong>{unread ? '● ' : ''}{record.destroyed ? 'Постройка уничтожена' : 'Атака постройки'}{count > 1 ? ` ×${count}` : ''}</strong>
                {record.owner_id === player?.id ? <span>Ваша постройка «{buildingName(record.building_type)}» {record.destroyed ? 'уничтожена' : 'атакована'}. Урон: {damage}.{record.attacker_id === player?.id && record.xp > 0 ? ` Получено ${record.xp} XP за последнее событие.` : ''}</span> : <span>Постройка «{buildingName(record.building_type)}» {record.destroyed ? 'уничтожена' : 'атакована'}. Урон: {damage}.</span>}
                <span>{record.source.startsWith('monster:') ? <>Монстр: {monsterDisplayName(record.source.slice('monster:'.length) as MonsterEntity['type'])}</> : record.source === 'monster' ? 'Монстр.' : <>Игрок: <PlayerName playerId={record.attacker_id} showLevelIcon />.</>}</span>
                <time dateTime={record.created_at}>{new Date(record.created_at).toLocaleString('ru-RU')}</time>
              </button>
              {record.destroyed ? <small>Уничтоженная постройка больше не отображается на карте.</small> : null}
            </article>
          ))}
          </div>
        </div>
      </Modal>, document.body)}
    </>
  )
}

function buildingName(type: string) {
  return buildingCatalog.find((building) => building.type === type)?.name
    ?? type.replaceAll('_', ' ')
}
