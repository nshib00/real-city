// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useState } from 'react'
import { Modal } from './Modal'
vi.mock('../../audio/playUiSound', () => ({ playUiSound: vi.fn() }))
afterEach(cleanup)
describe('Modal keyboard route', () => {
 it('skips controls inside hidden groups when trapping keyboard focus', () => {
  render(<Modal open title="Скрытые элементы" onClose={() => {}}><button>Видимый</button><div hidden><button>Скрытый</button></div><div style={{display:'none'}}><input aria-label="Скрытое поле" /></div></Modal>)
  const visible=screen.getByText('Видимый');visible.focus()
  fireEvent.keyDown(visible,{key:'Tab'})
  expect(document.activeElement).toBe(screen.getByRole('button',{name:'Закрыть'}))
 })
 it('moves focus inside, traps Tab and returns to the opener after Escape', () => {
  function Example() {
   const [open,setOpen]=useState(false)
   return <><button onClick={() => setOpen(true)}>Открыть</button><Modal open={open} title="Проверка" onClose={() => setOpen(false)}><input aria-label="Имя"/><button>Сохранить</button></Modal></>
  }
  render(<Example />)
  const opener=screen.getByText('Открыть');opener.focus();fireEvent.click(opener)
  const close=screen.getByRole('button',{name:'Закрыть'})
  expect(document.activeElement).toBe(close)
  fireEvent.keyDown(close,{key:'Tab',shiftKey:true})
  expect(document.activeElement).toBe(screen.getByText('Сохранить'))
  fireEvent.keyDown(document.activeElement!,{key:'Tab'})
  expect(document.activeElement).toBe(close)
  fireEvent.keyDown(close,{key:'Escape'})
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.activeElement).toBe(opener)
 })
})
