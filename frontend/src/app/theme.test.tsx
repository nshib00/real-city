import { act, fireEvent, render, screen, cleanup } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { useState } from 'react'
import { configuredDefaultTheme, interfaceColors, overlayColors, resolveInterfaceTheme, setInterfaceTheme, useApplyInterfaceTheme, useInterfaceTheme } from './theme'

afterEach(() => { cleanup(); setInterfaceTheme('classic'); localStorage.clear() })
it('принимает только известные значения rollout-темы и сохраняет classic по умолчанию', () => {
  expect(configuredDefaultTheme('aeolian')).toBe('aeolian')
  expect(configuredDefaultTheme('classic')).toBe('classic')
  expect(configuredDefaultTheme('unexpected')).toBe('classic')
  expect(configuredDefaultTheme(undefined)).toBe('classic')
  expect(resolveInterfaceTheme(null, 'aeolian')).toBe('aeolian')
  expect(resolveInterfaceTheme('classic', 'aeolian')).toBe('classic')
  expect(resolveInterfaceTheme('invalid', 'aeolian')).toBe('aeolian')
})
it('переключает оформление и откатывает его без потери формы и выбора', () => {
  function Surface() {
    useApplyInterfaceTheme()
    const theme = useInterfaceTheme()
    const [draft, setDraft] = useState('')
    return <><input aria-label="Черновик" value={draft} onChange={(event) => setDraft(event.target.value)} /><span>{theme}</span></>
  }
  render(<Surface />)
  fireEvent.change(screen.getByLabelText('Черновик'), { target: { value: 'Сохранить текст' } })
  const input = screen.getByLabelText('Черновик')
  input.focus()
  act(() => setInterfaceTheme('aeolian'))
  expect(document.documentElement.dataset.interfaceTheme).toBe('aeolian')
  expect(localStorage.getItem('real-city.interface-theme')).toBe('aeolian')
  act(() => setInterfaceTheme('classic'))
  expect(input).toBe(screen.getByDisplayValue('Сохранить текст'))
  expect(document.activeElement).toBe(input)
  expect(document.documentElement.dataset.interfaceTheme).toBe('classic')
  expect(document.documentElement.style.getPropertyValue('--map-focus')).toBe(interfaceColors.focus)
  expect(overlayColors.focus).toBe(Number.parseInt(interfaceColors.focus.slice(1), 16))
})
