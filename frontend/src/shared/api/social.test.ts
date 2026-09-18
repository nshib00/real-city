import { afterEach, describe, expect, it, vi } from 'vitest'

import { createAlliance, createMarketOrder, listChatMessages, sendChatMessage } from './social'

describe('social api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('calls alliance, chat and market endpoints', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ profile: { alliance: null, self: null, members: [], invites: [], treasury: [], buffs: [], aid: [] }, messages: [], order: {} }),
    } as Response)

    await createAlliance('Северный караван')
    await listChatMessages('global')
    await sendChatMessage({ channel: 'global', body: 'готовлю доски' })
    await createMarketOrder({ side: 'sell', resource: 'wood', amount: 10, price: 20 })

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      '/api/v1/alliances',
      '/api/v1/chat/messages?channel=global&limit=60',
      '/api/v1/chat/messages',
      '/api/v1/market/orders',
    ])
  })
})
