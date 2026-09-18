import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Player } from '../auth/types'
import { useAuthStore } from '../auth/useAuthStore'
import { ProfilePanel } from './ProfilePanel'

const testPlayer = vi.hoisted(() => ({
  id: 'player_1',
  email: 'test@example.com',
  name: 'Frontier One',
  status: 'active',
  role: 'user',
  profile: {
    display_name: 'Frontier One',
    city_name: 'Северный рубеж',
    avatar_url: '',
    level: 3,
    xp: 280,
    next_level_xp: 500,
    settings: {
      notifications: {
        raid_alerts: true,
        production_ready: true,
        market_updates: false,
      },
      render_quality: 'medium',
    },
    updated_at: '2026-08-30T00:00:00Z',
  },
  created_at: '2026-08-30T00:00:00Z',
  updated_at: '2026-08-30T00:00:00Z',
}))

vi.mock('../auth/api', () => ({
  logout: vi.fn(async () => undefined),
  updateMe: vi.fn(async (input) => ({
    ...testPlayer,
    profile: {
      ...testPlayer.profile,
      display_name: input.display_name,
      city_name: input.city_name,
      avatar_url: input.avatar_url,
      settings: input.settings,
    },
  })),
}))

describe('ProfilePanel', () => {
  beforeEach(() => {
    useAuthStore.setState({ player: testPlayer as Player, isAuthenticated: true })
  })

  it('opens profile details and settings from compact player card', async () => {
    render(<ProfilePanel />)

    fireEvent.click(screen.getByLabelText('Открыть профиль игрока'))

    expect(screen.getAllByText('Северный рубеж').length).toBeGreaterThan(0)
    expect(screen.getByLabelText('Опыт: 280/500')).toBeTruthy()

    fireEvent.click(screen.getByText('Настройки'))

    expect(screen.getByLabelText('Настройки профиля')).toBeTruthy()
    fireEvent.change(screen.getByDisplayValue('Северный рубеж'), { target: { value: 'Новый рубеж' } })
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(useAuthStore.getState().player?.profile.city_name).toBe('Новый рубеж'))
  })
})
