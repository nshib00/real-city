import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { buildingCatalog } from '../../../shared/catalog/buildings'
import { AeolianPrototype } from './AeolianPrototype'

afterEach(cleanup)
function chooseHouse() {
  fireEvent.click(screen.getByRole('button', { name: 'Тайл 1, 4' }))
  fireEvent.click(screen.getByRole('button', { name: 'Открыть строительство' }))
}
describe('Изолированный игровой цикл макета', () => {
  it('показывает цену каталога и проходит от тайла до инспектора стройки', () => {
    render(<AeolianPrototype />)
    expect((screen.getByRole('button', { name: 'Строить' }) as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByRole('button', { name: /занято ратушей/ }) as HTMLButtonElement).disabled).toBe(true)
    chooseHouse()
    const house = buildingCatalog.find(item => item.type === 'dugout')!
    const inspector = within(screen.getByLabelText('Инспектор макета'))
    expect(inspector.getByText(`Время строительства: ${house.buildSeconds} с`)).toBeTruthy()
    expect(inspector.getByText('Стоимость: Монеты: 50, Древесина: 3')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Предпросмотр размещения' }))
    fireEvent.click(screen.getByRole('button', { name: 'Разместить в макете' }))
    expect(screen.getByRole('img', { name: 'Землянка строится' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Открыть объект' }))
    expect(screen.getByText(/Объект открыт/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть' }))
    expect(screen.queryByLabelText('Инспектор макета')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Тайл 1, 4: стройка' }))
    expect(screen.getByText(/Объект открыт/)).toBeTruthy()
  })
  it('запрещает размещение при нехватке и потере связи, позволяет отменить предпросмотр', () => {
    render(<AeolianPrototype />)
    chooseHouse()
    fireEvent.click(screen.getByLabelText('Нехватка ресурсов'))
    expect((screen.getByRole('button', { name: 'Предпросмотр размещения' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByLabelText('Нехватка ресурсов'))
    fireEvent.click(screen.getByRole('button', { name: 'Предпросмотр размещения' }))
    fireEvent.click(screen.getByLabelText('Нет связи'))
    expect((screen.getByRole('button', { name: 'Разместить в макете' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.keyDown(screen.getByLabelText('Интерактивный макет Эолии'), { key: 'Escape' })
    expect(screen.queryByRole('img', { name: 'Землянка строится' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Сбросить макет' }))
    expect(screen.getByText('Выберите свободный тайл на карте.')).toBeTruthy()
  })
})
