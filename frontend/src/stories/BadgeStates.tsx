import { ObjectMarks } from '../shared/ui/ObjectMarks'

export function BadgeStates() {
  return <section aria-label="Матрица бейджей"><details><summary>Категория, состояние и редкость: открыть матрицу</summary><p>Редкий ресурс обозначен двойным восьмиугольником; треугольник оставлен только угрозе. Знаки располагаются рядом, основной рисунок не перекрывается.</p>
    {['light', 'dark', 'gray'].map(environment => <div className={`ownership-review ownership-review-${environment}`} key={environment}>
      <h3>{environment === 'light' ? 'Светлая поверхность' : environment === 'dark' ? 'Тёмная поверхность' : 'Без цвета'}</h3>
      <div className="ownership-review-grid">{(['own', 'ally', 'foreign', 'neutral'] as const).flatMap(ownership => Array.from({ length: 8 }, (_, flags) => (['building', 'ready', 'damage', 'depleted'] as const).map(status => <article key={`${ownership}-${flags}-${status}`}><ObjectMarks ownership={ownership} threat={Boolean(flags & 1)} selected={Boolean(flags & 2)} rare={Boolean(flags & 4)} status={status} category="industry" /></article>)))}</div>
    </div>)}
  </details></section>
}
