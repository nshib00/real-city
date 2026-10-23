import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
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
    xp: 1000,
    level_start_xp: 700,
    next_level_xp: 1900,
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
  getMe: vi.fn(async () => testPlayer),
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
    expect(screen.getByLabelText('Опыт: 300/1200')).toBeTruthy()
    expect(screen.getByText('До следующего уровня: 900 XP')).toBeTruthy()

    fireEvent.click(screen.getByText('Настройки'))

    expect(screen.getByLabelText('Настройки профиля')).toBeTruthy()
    fireEvent.change(screen.getByDisplayValue('Северный рубеж'), { target: { value: 'Новый рубеж' } })
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(useAuthStore.getState().player?.profile.city_name).toBe('Новый рубеж'))
  })

  it('resets the XP bar at the next level and fills only with new XP', () => {
    useAuthStore.setState({ player: { ...testPlayer, profile: { ...testPlayer.profile, level: 2, xp: 200, level_start_xp: 200, next_level_xp: 700 } } as Player })
    const { container } = render(<ProfilePanel />)
    fireEvent.click(screen.getByLabelText('Открыть профиль игрока'))

    expect(screen.getByLabelText('Опыт: 0/500')).toBeTruthy()
    expect(screen.getByText('До следующего уровня: 500 XP')).toBeTruthy()
    expect(container.querySelector('.profile-xp-mini > span')?.getAttribute('style')).toBe('width: 0%;')

    act(() => {
      useAuthStore.setState({ player: { ...testPlayer, profile: { ...testPlayer.profile, level: 2, xp: 450, level_start_xp: 200, next_level_xp: 700 } } as Player })
    })
    expect(screen.getByLabelText('Опыт: 250/500')).toBeTruthy()
    expect(screen.getByText('До следующего уровня: 250 XP')).toBeTruthy()
    expect(container.querySelector('.profile-xp-mini > span')?.getAttribute('style')).toBe('width: 50%;')

    act(() => {
      useAuthStore.setState({ player: { ...testPlayer, profile: { ...testPlayer.profile, level: 15, xp: 18121200, level_start_xp: 18121200, next_level_xp: null } } as Player })
    })
    expect(screen.getByLabelText('Опыт: 0')).toBeTruthy()
    expect(screen.getByText('Максимальный уровень')).toBeTruthy()
    expect(container.querySelector('.profile-xp-mini > span')?.getAttribute('style')).toBe('width: 0%;')
  })

  it('shows level progress when the API response has no level_start_xp', () => {
    const profile = { ...testPlayer.profile } as Player['profile']
    delete profile.level_start_xp
    useAuthStore.setState({ player: { ...testPlayer, profile } as Player })
    const { container } = render(<ProfilePanel />)
    fireEvent.click(screen.getByLabelText('Открыть профиль игрока'))

    expect(screen.getByLabelText('Опыт: 300/1200')).toBeTruthy()
    expect(container.querySelector('.profile-xp-mini > span')?.getAttribute('style')).toBe('width: 25%;')
  })

  it('uses the specification thresholds even if the profile carries obsolete level values', () => {
    useAuthStore.setState({ player: { ...testPlayer, profile: { ...testPlayer.profile, level: 15, xp: 199, level_start_xp: 17400, next_level_xp: 0 } } as Player })
    render(<ProfilePanel />)
    fireEvent.click(screen.getByLabelText('Открыть профиль игрока'))

    expect(screen.getByText('До следующего уровня: 1 XP')).toBeTruthy()
    expect(screen.getByLabelText('Опыт: 199/200')).toBeTruthy()
    expect(screen.getByTitle('Уровень 1')).toBeTruthy()
  })
})
