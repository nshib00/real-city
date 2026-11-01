// @vitest-environment jsdom
import { useState } from 'react'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { Button, Drawer, Tabs, Tooltip } from './index'
import { ResourceIcon } from '../../features/resources/ResourceIcon'
vi.mock('../../audio/playUiSound', () => ({ playUiSound: vi.fn() }))
afterEach(cleanup)

it('blocks repeated actions while waiting for server', () => {
  const click = vi.fn()
  render(<Button loading onClick={click}>Строим</Button>)
  const button = screen.getByRole('button') as HTMLButtonElement
  expect(button.disabled).toBe(true)
  expect(button.getAttribute('aria-busy')).toBe('true')
  fireEvent.click(button)
  expect(click).not.toHaveBeenCalled()
})
it('connects tabs and panel and navigates with arrows and Home', () => {
  function Example() { const [active, setActive] = useState('a'); return <Tabs items={[{ id: 'a', label: 'Стоимость' }, { id: 'b', label: 'Прочность' }]} active={active} onChange={setActive}>Данные</Tabs> }
  render(<Example />)
  const first = screen.getByRole('tab', { name: 'Стоимость' })
  first.focus()
  fireEvent.keyDown(first, { key: 'ArrowRight' })
  const second = screen.getByRole('tab', { name: 'Прочность' })
  expect(document.activeElement).toBe(second)
  expect(second.getAttribute('aria-selected')).toBe('true')
  expect(screen.getByRole('tabpanel').getAttribute('aria-labelledby')).toBe(second.id)
  fireEvent.keyDown(second, { key: 'Home' })
  expect(document.activeElement).toBe(first)
})
it('returns drawer focus to opener and keeps closed content inert', () => {
  function Example() { const [open, setOpen] = useState(false); return <><button onClick={() => setOpen(true)}>Панель</button><Drawer title="Выбор" open={open} onClose={() => setOpen(false)}>Землянка</Drawer></> }
  render(<Example />)
  const opener = screen.getByText('Панель'); opener.focus(); fireEvent.click(opener)
  const panel = screen.getByRole('complementary')
  const focus = vi.spyOn(HTMLElement.prototype, 'focus')
  fireEvent.keyDown(panel, { key: 'Escape' })
  expect(focus).toHaveBeenLastCalledWith({ preventScroll: true })
  fireEvent.click(opener)
  expect(focus).toHaveBeenLastCalledWith({ preventScroll: true })
  expect(document.activeElement).toBe(panel)
  fireEvent.keyDown(panel, { key: 'Escape' })
  expect(document.activeElement).toBe(opener)
  expect(panel.hasAttribute('inert')).toBe(true)
  focus.mockRestore()
})
it('dismisses an accessible tooltip with Escape', () => {
  render(<Tooltip text="Свободная клетка"><button>Строить</button></Tooltip>)
  const tip = screen.getByRole('tooltip')
  const button = screen.getByRole('button')
  expect(button.getAttribute('aria-describedby')).toBe(tip.id)
  fireEvent.keyDown(button, { key: 'Escape' })
  expect(tip.getAttribute('data-dismissed')).toBe('true')
})
it('preserves resource name after failed image and resets for new resource', () => {
  const { container, rerender } = render(<ResourceIcon id="wood" label="Дерево" />)
  fireEvent.error(container.querySelector('img')!)
  expect(screen.getByRole('img', { name: 'Дерево' })).toBeTruthy()
  expect(container.querySelector('img')).toBeNull()
  rerender(<ResourceIcon id="stone" label="Камень" />)
  expect(container.querySelector('img')).toBeTruthy()
})
