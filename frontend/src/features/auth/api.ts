import { clearTokens, getRefreshToken, request, setTokens } from '../../shared/api/client'
import type { AuthResponse, Player, ProfileSettings } from './types'

export async function register(input: { email: string; name: string; password: string }) {
  const result = await request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  setTokens(result.access_token, result.refresh_token)
  return result
}

export async function login(input: { email: string; password: string }) {
  const result = await request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  setTokens(result.access_token, result.refresh_token)
  return result
}

export async function refresh() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('refresh token is missing')
  }
  const result = await request<AuthResponse>('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  setTokens(result.access_token, result.refresh_token)
  return result
}

export async function logout(allDevices = false) {
  const refreshToken = getRefreshToken()
  await request<{ status: string }>('/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken ?? '', all_devices: allDevices }),
  }).catch(() => undefined)
  clearTokens()
}

export async function getMe() {
  return request<Player>('/players/me')
}

export function getPublicPlayer(id: string) {
  return request<{ id: string; display_name: string; level: number }>(`/players/${encodeURIComponent(id)}`)
}

export async function updateMe(input: {
  display_name: string
  city_name: string
  avatar_url: string
  settings: ProfileSettings
}) {
  return request<Player>('/players/me', {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export async function changePassword(input: { current_password: string; new_password: string }) {
  return request<{ status: string }>('/players/me/password', {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}
