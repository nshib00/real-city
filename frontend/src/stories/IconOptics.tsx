import { AeolianIcon } from '../shared/ui/AeolianIcon'
import { iconPaths } from '../shared/ui/iconPaths'

export function IconOptics() {
  return <section aria-label="Оптические варианты иконок"><details><summary>16 px и основная сетка: открыть лист оптики</summary><p>Слева — отдельный малый рисунок, затем 20 / 24 / 32 px. Малые детали упрощены; центр и поля сохранены.</p>
    {['light', 'dark', 'gray'].map(environment => <div className={`ownership-review ownership-review-${environment}`} key={environment}><div className="icon-optics-grid">{Object.keys(iconPaths).map(name => <article key={name}><span>{name}</span>{[16, 20, 24, 32].map(size => <AeolianIcon key={size} name={name} size={size} />)}</article>)}</div></div>)}
  </details></section>
}
