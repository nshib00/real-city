import { AeolianIcon } from './AeolianIcon'
import { ownershipLabels, type Ownership } from './ownership'

export type ObjectStatus = 'building' | 'ready' | 'damage' | 'depleted' | 'offline' | 'locked'
const statuses = { building: ['status-building', 'Строится'], ready: ['status-ready', 'Готово'], damage: ['damage', 'Повреждено'], depleted: ['status-depleted', 'Истощено'], offline: ['offline', 'Нет связи'], locked: ['lock', 'Недоступно'] } as const
const categories = { center: ['center', 'Центр'], housing: ['housing', 'Жильё'], fields: ['fields', 'Грядки'], industry: ['production', 'Производство'], defense: ['shield', 'Оборона'], roads: ['road', 'Дороги'], storage: ['storage', 'Склады'], social: ['alliance', 'Союзы'], trade: ['market', 'Торговля'] } as const

/** Владение, опасность и выбор — независимые знаки; текст доступен без цвета. */
export function ObjectMarks({ ownership, threat = false, selected = false, compact = false, status, rare = false, category }: { ownership: Ownership; threat?: boolean; selected?: boolean; compact?: boolean; status?: ObjectStatus; rare?: boolean; category?: keyof typeof categories }) {
  return <span className={`object-marks${compact ? ' object-marks-compact' : ''}`} data-ownership={ownership} data-selected={selected || undefined}>
    <span className="ownership-sign"><AeolianIcon name={`ownership-${ownership}`} size={compact ? 14 : 20} label={compact ? ownershipLabels[ownership] : undefined} />{!compact && <span>{ownershipLabels[ownership]}</span>}</span>
    {threat && <span className="threat-sign"><AeolianIcon name="threat" size={compact ? 14 : 20} label={compact ? 'Угроза' : undefined} />{!compact && <span>Угроза</span>}</span>}
    {category && <span className="category-sign"><AeolianIcon name={categories[category][0]} size={compact ? 14 : 20} label={compact ? categories[category][1] : undefined} />{!compact && categories[category][1]}</span>}
    {status && <span className="status-sign"><AeolianIcon name={statuses[status][0]} size={compact ? 14 : 20} label={compact ? statuses[status][1] : undefined} />{!compact && statuses[status][1]}</span>}
    {rare && <RarityMark compact={compact} />}
    {selected && !compact && <span className="selection-sign">Выбрано</span>}
  </span>
}

/** Редкость берётся только из категории rare каталога; новые игровые уровни не вводятся. */
export function RarityMark({ compact = false }: { compact?: boolean }) {
  return <span className="rarity-sign"><AeolianIcon name="rarity-rare" size={compact ? 14 : 20} label={compact ? 'Редкий ресурс' : undefined} />{!compact && 'Редкий ресурс'}</span>
}
