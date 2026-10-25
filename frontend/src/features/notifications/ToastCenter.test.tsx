import { act, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'

import { ToastCenter } from './ToastCenter'
import { showToast } from './toast'

afterEach(() => vi.useRealTimers())

it('shows a server-result toast once and removes it after five seconds', () => {
  vi.useFakeTimers()
  render(<ToastCenter />)
  act(() => showToast('warning', 'Не удалось вырубить лес'))
  expect(screen.getByRole('status').textContent).toBe('Не удалось вырубить лес')
  act(() => vi.advanceTimersByTime(5000))
  expect(screen.queryByRole('status')).toBeNull()
})
