import { QueryClient, QueryClientProvider, useMutation } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { ActionFeedback } from './ActionFeedback'
import { ApiClientError } from '../../shared/api/client'
import { ActionState, actionErrorReason } from '../../shared/ui/ActionState'

afterEach(() => { cleanup(); localStorage.clear() })

it('отделяет ожидание сервера от подтверждения, не показывает содержимое ответа', async () => {
  let confirm!: (value: string) => void
  const result = new Promise<string>((resolve) => { confirm = resolve })
  function Action() {
    const action = useMutation({ mutationFn: () => result })
    return <button onClick={() => action.mutate()}>Строить</button>
  }
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  render(<QueryClientProvider client={client}><ActionFeedback /><Action /></QueryClientProvider>)
  fireEvent.click(screen.getByText('Строить'))
  await screen.findByText('Ожидаем ответ сервера')
  expect(screen.queryByText('Сервер подтвердил действие')).toBeNull()
  confirm('private-server-payload')
  await screen.findByText('Сервер подтвердил действие')
  expect(screen.queryByText('private-server-payload')).toBeNull()
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })
  fireEvent(window, new Event('offline'))
  expect(screen.getByText('Нет связи — подтверждение сервера недоступно')).toBeTruthy()
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
  fireEvent(window, new Event('online'))
  expect(screen.getByText('Интерфейс').closest('details')?.hasAttribute('open')).toBe(false)
  fireEvent.click(screen.getByText('Интерфейс'))
  fireEvent.click(screen.getByRole('button', { name: 'Эффекты: включены' }))
  expect(document.documentElement.dataset.uiEffects).toBe('off')
  expect(localStorage.getItem('real-city.ui-effects')).toBe('off')
  client.clear()
})

it('объясняет код отказа без личных данных и отличает отказ от успеха', async () => {
  function Action() {
    const action = useMutation({ mutationFn: async () => { throw new ApiClientError({ kind: 'forbidden', message: 'private-coordinate' }) } })
    return <button onClick={() => action.mutate()}>Атака</button>
  }
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  render(<QueryClientProvider client={client}><ActionFeedback /><Action /></QueryClientProvider>)
  fireEvent.click(screen.getByText('Атака'))
  await waitFor(() => expect(screen.getByText('Нет разрешения на действие.')).toBeTruthy())
  expect(screen.queryByText('private-coordinate')).toBeNull()
  expect(screen.queryByText('Сервер подтвердил действие')).toBeNull()
  client.clear()
})

it('предоставляет текст для всех состояний, не превращает таймер в live-поток', () => {
  const { container } = render(<ActionState phase="cooldown" reason="Доступно через 10 с" announce={false} />)
  expect(screen.getByText('Действие восстанавливается')).toBeTruthy()
  expect(container.querySelector('[role="status"]')).toBeNull()
  expect(actionErrorReason(new ApiClientError({ kind: 'rate_limited', message: '' }))).toContain('Подождите')
})
