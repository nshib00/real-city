import { beforeEach, describe, expect, it, vi } from 'vitest'

import { clearTokens, getAccessToken, getRefreshToken } from '../../shared/api/client'
import { login, logout } from './api'

describe('auth api', () => {
  beforeEach(() => {
    clearTokens()
    vi.restoreAllMocks()
  })

  it('stores tokens after login and clears them on logout', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            player: {
              id: 'player_1',
              email: 'test@example.com',
              name: 'Test City',
              status: 'active',
              role: 'user',
              profile: {
                display_name: 'Test City',
                city_name: 'Test City',
                avatar_url: '',
                level: 1,
                xp: 0,
                level_start_xp: 0,
                next_level_xp: 100,
                settings: {
                  notifications: {
                    attack_alerts: true,
                    production_ready: true,
                    market_updates: false,
                  },
                  render_quality: 'medium',
                },
                updated_at: '2026-07-24T00:00:00Z',
              },
              created_at: '2026-07-24T00:00:00Z',
              updated_at: '2026-07-24T00:00:00Z',
            },
            access_token: 'access',
            refresh_token: 'refresh',
            access_until: '2026-07-24T00:15:00Z',
            refresh_until: '2026-08-24T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'ok' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

    vi.stubGlobal('fetch', fetchMock)

    await login({ email: 'test@example.com', password: 'frontier123' })
    expect(getAccessToken()).toBe('access')
    expect(getRefreshToken()).toBe('refresh')

    await logout()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })
})
