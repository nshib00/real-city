import { afterEach, describe, expect, it, vi } from 'vitest'
import { RealtimeClient } from './client'

vi.mock('../api/client', () => ({
  getAccessToken: () => 'test-token',
  getRefreshToken: () => null,
  refreshTokens: vi.fn(),
}))

class FakeSocket {
  static OPEN = 1
  static CONNECTING = 0
  static instances: FakeSocket[] = []
  readyState = FakeSocket.OPEN
  onopen: (() => void) | null = null
  onmessage: ((message: MessageEvent) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  sent: Array<{ type: string; chunk_ids?: string[] }> = []
  constructor(_url: string) { FakeSocket.instances.push(this) }
  send(message: string) { this.sent.push(JSON.parse(message)) }
  close() { this.readyState = 3; this.onclose?.() }
  receive(seq: number) {
    this.onmessage?.({ data: JSON.stringify({ type: 'monster.attacked', event_id: `hit-${seq}`, seq,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1, payload: {} }) } as MessageEvent)
  }
  ack(seq = 0, command?: string) {
    this.onmessage?.({ data: JSON.stringify({ type: 'ack', event_id: 'ack', seq,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1, payload: command ? { command } : undefined }) } as MessageEvent)
  }
  resync(seq: number) {
    this.onmessage?.({ data: JSON.stringify({ type: 'realtime.resync_required', event_id: 'resync', seq,
      sent_at: '2026-10-25T00:00:00Z', payload_version: 1 }) } as MessageEvent)
  }
}

describe('realtime sequence', () => {
  afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); FakeSocket.instances = [] })

  it('schedules one bounded retry after repeated close notifications', () => {
    vi.useFakeTimers()
    vi.spyOn(Math, 'random').mockReturnValue(0)
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    client.connect()
    const socket = FakeSocket.instances[0]
    socket.readyState = 3
    socket.onclose?.()
    socket.onclose?.()
    vi.advanceTimersByTime(1499)
    expect(FakeSocket.instances).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(FakeSocket.instances).toHaveLength(2)
    client.close()
  })

  it('resyncs after malformed or incompatible frames and accepts the next valid event', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    const received = vi.fn(), resync = vi.fn()
    client.onEvent(received); client.onResync(resync); client.connect()
    const socket = FakeSocket.instances[0]
    socket.onopen?.()
    for (const data of ['{', 'null', '{"type":"monster.attacked","seq":1,"payload_version":2}']) {
      expect(() => socket.onmessage?.({ data } as MessageEvent)).not.toThrow()
    }
    expect(received).not.toHaveBeenCalled()
    expect(resync).toHaveBeenCalledTimes(3)
    socket.receive(1)
    expect(received).toHaveBeenCalledTimes(1)
    client.close()
  })

  it('accepts fresh events when a new socket restarts sequence numbering', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    const received: string[] = []
    client.onEvent((event) => received.push(event.event_id))
    client.connect()
    const first = FakeSocket.instances[0]
    first.onopen?.()
    first.receive(50)
    first.readyState = 3
    client.connect()
    const second = FakeSocket.instances[1]
    second.onopen?.()
    second.receive(1)
    expect(received).toEqual(['hit-50', 'hit-1'])
    client.close()
  })

  it('unsubscribes old chunks and sends only new ones', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    client.subscribeChunks(['dev-world:0:0', 'dev-world:0:1'])
    client.connect()
    const socket = FakeSocket.instances[0]
    socket.onopen?.()
    client.subscribeChunks(['dev-world:0:1', 'dev-world:1:1'])
    expect(socket.sent).toEqual([
      { type: 'subscribe', chunk_ids: ['dev-world:0:0', 'dev-world:0:1'], private: true },
      { type: 'unsubscribe', chunk_ids: ['dev-world:0:0'] },
      { type: 'subscribe', chunk_ids: ['dev-world:1:1'], private: true },
    ])
    client.close()
  })

  it('refreshes snapshots after the server confirms each new chunk subscription', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    const reasons: string[] = []
    client.onResync((reason) => reasons.push(reason))
    client.subscribeChunks(['dev-world:0:0'])
    client.connect()
    const socket = FakeSocket.instances[0]
    socket.onopen?.()
    socket.ack(0)
    expect(reasons).toEqual([])
    socket.ack(0, 'subscribe')
    expect(reasons).toEqual(['subscription'])
    socket.ack(0, 'subscribe')
    expect(reasons).toEqual(['subscription'])
    client.subscribeChunks(['dev-world:0:0', 'dev-world:1:0'])
    socket.ack(0, 'subscribe')
    expect(reasons).toEqual(['subscription', 'subscription'])
    client.close()
  })

  it('ignores acknowledgments for ordering and requests resync on a gap', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    const received: string[] = []
    const reasons: string[] = []
    client.onEvent((event) => { if (event.type !== 'ack') received.push(event.event_id) })
    client.onResync((reason) => reasons.push(reason))
    client.connect()
    const socket = FakeSocket.instances[0]
    socket.onopen?.()
    socket.ack(100)
    socket.receive(1)
    socket.receive(3)
    socket.receive(2)
    expect(received).toEqual(['hit-1', 'hit-3'])
    expect(reasons).toEqual(['gap'])
    client.close()
  })

  it('requests a snapshot after reconnect', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    const reasons: string[] = []
    client.onResync((reason) => reasons.push(reason))
    client.connect()
    FakeSocket.instances[0].onopen?.()
    FakeSocket.instances[0].readyState = 3
    FakeSocket.instances[0].onclose?.()
    client.connect()
    FakeSocket.instances[1].onopen?.()
    expect(reasons).toEqual(['reconnect'])
    client.close()
  })

  it('requests a snapshot when EventBus reports a dropped event', () => {
    vi.stubGlobal('WebSocket', FakeSocket)
    const client = new RealtimeClient()
    const reasons: string[] = []
    client.onResync((reason) => reasons.push(reason))
    client.connect()
    const socket = FakeSocket.instances[0]
    socket.onopen?.()
    socket.receive(1)
    socket.resync(2)
    socket.receive(3)
    expect(reasons).toEqual(['gap'])
    client.close()
  })
})
