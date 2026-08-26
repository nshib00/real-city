import { Coins, Gauge, Hammer, Shield } from 'lucide-react'

import { useGameStore } from '../../game/state/useGameStore'
import { Drawer, IconButton } from '../../shared/ui'

const members = [
  ['Лидер', 'Северный двор'],
  ['Казначей', 'Каменная пристань'],
  ['Заместитель', 'Сад ветров'],
  ['Офицер', 'Горная линия'],
  ['Участник', 'Новая Землянка'],
] as const

const buffs = [
  { icon: Hammer, name: 'Быстрая стройка', level: 2, effect: '+6% скорость' },
  { icon: Shield, name: 'Общая защита', level: 1, effect: '+4% прочность' },
  { icon: Gauge, name: 'Логистика', level: 1, effect: '+3% доставка' },
] as const

export function AlliancePanel() {
  const open = useGameStore((state) => state.uiPreferences.alliancePanelOpen)
  const setAlliancePanelOpen = useGameStore((state) => state.setAlliancePanelOpen)

  return (
    <Drawer title="Союзный дом" open={open} onClose={() => setAlliancePanelOpen(false)}>
      <section className="alliance-summary">
        <strong>Караван Эолии</strong>
        <span>Уровень дома 2</span>
        <span>Участники 18/25</span>
      </section>
      <section className="alliance-treasury">
        <h3>Казна</h3>
        <p>
          <Coins size={16} aria-hidden="true" /> 12 800 монет, 640 древесины, 310 камня, 42 бензина
        </p>
        <button type="button">Пожертвовать</button>
      </section>
      <section className="alliance-list">
        <h3>Иерархия</h3>
        {members.map(([role, name]) => (
          <p key={`${role}:${name}`}>
            <strong>{role}</strong>
            <span>{name}</span>
          </p>
        ))}
      </section>
      <section className="alliance-buffs">
        <h3>Баффы</h3>
        {buffs.map((buff) => (
          <article key={buff.name}>
            <IconButton label={buff.name} icon={buff.icon} />
            <strong>{buff.name}</strong>
            <span>ур. {buff.level}</span>
            <small>{buff.effect}</small>
          </article>
        ))}
      </section>
    </Drawer>
  )
}
