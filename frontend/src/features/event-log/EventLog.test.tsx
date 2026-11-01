import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { EventLog } from './EventLog'
import { useGameStore } from '../../game/state/useGameStore'
import { useAuthStore } from '../auth/useAuthStore'

vi.mock('../chat/useChatChannels', () => ({ useChatChannels: () => [
  { data: { read_state: { unread: 2 } } }, { data: { read_state: { unread: 3 } } },
] }))
vi.mock('../chat/ChatPanel', () => ({ ChatPanel: () => <p>Сообщения чата</p> }))
afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('shows the aggregate badge while collapsed and acknowledges events only when displayed', () => {
  localStorage.clear()
  vi.spyOn(document, 'hidden', 'get').mockReturnValue(false)
  useAuthStore.setState({ player: { id: 'p1' } as never })
  useGameStore.setState({ cannonShots: [{ id: 'a', buildingId: 'b', monsterId: 'm', damage: 10 }] as never,
    uiPreferences: { ...useGameStore.getState().uiPreferences, isChatCollapsed: true } })
  render(<EventLog />)
  expect(screen.getByLabelText('Непрочитано: 6')).toBeTruthy()
  expect(localStorage.getItem('real-city.events.read.p1')).toBeNull()
  fireEvent.click(screen.getByLabelText('Развернуть чат и события'))
  expect(JSON.parse(localStorage.getItem('real-city.events.read.p1')!)).toEqual(['a'])
  expect(screen.getByRole('tab', { name: 'Чат 5' })).toBeTruthy()
  fireEvent.click(screen.getByLabelText('Свернуть чат и события'))
  expect(screen.getByLabelText('Непрочитано: 5')).toBeTruthy()
})
