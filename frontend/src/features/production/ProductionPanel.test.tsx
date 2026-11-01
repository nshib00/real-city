import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { useGameStore } from '../../game/state/useGameStore'
import { ProductionPanel } from './ProductionPanel'

const api = vi.hoisted(() => ({ patch: vi.fn(), start: vi.fn() }))
vi.mock('../../shared/api/economy', () => ({
  listProductionRecipes: vi.fn(async () => ({ recipes: [] })),
  listProductionJobs: vi.fn(async () => ({ jobs: [] })),
  patchProductionJob: api.patch, startProduction: api.start,
}))
vi.mock('../economy/useInventory', () => ({
  useInventory: () => ({ data: { inventory: { items: [] } } }),
  inventoryAmount: () => 0, availablePopulation: () => 0,
}))
vi.mock('../auth/useAuthStore', () => ({ useAuthStore: (select: (state: unknown) => unknown) => select({ player: { id: 'p1', profile: { settings: { notifications: {} } } } }) }))

let client: QueryClient
beforeEach(() => {
  client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
  client.setQueryData(['production', 'recipes'], { recipes: [] })
  useGameStore.setState({ constructionNow: Date.parse('2026-10-30T12:01:00Z'), buildings: [] })
})
afterEach(() => { cleanup(); client.clear(); vi.clearAllMocks() })

it('waits for server ready state after the deadline, then collects instead of cancelling', () => {
  const job = { id: 'j1', building_id: 'b1', recipe_id: 'planks', state: 'running', started_at: '2026-10-30T12:00:00Z', completes_at: '2026-10-30T12:00:30Z' }
  client.setQueryData(['production', 'jobs'], { jobs: [job] })
  api.patch.mockReturnValue(new Promise(() => {}))
  render(<QueryClientProvider client={client}><ProductionPanel /></QueryClientProvider>)
  expect(screen.getByText('Ожидаем подтверждения готовности сервером')).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Собрать' })).toBeNull()
  act(() => { client.setQueryData(['production', 'jobs'], { jobs: [{ ...job, state: 'ready' }] }) })
  return screen.findByRole('button', { name: 'Собрать' }).then(async (button) => {
    fireEvent.click(button)
    await vi.waitFor(() => expect(api.patch).toHaveBeenCalledWith('j1', 'complete'))
  })
})

it('explains empty recipes and jobs without inventing production', () => {
  client.setQueryData(['production', 'jobs'], { jobs: [] })
  render(<QueryClientProvider client={client}><ProductionPanel /></QueryClientProvider>)
  expect(screen.getByText(/Рецептов пока нет/)).toBeTruthy()
  expect(screen.getByText(/Заданий нет/)).toBeTruthy()
  expect(api.start).not.toHaveBeenCalled()
})
