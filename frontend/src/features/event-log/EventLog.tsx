import { lazy, Suspense, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, MessageSquare } from '../../shared/ui/icons'

import { useGameStore } from '../../game/state/useGameStore'
import { IconButton, Tabs } from '../../shared/ui'
import { useChatChannels } from '../chat/useChatChannels'
import { useAuthStore } from '../auth/useAuthStore'
import { useEventReadState } from './useEventReadState'

const tabs = [
  { id: 'events', label: 'События' },
  { id: 'chat', label: 'Чат' },
] as const
const ChatPanel = lazy(() => import('../chat/ChatPanel').then((module) => ({ default: module.ChatPanel })))

export function EventLog() {
  const [activeTab, setActiveTab] = useState<'events' | 'chat'>('events')
  const [chatMounted, setChatMounted] = useState(false)
  const playerId = useAuthStore((state) => state.player?.id)
  const chatQueries = useChatChannels()
  const isChatCollapsed = useGameStore((state) => state.uiPreferences.isChatCollapsed)
  const cannonShots = useGameStore((state) => state.cannonShots)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const buildings = useGameStore((state) => state.buildings)
  const focusTile = useGameStore((state) => state.focusTile)
  const selectBuilding = useGameStore((state) => state.selectBuilding)
  const unread = useEventReadState(playerId, cannonShots.map((shot) => shot.id), !isChatCollapsed && activeTab === 'events')
  const chatUnread = chatQueries.reduce((sum, query) => sum + (query.data?.read_state?.unread ?? 0), 0)
  const tabItems = tabs.map((tab) => ({ ...tab, badge: (tab.id === 'events' ? unread : chatUnread) || undefined }))
  const groupedShots = useMemo(() => {
    const groups = new Map<string, typeof cannonShots[number] & { count: number; totalDamage: number }>()
    for (const shot of cannonShots) {
      const key = `${shot.buildingId}:${shot.monsterId}`
      const previous = groups.get(key)
      groups.set(key, { ...shot, count: (previous?.count ?? 0) + 1, totalDamage: (previous?.totalDamage ?? 0) + shot.damage })
    }
    return [...groups.values()]
  }, [cannonShots])
  const buildingsById = useMemo(() => new Map(buildings.map((building) => [building.id, building])), [buildings])
  const setChatCollapsed = useGameStore((state) => state.setChatCollapsed)
  const collapsedLabel = activeTab === 'chat' ? 'Чат свернут' : 'Журнал свернут'

  return (
    <section id="game-events" tabIndex={-1} className={isChatCollapsed ? 'event-log event-log-collapsed' : 'event-log'} aria-label="Журнал событий" onKeyDown={(event) => { if (event.key === 'Escape') { event.stopPropagation(); setChatCollapsed(true); document.getElementById('game-map')?.focus() } }}>
      <div className="event-log-header">
        <span>
          <MessageSquare size={16} aria-hidden="true" />
          {isChatCollapsed ? collapsedLabel : 'Связь и события'}
          {isChatCollapsed && unread + chatUnread > 0 ? <strong aria-label={`Непрочитано: ${unread + chatUnread}`}> {unread + chatUnread}</strong> : null}
        </span>
        <IconButton
          label={isChatCollapsed ? 'Развернуть чат и события' : 'Свернуть чат и события'}
          icon={isChatCollapsed ? ChevronUp : ChevronDown}
          active={isChatCollapsed}
          sound={isChatCollapsed ? 'ui.toggle.on' : 'ui.toggle.off'}
          onClick={() => setChatCollapsed(!isChatCollapsed)}
        />
      </div>
      {realtimeStatus !== 'connected' ? <p className="connection-note" role="status">Связь с миром потеряна или восстанавливается. Новые события могут задерживаться.</p> : null}
      <div hidden={isChatCollapsed}>
        <Tabs items={tabItems} active={activeTab} onChange={(next) => { setActiveTab(next); if (next === 'chat') setChatMounted(true) }}>
          <div hidden={activeTab !== 'events'}>
                {groupedShots.map((shot) => <p key={shot.id}>
                  Оборона против монстра {shot.monsterId}: попаданий {shot.count}, урон {shot.totalDamage}.
                  {buildingsById.has(shot.buildingId) ? <button type="button" onClick={() => { const building = buildingsById.get(shot.buildingId); if (building) { focusTile({ tile: building.tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight }); selectBuilding(building.id) } }}>К постройке</button> : null}
                </p>)}
                {!cannonShots.length ? <p>Новых событий обороны нет. Здесь появятся подтверждённые попадания ваших защитных построек.</p> : null}
          </div>
          <div hidden={activeTab !== 'chat'}>{chatMounted ? <Suspense fallback={null}><ChatPanel key={playerId ?? 'anonymous'} visible={!isChatCollapsed && activeTab === 'chat'} /></Suspense> : null}</div>
        </Tabs>
      </div>
    </section>
  )
}
