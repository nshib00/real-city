import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, expect, it, vi } from 'vitest'
import { PublicProfileButton } from './PublicProfileButton'
import { useAuthStore } from '../auth/useAuthStore'
import { getPublicProfile } from '../../shared/api/playerProfile'

vi.mock('../../shared/api/playerProfile', () => ({ getPublicProfile: vi.fn() }))
afterEach(() => { cleanup(); vi.resetAllMocks() })

function mount() {
  useAuthStore.setState({ player: { id: 'viewer' } as never })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  render(<QueryClientProvider client={client}><PublicProfileButton playerId="owner" /></QueryClientProvider>)
  fireEvent.click(screen.getByText('Профиль владельца'))
  return client
}

it('renders only allowed public fields even when the response contains private data', async () => {
  vi.mocked(getPublicProfile).mockResolvedValue({ profile: {
    player_id: 'owner', display_name: 'Строитель', level: 3, title: 'Мастер', scores: { economy: 30, private_stock: 987654 },
    email: 'secret@example.invalid', xp: 987654, settings: { secret: true },
  } } as never)
  const client = mount()
  expect(await screen.findByText('Строитель')).toBeTruthy()
  expect(screen.queryByText(/Экономика|secret@example|987654|private_stock/)).toBeNull()
  expect(getPublicProfile).toHaveBeenCalledWith('owner')
  client.clear()
})

it('offers retry after a failed request', async () => {
  vi.mocked(getPublicProfile).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ profile: {
    player_id: 'owner', display_name: 'Владелец', level: 1,
  } } as never)
  const client = mount()
  fireEvent.click(await screen.findByText('Повторить'))
  expect(await screen.findByText('Владелец')).toBeTruthy()
  expect(screen.queryByLabelText('Показатели профиля')).toBeNull()
  client.clear()
})
