import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, expect, it, vi } from 'vitest'
import type { Player } from '../auth/types'
import { useAuthStore } from '../auth/useAuthStore'
import { AdminPanel } from './AdminPanel'

const api = vi.hoisted(() => vi.fn())
vi.mock('../../shared/api/client', async (original) => ({ ...await original<typeof import('../../shared/api/client')>(), request: api }))
vi.mock('../../audio/playUiSound', () => ({ playUiSound: vi.fn() }))
afterEach(() => { cleanup(); useAuthStore.setState({ player: null }); vi.clearAllMocks() })
function player(role: Player['role']): Player {
  return { id: 'moderator', email: '', name: 'Модератор', role, status: 'active', profile: { display_name: '', city_name: '', avatar_url: '', level: 1, xp: 0, next_level_xp: null, settings: { render_quality: 'low', notifications: { attack_alerts: true, production_ready: true, market_updates: true } }, updated_at: '' }, created_at: '', updated_at: '' }
}
it('does not request administrative data for an ordinary player', () => {
  useAuthStore.setState({ player: player('user') })
  render(<AdminPanel />)
  expect(screen.queryByRole('button', { name: 'Администрирование' })).toBeNull()
  expect(api).not.toHaveBeenCalled()
})
it('requires a reason and submits the selected moderation decision', async () => {
  useAuthStore.setState({ player: player('admin') })
  api.mockImplementation(async (path: string) => path === '/admin/players' ? { players: [] } : path.endsWith('/audit') ? { actions: [] } : path === '/admin/chat/messages' ? { messages: [{ id: 'message', channel: 'global', author_id: 'author', body: 'Текст для проверки' }] } : { status: 'ok' })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><AdminPanel /></QueryClientProvider>)
  expect(api).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Администрирование' }))
  const reject = await screen.findByRole('button', { name: 'Удалить текст сообщения' })
  expect((reject as HTMLButtonElement).disabled).toBe(true)
  fireEvent.change(screen.getByLabelText('Причина решения'), { target: { value: 'Нарушение правил' } })
  fireEvent.click(reject)
  await waitFor(() => expect(api).toHaveBeenCalledWith('/admin/chat/messages/message', { method: 'PATCH', body: JSON.stringify({ action: 'reject', reason: 'Нарушение правил' }) }))
  client.clear()
})

it('requires a reason to suspend an account and preserves its role', async () => {
  useAuthStore.setState({ player: player('admin') })
  api.mockImplementation(async (path: string) => path === '/admin/players' ? { players: [{ id: 'target', name: 'Сосед', status: 'active', role: 'user' }] } : path === '/admin/chat/messages' ? { messages: [] } : path.endsWith('/audit') ? { actions: [] } : { status: 'ok' })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><AdminPanel /></QueryClientProvider>)
  fireEvent.click(screen.getByRole('button', { name: 'Администрирование' }))
  const suspend = await screen.findByRole('button', { name: 'Заблокировать Сосед' })
  expect((suspend as HTMLButtonElement).disabled).toBe(true)
  fireEvent.change(screen.getByLabelText('Причина решения'), { target: { value: 'Повторное нарушение' } })
  fireEvent.click(suspend)
  await waitFor(() => expect(api).toHaveBeenCalledWith('/admin/players/target', { method: 'PATCH', body: JSON.stringify({ status: 'suspended', role: 'user', reason: 'Повторное нарушение' }) }))
  client.clear()
})
