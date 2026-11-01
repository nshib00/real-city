const labels: Record<string, string> = {
  economy: 'Экономика', production: 'Производство', storage: 'Хранение', defense: 'Оборона',
  trade: 'Торговля', attacks: 'Прямые атаки', threats: 'Устранённые угрозы', objects: 'Объекты',
}

export function ProfileScores({ scores }: { scores?: Record<string, number> }) {
  const entries = Object.entries(labels).filter(([key]) => Number.isFinite(scores?.[key]))
  if (!entries.length) return <p>Показатели пока недоступны.</p>
  return <dl className="profile-stat-grid" aria-label="Показатели профиля">
    {entries.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{scores![key].toLocaleString('ru-RU')}</dd></div>)}
  </dl>
}
