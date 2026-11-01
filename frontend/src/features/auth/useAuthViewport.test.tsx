import { act, renderHook } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { useAuthViewport } from './useAuthViewport'

it('учитывает уменьшение visualViewport и очищает слушатели после входа', () => {
  const viewport = new EventTarget() as EventTarget & { height: number; offsetTop: number }
  viewport.height = 844; viewport.offsetTop = 0
  vi.stubGlobal('visualViewport', viewport)
  const { unmount } = renderHook(useAuthViewport)
  expect(document.documentElement.style.getPropertyValue('--auth-visible-height')).toBe('844px')
  act(() => { viewport.height = 420; viewport.offsetTop = 36; viewport.dispatchEvent(new Event('resize')) })
  expect(document.documentElement.style.getPropertyValue('--auth-visible-height')).toBe('420px')
  expect(document.documentElement.style.getPropertyValue('--auth-visible-top')).toBe('36px')
  unmount()
  viewport.height = 844; viewport.dispatchEvent(new Event('resize'))
  expect(document.documentElement.style.getPropertyValue('--auth-visible-height')).toBe('')
  vi.unstubAllGlobals()
})
