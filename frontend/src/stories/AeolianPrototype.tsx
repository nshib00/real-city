import { useLayoutEffect, useRef, useState } from 'react'
import { buildingCatalog } from '../../../shared/catalog/buildings'
import './aeolian-prototype.css'

const house = buildingCatalog.find(item => item.type === 'dugout')!
const labels: Record<string, string> = { coins: 'Монеты', wood: 'Древесина', stone: 'Камень' }
const asset = '/assets/buildings/housing/dugout/dugout_l01_'
type Step = 'empty' | 'tile' | 'catalog' | 'preview' | 'building' | 'object'

/** Изолированная модель взаимодействия: не отправляет команды в игровой мир. */
export function AeolianPrototype() {
  const [variant, setVariant] = useState('edge')
  const [step, setStep] = useState<Step>('empty')
  const [tile, setTile] = useState(18)
  const [poor, setPoor] = useState(false)
  const [offline, setOffline] = useState(false)
  const [panel, setPanel] = useState(true)
  const tileRef = useRef<HTMLButtonElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const cost = house.cost.map(item => `${labels[item.resource] ?? item.resource}: ${item.amount}`).join(', ')
  const placed = step === 'building' || step === 'object'
  const blocked = poor || offline
  useLayoutEffect(() => {
    if (!panel) tileRef.current?.focus()
    else if (step !== 'empty') heading.current?.focus()
  }, [panel, step, tile])
  function cancel() {
    setStep(placed ? 'building' : 'tile')
    setPanel(false)
  }
  function open(next: Step) {
    setPanel(true)
    setStep(next)
  }
  return <section className="aeolian" aria-label="Интерактивный макет Эолии" onKeyDown={event => { if (event.key === 'Escape') cancel() }}>
    <header className="aeolian-controls">
      <h2>Эолия: мастерская города</h2>
      <p>Макет. Размещение и ход стройки имитируются, сервер не подключён.</p>
      <label>Компоновка <select value={variant} onChange={event => setVariant(event.target.value)}><option value="edge">А: инструменты по краям</option><option value="desk">Б: нижний рабочий стол</option></select></label>
      <label><input type="checkbox" checked={poor} onChange={event => setPoor(event.target.checked)} /> Нехватка ресурсов</label>
      <label><input type="checkbox" checked={offline} onChange={event => setOffline(event.target.checked)} /> Нет связи</label>
      <button onClick={() => { setStep('empty'); setPanel(true); setPoor(false); setOffline(false) }}>Сбросить макет</button>
    </header>
    <div className={`aeolian-scene aeolian-${variant}`}>
      <div className="aeolian-resources" aria-label="Ресурсы макета"><strong>Город Эолии</strong><span>Монеты: {poor ? 0 : 5000}</span><span>Древесина: {poor ? 0 : 5000}</span><span>Камень: {poor ? 0 : 5000}</span><span>{offline ? '⚠ Нет связи' : 'Связь установлена'}</span></div>
      <nav className="aeolian-tools" aria-label="Инструменты макета"><button onClick={() => open(placed ? 'object' : step === 'empty' ? 'empty' : 'tile')}>Выбор</button><button disabled={step === 'empty' || placed} onClick={() => open('catalog')}>Строить</button></nav>
      <div className="aeolian-map" role="group" aria-label="Карта макета">
        {Array.from({ length: 36 }, (_, index) => <button key={index} disabled={index === 8 || (placed && index !== tile)} ref={index === tile ? tileRef : undefined} className={`aeolian-tile ${index === tile && step !== 'empty' ? 'is-selected' : ''}`} aria-pressed={index === tile && step !== 'empty'} aria-label={`Тайл ${index % 6 + 1}, ${Math.floor(index / 6) + 1}${index === 8 ? ': занято ратушей' : index === tile && placed ? ': стройка' : ''}`} onClick={() => {
          if (placed) { if (index === tile) open('object'); return }
          setTile(index); open('tile')
        }}>
          {index === 8 ? <img src="/assets/buildings/center/town_hall/town_hall_l01_active.png" alt="Ратуша" /> : index === tile && placed ? <img src={`${asset}construction.png`} alt="Землянка строится" /> : <span aria-hidden="true">{index % 7 === 0 ? '♣' : '·'}</span>}
        </button>)}
      </div>
      {panel && <aside className="aeolian-inspector" aria-label="Инспектор макета">
        <button className="aeolian-close" onClick={cancel}>Закрыть</button>
        <h3 ref={heading} tabIndex={-1}>{placed ? house.name : step === 'empty' ? 'Выберите место' : `Тайл ${tile % 6 + 1}, ${Math.floor(tile / 6) + 1}`}</h3>
        {step === 'empty' && <p>Выберите свободный тайл на карте.</p>}
        {step === 'tile' && <><p>Трава · свободное место. Проверку правил выполняет сервер в игре.</p><button onClick={() => open('catalog')}>Открыть строительство</button></>}
        {(step === 'catalog' || step === 'preview') && <>
          <img className="aeolian-preview" src={`${asset}active.png`} alt="Землянка, уровень 1" />
          <h4>{house.name}</h4><p>Жильё · {house.footprint.width}×{house.footprint.height} · население +{house.population}</p>
          <p>Стоимость: {cost || 'Бесплатно'}</p><p>Время строительства: {house.buildSeconds} с</p>
          <p role="status">{offline ? '⚠ Нет связи. Дождитесь подключения.' : poor ? '⚠ Недостаточно ресурсов. Пополните запасы.' : '✓ В макете ресурсов достаточно.'}</p>
          {step === 'catalog' ? <button disabled={blocked} onClick={() => open('preview')}>Предпросмотр размещения</button> : <><p>Контур выбранного тайла показывает место размещения.</p><button disabled={blocked} onClick={() => open('building')}>Разместить в макете</button></>}
          <button onClick={() => open('tile')}>Назад к тайлу</button>
        </>}
        {placed && <><p role="status">◷ Строится · 0 / {house.buildSeconds} с</p><p>◉ Ваш объект · уровень 1</p><p>Прочность после завершения: {house.health}</p><p>Стоимость макета: {cost}. Списания в игре нет.</p>{step === 'building' ? <button onClick={() => open('object')}>Открыть объект</button> : <p>Объект открыт. В игре прогресс поступает с сервера; здесь время остановлено.</p>}</>}
      </aside>}
      <div className="aeolian-events" role="status">{placed ? 'Заявка принята в макете. Стройка появилась на карте.' : 'События города: выберите место для нового жилья.'}{!panel && <button onClick={() => open(placed ? 'object' : 'tile')}>Открыть инспектор</button>}</div>
    </div>
  </section>
}
