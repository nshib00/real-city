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
})
