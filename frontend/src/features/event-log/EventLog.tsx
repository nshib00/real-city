import { useState } from 'react'
import { ChevronDown, ChevronUp, MessageSquare } from 'lucide-react'

import { useGameStore } from '../../game/state/useGameStore'
import { IconButton, Tabs } from '../../shared/ui'
import { ChatPanel } from '../chat/ChatPanel'

const events = [
  'Разведчики заметили ресурсную поляну на востоке.',
  'Склад закончит строительство через 04:20.',
  'У границы появился враждебный отряд.',
]

const tabs = [
  { id: 'events', label: 'События' },
  { id: 'chat', label: 'Чат', badge: 2 },
] as const

export function EventLog() {
  const [activeTab, setActiveTab] = useState<'events' | 'chat'>('events')
  const isChatCollapsed = useGameStore((state) => state.uiPreferences.isChatCollapsed)
  const setChatCollapsed = useGameStore((state) => state.setChatCollapsed)
  const collapsedLabel = activeTab === 'chat' ? 'Чат свернут' : 'Журнал свернут'

  return (
    <section className={isChatCollapsed ? 'event-log event-log-collapsed' : 'event-log'} aria-label="Журнал событий">
      <div className="event-log-header">
        <span>
          <MessageSquare size={16} aria-hidden="true" />
          {isChatCollapsed ? collapsedLabel : 'Связь и события'}
        </span>
        <IconButton
          label={isChatCollapsed ? 'Развернуть чат и события' : 'Свернуть чат и события'}
          icon={isChatCollapsed ? ChevronUp : ChevronDown}
          active={isChatCollapsed}
          onClick={() => setChatCollapsed(!isChatCollapsed)}
        />
      </div>
      {isChatCollapsed ? null : (
        <Tabs items={tabs} active={activeTab} onChange={setActiveTab}>
          {activeTab === 'events'
            ? events.map((event) => <p key={event}>{event}</p>)
            : <ChatPanel />}
        </Tabs>
      )}
    </section>
  )
}
