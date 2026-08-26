import type { APIError } from '../contracts'

const accessTokenKey = 'real-city.access-token'
const refreshTokenKey = 'real-city.refresh-token'

export class ApiClientError extends Error {
  constructor(public readonly apiError: APIError) {
    super(apiError.message)
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  return requestWithAuth<T>(path, init, true)
}

async function requestWithAuth<T>(path: string, init: RequestInit | undefined, allowRefresh: boolean): Promise<T> {
  const token = getAccessToken()
  const response = await fetch(`/api/v1${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
    ...init,
  })

  if (response.status === 401 && allowRefresh && shouldRefresh(path) && getRefreshToken()) {
    const refreshed = await refreshTokens()
    if (refreshed) {
      return requestWithAuth<T>(path, init, false)
    }
  }

  if (!response.ok) {
    const payload = (await response.json()) as { error: APIError }
    throw new ApiClientError(payload.error)
  }

  return (await response.json()) as T
}

function shouldRefresh(path: string) {
  return !path.startsWith('/auth/login') && !path.startsWith('/auth/register') && !path.startsWith('/auth/refresh')
}

export async function refreshTokens() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return false
  }
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!response.ok) {
    clearTokens()
    return false
  }
  const payload = (await response.json()) as { access_token: string; refresh_token: string }
  setTokens(payload.access_token, payload.refresh_token)
  return true
}

export function getAccessToken() {
  return localStorage.getItem(accessTokenKey)
}

export function getRefreshToken() {
  return localStorage.getItem(refreshTokenKey)
}

export function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(accessTokenKey, accessToken)
  localStorage.setItem(refreshTokenKey, refreshToken)
}

export function clearTokens() {
  localStorage.removeItem(accessTokenKey)
  localStorage.removeItem(refreshTokenKey)
}
