import { Bell, ChevronDown, ChevronUp } from '../../shared/ui/icons'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { request } from '../../shared/api/client'
import { useAuthStore } from '../auth/useAuthStore'
import type { CombatRecord } from '../../../../shared/events/combat'

export function NotificationCenter() {
  const collapsed = useGameStore((state) => state.uiPreferences.areNotificationsCollapsed)
  const setCollapsed = useGameStore((state) => state.setNotificationsCollapsed)
  const player = useAuthStore((state) => state.player)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const buildings = useGameStore((state) => state.buildings)
  const focusTile = useGameStore((state) => state.focusTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
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

  return (
    <section className={collapsed ? 'notification-stack notification-stack-collapsed' : 'notification-stack'} aria-label="Уведомления">
      <p className="ui-sr-only" role="status" aria-atomic="true">{announcement}</p>
      <header className="notification-header">
        <span>
          <Bell size={16} aria-hidden="true" />
          Уведомления
          <strong aria-label="Непрочитанные уведомления">{unread}</strong>
        </span>
        <IconButton
          label={collapsed ? 'Развернуть уведомления' : 'Свернуть уведомления'}
          icon={collapsed ? ChevronDown : ChevronUp}
          active={collapsed}
          sound={collapsed ? 'ui.toggle.on' : 'ui.toggle.off'}
          onClick={() => setCollapsed(!collapsed)}
        />
      </header>
      {realtimeStatus !== 'connected' ? <p className="connection-note" role="status">Нет связи с миром. История может обновляться с задержкой.</p> : null}
      {collapsed ? null : (
        <div className="notification-list">
          {history.isPending && player ? <p role="status">Загружаем боевые события…</p> : null}
          {history.error ? <p role="alert">Не удалось загрузить журнал боя. <button type="button" onClick={() => void history.refetch()}>Повторить</button></p> : null}
          {unread ? <button type="button" onClick={() => setRead({ playerId: player?.id, ids: records.map((record) => record.id) })}>Отметить прочитанными</button> : null}
          {!history.isPending && !history.error && !records.length ? <p>Боевых событий пока нет.</p> : null}
          {notifications.map(({ record, count, damage, unread }) => (
            <article className={`notification notification-${record.owner_id === player?.id ? 'danger' : 'info'}`} key={record.id}>
              <strong>{unread ? '● ' : ''}{record.destroyed ? 'Постройка уничтожена' : 'Атака постройки'}{count > 1 ? ` ×${count}` : ''}</strong>
              <span>{record.attacker_id || 'Дикий монстр'} → {record.building_type}, ур. {record.level}, владелец {record.owner_id}. Урон: {damage}.{record.attacker_id === player?.id && record.xp > 0 ? ` Получено ${record.xp} XP за последнее событие.` : ''}</span>
              <time dateTime={record.created_at}>{new Date(record.created_at).toLocaleString('ru-RU')}</time>
              {buildings.some((building) => building.id === record.building_id) ? <button type="button" onClick={() => { const building = buildings.find((item) => item.id === record.building_id); if (building) { focusTile({ tile: building.tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight }); selectBuilding(building.id) } }}>Показать на карте</button> : <small>Объект уничтожен или находится вне загруженной области.</small>}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
