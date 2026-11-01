import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import type { CombatRecord } from '../../../../shared/events/combat'
import { useGameStore } from '../../game/state/useGameStore'
import { NotificationCenter } from './NotificationCenter'

vi.mock('../auth/useAuthStore', () => ({ useAuthStore: (select: (state: unknown) => unknown) => select({ player: { id: 'p1' } }) }))
const clients: QueryClient[] = []
afterEach(() => { cleanup(); clients.splice(0).forEach((client) => client.clear()) })

function record(id: string, owner: string, damage: number): CombatRecord {
  return { id, owner_id: owner, attacker_id: 'attacker', building_id: owner + '-building', building_type: 'dugout', level: 1, damage, destroyed: false, xp: 0, base_xp: 0, source: 'weapon', created_at: '2026-10-30T12:00:00Z' }
}

it('groups repeated attacks, prioritizes threats to the player and marks visible history read', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
  clients.push(client)
  client.setQueryData(['combat', 'history', 'p1'], { records: [record('foreign', 'other', 7), record('own1', 'p1', 10), record('own2', 'p1', 20)] })
  useGameStore.setState({ realtimeStatus: 'offline', buildings: [], uiPreferences: { ...useGameStore.getState().uiPreferences, areNotificationsCollapsed: false } })
  const { container } = render(<QueryClientProvider client={client}><NotificationCenter /></QueryClientProvider>)
  expect(container.querySelectorAll('article')).toHaveLength(2)
  expect(container.querySelector('article')?.classList.contains('notification-danger')).toBe(true)
  expect(screen.getByText(/Урон: 30/)).toBeTruthy()
  expect(screen.getByLabelText('Непрочитанные уведомления').textContent).toBe('3')
  expect(screen.getByText(/Нет связи с миром/)).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Отметить прочитанными' }))
  expect(screen.getByLabelText('Непрочитанные уведомления').textContent).toBe('0')
  expect(screen.queryByRole('button', { name: 'Показать на карте' })).toBeNull()
})

it('announces new own threats once, without announcing history or polling ticks', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
  clients.push(client)
  client.setQueryData(['combat', 'history', 'p1'], { records: [record('old', 'p1', 1)] })
  const { container } = render(<QueryClientProvider client={client}><NotificationCenter /></QueryClientProvider>)
  const live = container.querySelector('.ui-sr-only')!
  expect(live.textContent).toBe('')
  act(() => { client.setQueryData(['combat', 'history', 'p1'], { records: [record('new', 'p1', 2), record('old', 'p1', 1)] }) })
  await waitFor(() => expect(live.textContent).toContain('Всего за сеанс: 1'))
  const message = live.textContent
  act(() => { client.setQueryData(['combat', 'history', 'p1'], { records: [record('foreign', 'other', 1), record('new', 'p1', 2), record('old', 'p1', 1)] }) })
  await waitFor(() => expect(screen.getByLabelText('Непрочитанные уведомления').textContent).toBe('3'))
  expect(live.textContent).toBe(message)
  expect(container.querySelector('section')?.hasAttribute('aria-live')).toBe(false)
})
