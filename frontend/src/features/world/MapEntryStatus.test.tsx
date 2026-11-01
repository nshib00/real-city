import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { MapEntryStatus } from './MapEntryStatus'
import { useVisibleChunks } from './useVisibleChunks'

function Entry() { return <MapEntryStatus query={useVisibleChunks({ x: 0, y: 0 })} /> }

afterEach(() => { cleanup(); vi.restoreAllMocks() })
it('показывает реальные этапы и повторяет API без повторного запуска графики', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('offline')).mockResolvedValue(new Response(JSON.stringify({ chunks: [] })))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><Entry /></QueryClientProvider>)
  fireEvent.click(await screen.findByRole('button', { name: 'Повторить загрузку карты' }))
  await screen.findByText('Подготавливаем графику карты…')
  await act(async () => { window.dispatchEvent(new Event('real-city:map-ready')) })
  await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
  expect(fetchMock).toHaveBeenCalledTimes(2)
  client.clear()
})
it('ошибка WebGL предлагает запуск, а повтор не перезагружает приложение', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ chunks: [] })))
  const retry = vi.fn()
  window.addEventListener('real-city:retry-renderer', retry)
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><Entry /></QueryClientProvider>)
  await act(async () => { window.dispatchEvent(new Event('real-city:map-failed')) })
  fireEvent.click(screen.getByRole('button', { name: 'Повторить запуск карты' }))
  expect(retry).toHaveBeenCalledTimes(1)
  await act(async () => { window.dispatchEvent(new Event('real-city:map-ready')) })
  await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
  window.removeEventListener('real-city:retry-renderer', retry)
  client.clear()
})
