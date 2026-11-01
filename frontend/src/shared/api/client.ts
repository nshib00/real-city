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
  const headers = new Headers(init?.headers)
  headers.set('Content-Type', headers.get('Content-Type') ?? 'application/json')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (needsIdempotencyKey(path, init?.method) && !headers.has('Idempotency-Key')) {
    headers.set('Idempotency-Key', createIdempotencyKey())
  }
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers,
  })

  if (response.status === 401 && allowRefresh && shouldRefresh(path) && getRefreshToken()) {
    const refreshed = await refreshTokens()
    if (refreshed) {
      return requestWithAuth<T>(path, { ...init, headers }, false)
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

function needsIdempotencyKey(path: string, method = 'GET') {
  if (method.toUpperCase() !== 'POST') {
    return false
  }
  return path === '/buildings' || path === '/combat/monsters' || /^\/buildings\/[^/]+\/weapons$/.test(path) || path === '/market/orders' || path === '/alliances/invites'
}

function createIdempotencyKey() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

let pendingRefresh: Promise<boolean> | null = null
export function refreshTokens(): Promise<boolean> {
  if (!pendingRefresh) pendingRefresh = performRefresh().finally(() => { pendingRefresh = null })
  return pendingRefresh
}

async function performRefresh() {
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
    if (response.status === 401 || response.status === 403) {
      clearTokens()
      return false
    }
    throw new Error('Не удалось обновить сессию. Повторите подключение.')
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
