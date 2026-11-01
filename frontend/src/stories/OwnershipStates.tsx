import { ObjectMarks } from '../shared/ui/ObjectMarks'

export function OwnershipStates() {
  return <section aria-label="Матрица владения и состояния">
    <h2>Владение не заменяет состояние</h2>
    <p>Круг с точкой — свой объект, связанный знак — союзный, ромб — чужой, пустой круг — нейтральный. Угроза и выбор добавляются отдельно.</p>
    {['light', 'dark', 'gray'].map(environment => <div className={`ownership-review ownership-review-${environment}`} key={environment}>
      <h3>{environment === 'light' ? 'Светлая панель' : environment === 'dark' ? 'Тёмная панель' : 'Без цвета'}</h3>
      <div className="ownership-review-grid">{(['own', 'ally', 'foreign', 'neutral'] as const).flatMap(ownership => [0, 1, 2, 3].map(state => <article key={`${ownership}-${state}`}><ObjectMarks ownership={ownership} threat={Boolean(state & 1)} selected={Boolean(state & 2)} /></article>))}</div>
    </div>)}
  </section>
}
