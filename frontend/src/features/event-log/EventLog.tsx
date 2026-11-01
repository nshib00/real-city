import { useState } from 'react'
import { ChevronDown, ChevronUp, MessageSquare } from '../../shared/ui/icons'

import { useGameStore } from '../../game/state/useGameStore'
import { IconButton, Tabs } from '../../shared/ui'
import { ChatPanel } from '../chat/ChatPanel'
import { useChatChannels } from '../chat/useChatChannels'
import { useAuthStore } from '../auth/useAuthStore'
import { useEventReadState } from './useEventReadState'

const tabs = [
  { id: 'events', label: 'События' },
  { id: 'chat', label: 'Чат' },
] as const

export function EventLog() {
  const [activeTab, setActiveTab] = useState<'events' | 'chat'>('events')
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
  const groupedShots = [...new Map(cannonShots.map((shot) => [shot.buildingId + ':' + shot.monsterId, {
    ...shot,
    count: cannonShots.filter((other) => other.buildingId === shot.buildingId && other.monsterId === shot.monsterId).length,
    totalDamage: cannonShots.filter((other) => other.buildingId === shot.buildingId && other.monsterId === shot.monsterId).reduce((sum, other) => sum + other.damage, 0),
  }])).values()]
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
        <Tabs items={tabItems} active={activeTab} onChange={setActiveTab}>
          <div hidden={activeTab !== 'events'}>
                {groupedShots.map((shot) => <p key={shot.id}>
                  Оборона против монстра {shot.monsterId}: попаданий {shot.count}, урон {shot.totalDamage}.
                  {buildings.some((building) => building.id === shot.buildingId) ? <button type="button" onClick={() => { const building = buildings.find((item) => item.id === shot.buildingId); if (building) { focusTile({ tile: building.tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight }); selectBuilding(building.id) } }}>К постройке</button> : null}
                </p>)}
                {!cannonShots.length ? <p>Новых событий обороны нет. Здесь появятся подтверждённые попадания ваших защитных построек.</p> : null}
          </div>
          <div hidden={activeTab !== 'chat'}><ChatPanel key={playerId ?? 'anonymous'} visible={!isChatCollapsed && activeTab === 'chat'} /></div>
        </Tabs>
      </div>
    </section>
  )
}
