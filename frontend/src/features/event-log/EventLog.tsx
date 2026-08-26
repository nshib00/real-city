import { useState } from 'react'

import { Tabs } from '../../shared/ui'
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

  return (
    <section className="event-log" aria-label="Журнал событий">
      <Tabs items={tabs} active={activeTab} onChange={setActiveTab}>
        {activeTab === 'events'
          ? events.map((event) => <p key={event}>{event}</p>)
          : <ChatPanel />}
      </Tabs>
    </section>
  )
}
