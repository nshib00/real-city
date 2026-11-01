import { StrictMode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen, waitFor, cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthScreen } from './AuthScreen'
import { AuthGate } from './AuthGate'
import { useAuthStore } from './useAuthStore'
import { FirstCityHelp } from '../buildings/FirstCityHelp'
import { useGameStore } from '../../game/state/useGameStore'

const player = { id: 'start-test', name: 'Город', profile: {} }
beforeEach(() => { localStorage.clear(); useAuthStore.setState({ player: null, isAuthenticated: false }) })
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear() })
describe('вход в мир', () => {
  it('сохраняет поля и показывает серверную ошибку поля, пароль можно показать', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async url => String(url) === '/ready'
      ? new Response(JSON.stringify({ status: 'ready' }))
      : new Response(JSON.stringify({ error: { kind: 'validation', message: 'Проверьте email', fields: { email: 'Адрес уже занят' } } }), { status: 422 }))
    render(<AuthScreen />)
    fireEvent.click(screen.getByRole('button', { name: 'Начать играть' }))
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@example.invalid' } })
    fireEvent.change(screen.getByLabelText('Имя города'), { target: { value: 'Город' } })
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'long-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Показать пароль' }))
    expect((screen.getByLabelText('Пароль') as HTMLInputElement).type).toBe('text')
    fireEvent.submit(screen.getByRole('button', { name: 'Создать город' }).closest('form')!)
    await screen.findByText('Адрес уже занят')
    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('test@example.invalid')
    expect(screen.getByLabelText('Email').getAttribute('aria-invalid')).toBe('true')
  })
  it('StrictMode проверяет сессию один раз и сразу открывает карту', async () => {
    localStorage.setItem('real-city.access-token', 'valid')
    let resolve!: (response: Response) => void
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(r => { resolve = r }))
    render(<StrictMode><AuthGate><div>Карта готова</div></AuthGate></StrictMode>)
    await act(async () => resolve(new Response(JSON.stringify(player))))
    await screen.findByText('Карта готова')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
  it('сетевая ошибка не стирает сессию; повтор открывает карту', async () => {
    localStorage.setItem('real-city.access-token', 'valid')
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(new Response(JSON.stringify(player)))
    render(<AuthGate><div>Карта готова</div></AuthGate>)
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить подключение' }))
    await screen.findByText('Карта готова')
    expect(localStorage.getItem('real-city.access-token')).toBe('valid')
  })
  it('истечение открывает вход с объяснением', async () => {
    localStorage.setItem('real-city.access-token', 'expired')
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ error: { kind: 'unauthorized', message: 'Expired' } }), { status: 401 }))
    render(<AuthGate><div>Карта готова</div></AuthGate>)
    await screen.findByText('Сессия истекла. Войдите снова, чтобы вернуться к карте.')
    expect(localStorage.getItem('real-city.access-token')).toBeNull()
  })
  it('помощь появляется после списка построек, закрывается и не блокирует карту', async () => {
    useAuthStore.setState({ player: player as never, isAuthenticated: true })
    useGameStore.setState({ buildings: [], uiPreferences: { ...useGameStore.getState().uiPreferences, buildMenuOpen: false } })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ buildings: [] })))
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><FirstCityHelp /></QueryClientProvider>)
    await screen.findByRole('complementary', { name: 'Первый город' })
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть помощь' }))
    await waitFor(() => expect(screen.queryByRole('complementary')).toBeNull())
    expect(localStorage.getItem('real-city.first-city-help.start-test')).toBe('dismissed')
    client.clear()
  })
})
