import { Bell, ChevronDown, ChevronUp } from 'lucide-react'

import { useGameStore } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'

const notifications = [
  { id: 'build', severity: 'info', title: 'Стройка', text: 'Деревянный дом завершится через 04:20.' },
  { id: 'raid', severity: 'danger', title: 'Угроза', text: 'Рядом с границей замечен рейд.' },
  { id: 'fuel', severity: 'warning', title: 'Бензин', text: 'Нефтеперерабатывающий завод простаивает без нефти.' },
] as const

export function NotificationCenter() {
  const collapsed = useGameStore((state) => state.uiPreferences.areNotificationsCollapsed)
  const setCollapsed = useGameStore((state) => state.setNotificationsCollapsed)

  return (
    <section className={collapsed ? 'notification-stack notification-stack-collapsed' : 'notification-stack'} aria-label="Уведомления" aria-live="polite">
      <header className="notification-header">
        <span>
          <Bell size={16} aria-hidden="true" />
          Уведомления
          <strong>{notifications.length}</strong>
        </span>
        <IconButton
          label={collapsed ? 'Развернуть уведомления' : 'Свернуть уведомления'}
          icon={collapsed ? ChevronDown : ChevronUp}
          active={collapsed}
          onClick={() => setCollapsed(!collapsed)}
        />
      </header>
      {collapsed ? null : (
        <div className="notification-list">
          {notifications.map((notification) => (
            <article className={`notification notification-${notification.severity}`} key={notification.id}>
              <strong>{notification.title}</strong>
              <span>{notification.text}</span>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
