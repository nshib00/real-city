import { useState } from 'react'
import { Hammer } from '../shared/ui/icons'
import { Button, Drawer, IconButton, Modal, Tabs, Tooltip } from '../shared/ui'
import { ResourceIcon } from '../features/resources/ResourceIcon'
import { buildingCatalog } from '../../../shared/catalog/buildings'

export function ComponentStates() {
  const [tab, setTab] = useState('cost')
  const [modal, setModal] = useState(false)
  const [drawer, setDrawer] = useState(false)
  const building = buildingCatalog.find((item) => item.type === 'dugout')!
  return <section className="component-states" aria-label="Дизайн-система">
    <h2>Компоненты Эолии</h2>
    <p>Данные каталога: {building.name}. Одинаковые элементы над светлым и тёмным фоном карты.</p>
    {(['light', 'dark'] as const).map((environment) => <article key={environment} className={`component-environment component-environment-${environment}`}>
      <div className="component-surface"><h3>{environment === 'light' ? 'Светлая поляна' : 'Тёмный лес'}</h3>
        <div className="component-row"><Button variant="primary">Построить {building.name}</Button><Button disabled>Недостаточно дерева</Button><Button loading>Ожидание сервера</Button><Button variant="danger">Отменить строительство</Button></div>
        <div className="component-row"><Tooltip text="Выберите свободную клетку перед строительством"><IconButton icon={Hammer} label="Строительство" /></Tooltip><IconButton icon={Hammer} label="Строительство выбрано" active /><IconButton icon={Hammer} label="Ожидание размещения" loading /></div>
        <Tabs items={[{ id: 'cost', label: 'Стоимость' }, { id: 'stats', label: 'Характеристики' }]} active={tab} onChange={setTab}>
          {tab === 'cost' ? <div className="component-row">{building.cost.map(({ resource: id, amount }) => <span className="component-row" key={id}><ResourceIcon id={id} label={id === 'coins' ? 'Монеты' : 'Дерево'} /><strong className="ui-numeric">{amount}</strong></span>)}<ResourceIcon id="missing-design-sample" label="Недоступная миниатюра" /></div> : <p>Строительство: {building.buildSeconds} с. Прочность: {building.health}.</p>}
        </Tabs>
        <div className="component-row"><Button onClick={() => setModal(true)}>Открыть диалог</Button><Button onClick={() => setDrawer(true)}>Открыть панель</Button></div>
        <label>Ошибка ввода <input aria-invalid="true" aria-describedby={`${environment}-field-error`} value="−1" readOnly /></label>
        <p id={`${environment}-field-error`}>Введите целое положительное количество.</p>
      </div>
    </article>)}
    <Modal title="Стоимость строительства" open={modal} onClose={() => setModal(false)}><p>{building.name}: {building.buildSeconds} с.</p><Button onClick={() => setModal(false)}>Вернуться к карте</Button></Modal>
    <Drawer title="Характеристики землянки" open={drawer} onClose={() => setDrawer(false)}><p>Прочность: {building.health}.</p></Drawer>
  </section>
}
