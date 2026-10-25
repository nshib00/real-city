import { afterEach, describe, expect, it, vi } from 'vitest'

import { request } from './client'

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('adds idempotency keys to unsafe durable POST routes', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }))

    await request('/market/orders', { method: 'POST', body: JSON.stringify({}) })

    const init = fetchMock.mock.calls[0][1] as RequestInit
    const headers = init.headers as Headers
    expect(headers.get('Idempotency-Key')).toBeTruthy()
  })

  it('preserves a raid key after refreshing an expired access token', async () => {
    localStorage.setItem('real-city.access-token', 'expired')
    localStorage.setItem('real-city.refresh-token', 'refresh')
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: 'new', refresh_token: 'next' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ raid: { id: 'one' } }), { status: 201 }))

    await request('/raids', { method: 'POST', body: JSON.stringify({ target_building_id: 'target' }) })

    const first = (fetchMock.mock.calls[0][1] as RequestInit).headers as Headers
    const replay = (fetchMock.mock.calls[2][1] as RequestInit).headers as Headers
    expect(first.get('Idempotency-Key')).toBeTruthy()
    expect(replay.get('Idempotency-Key')).toBe(first.get('Idempotency-Key'))
    expect(replay.get('Authorization')).toBe('Bearer new')
  })
})
