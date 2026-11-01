import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Hammer, MousePointer2, Swords } from '../shared/ui/icons'
import { IconButton } from '../shared/ui/IconButton'
import { SegmentedControl } from '../shared/ui/SegmentedControl'
import { StatusState } from '../shared/ui/StatusState'
import { HealthBar } from '../game/HealthBar'
import '../app/styles/index.css'
import '../app/styles/aeolian.css'
import '../app/styles/control-states.css'
import '../app/styles/object-marks.css'
import { OwnershipStates } from './OwnershipStates'
import { BadgeStates } from './BadgeStates'
import { IconOptics } from './IconOptics'
import { setInterfaceTheme, useApplyInterfaceTheme, useInterfaceTheme } from '../app/theme'
import './design.css'
import { AeolianPrototype } from './AeolianPrototype'
import { ComponentStates } from './ComponentStates'

function DesignWorkbench() {
  useApplyInterfaceTheme()
  const theme = useInterfaceTheme()
  const [mode, setMode] = useState('select')
  const [retry, setRetry] = useState(false)
  return <><AeolianPrototype /><main className="design-workbench">
    <h1>Эолия: исходные компоненты</h1>
    <p>Стенд аудита. Текущие стили и шрифт игры, без подключения к миру.</p>
    <label>Оформление стенда <select value={theme} onChange={event => setInterfaceTheme(event.target.value === 'aeolian' ? 'aeolian' : 'classic')}><option value="classic">Классическое</option><option value="aeolian">Эолия</option></select></label>
    <ComponentStates />
    <OwnershipStates />
    <BadgeStates />
    <IconOptics />
    <section aria-label="Инструменты"><h2>Режим действия</h2>
      <IconButton label="Выбор" icon={MousePointer2} active={mode === 'select'} onClick={() => setMode('select')} />
      <IconButton label="Строительство" icon={Hammer} active={mode === 'build'} onClick={() => setMode('build')} />
      <IconButton label="Атака недоступна" icon={Swords} disabled />
      <p role="status">Режим: {mode}</p>
    </section>
    <section><h2>Переключатель</h2><SegmentedControl label="Режим" value={mode} onChange={setMode} items={[{ id: 'select', label: 'Наблюдение' }, { id: 'build', label: 'Строительство' }]} /></section>
    <section><h2>Состояния</h2>
      <StatusState title="Ничего не выбрано">Выберите объект на карте.</StatusState>
      <StatusState variant="loading">Загрузка мира…</StatusState>
      <StatusState variant="offline" title="Связь потеряна">Дождитесь подключения перед действием.</StatusState>
      <StatusState variant="error" title="Не удалось загрузить" action={{ label: 'Повторить', onClick: () => setRetry(true) }}>Проверьте подключение.</StatusState>
      {retry && <p role="status">Повтор запрошен</p>}
    </section>
    <section><h2>Повреждение</h2><HealthBar health={35} maxHealth={100} /><p>Прочность 35 / 100</p></section>
    <section><h2>Экспорт пилотных ассетов</h2><img width="24" height="24" src="/assets/ui/pilot/select.svg" alt="Выбор клетки" /><img width="64" height="64" src="/assets/ui/pilot/stone.png" alt="Камень" /></section>
  </main></>
}

createRoot(document.getElementById('root')!).render(<DesignWorkbench />)
