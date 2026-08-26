const notifications = [
  { id: 'build', severity: 'info', title: 'Стройка', text: 'Деревянный дом завершится через 04:20.' },
  { id: 'raid', severity: 'danger', title: 'Угроза', text: 'Рядом с границей замечен рейд.' },
  { id: 'fuel', severity: 'warning', title: 'Бензин', text: 'Нефтеперерабатывающий завод простаивает без нефти.' },
] as const

export function NotificationCenter() {
  return (
    <section className="notification-stack" aria-label="Уведомления" aria-live="polite">
      {notifications.map((notification) => (
        <article className={`notification notification-${notification.severity}`} key={notification.id}>
          <strong>{notification.title}</strong>
          <span>{notification.text}</span>
        </article>
      ))}
    </section>
  )
}
