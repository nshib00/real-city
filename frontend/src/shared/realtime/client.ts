import { getAccessToken, getRefreshToken, refreshTokens } from '../api/client'
import type { RealtimeEnvelope } from '../../../../shared/events/world'
import { clientTelemetry } from '../telemetry/clientTelemetry'

export type RealtimeStatus = 'connecting' | 'connected' | 'reconnecting' | 'offline'

type Listener = (event: RealtimeEnvelope) => void
type StatusListener = (status: RealtimeStatus) => void
type ResyncListener = (reason: 'reconnect' | 'gap' | 'subscription') => void

export class RealtimeClient {
  private socket: WebSocket | null = null
  private listeners = new Set<Listener>()
  private statusListeners = new Set<StatusListener>()
  private resyncListeners = new Set<ResyncListener>()
  private reconnectTimer: number | null = null
  private reconnectAttempt = 0
  private subscribedChunks = new Set<string>()
  private sentChunks = new Set<string>()
  private subscriptionInitialized = false
  private pendingSubscriptionAcks = 0
  private closedByUser = false
  private lastSeq = 0

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }
    const token = getAccessToken()
    if (!token) {
      if (getRefreshToken()) {
        void refreshTokens().then((refreshed) => {
          if (refreshed) {
            this.connect()
          } else {
            this.setStatus('offline')
          }
        })
        return
      }
      this.setStatus('offline')
      return
    }
    this.closedByUser = false
    this.setStatus(this.reconnectAttempt > 0 ? 'reconnecting' : 'connecting')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(`${protocol}//${window.location.host}/api/v1/realtime?token=${encodeURIComponent(token)}`)
    this.socket = socket
    socket.onopen = () => {
      if (this.socket !== socket) return
      const reconnected = this.reconnectAttempt > 0
      if (this.reconnectTimer !== null) {
        window.clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
      // Sequence numbers belong to a single socket connection.
      this.lastSeq = 0
      this.sentChunks.clear()
      this.subscriptionInitialized = false
      this.pendingSubscriptionAcks = 0
      this.reconnectAttempt = 0
      this.setStatus('connected')
      this.sendSubscription()
      if (reconnected) this.requestResync('reconnect')
    }
    socket.onmessage = (message) => { if (this.socket === socket) this.handleMessage(message) }
    socket.onclose = () => { if (this.socket === socket) this.scheduleReconnect() }
    socket.onerror = () => socket.close()
  }

  close() {
    this.closedByUser = true
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.socket?.close()
    this.socket = null
    this.setStatus('offline')
  }

  subscribeChunks(chunkIDs: string[]) {
    this.subscribedChunks = new Set(chunkIDs)
    this.sendSubscription()
  }

  onEvent(listener: Listener) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  onStatus(listener: StatusListener) {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
  }

  onResync(listener: ResyncListener) {
    this.resyncListeners.add(listener)
    return () => this.resyncListeners.delete(listener)
  }

  private handleMessage(message: MessageEvent) {
    let event: RealtimeEnvelope
    try {
      event = JSON.parse(String(message.data)) as RealtimeEnvelope
      if (!event || typeof event.type !== 'string' || !Number.isSafeInteger(event.seq) || event.seq < 0 || event.payload_version !== 1) {
        this.requestResync('gap')
        return
      }
    } catch {
      this.requestResync('gap')
      return
    }
    if (event.type === 'ack') {
      const payload = event.payload as { command?: string } | undefined
      if (payload?.command === 'subscribe' && this.pendingSubscriptionAcks > 0) {
        this.pendingSubscriptionAcks--
        // The initial HTTP snapshot may predate the server-side chunk subscription.
        this.requestResync('subscription')
      }
      for (const listener of this.listeners) listener(event)
      return
    }
    if (event.seq && event.seq <= this.lastSeq) {
      return
    }
    if (event.seq) {
      if (event.seq > this.lastSeq + 1) this.requestResync('gap')
      this.lastSeq = event.seq
    }
    if (event.type === 'realtime.resync_required') {
      this.requestResync('gap')
      return
    }
    for (const listener of this.listeners) {
      listener(event)
    }
  }

  private sendSubscription() {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return
    }
    const removed = [...this.sentChunks].filter((id) => !this.subscribedChunks.has(id))
    const added = [...this.subscribedChunks].filter((id) => !this.sentChunks.has(id))
    if (removed.length) this.socket.send(JSON.stringify({ type: 'unsubscribe', chunk_ids: removed }))
    if (added.length || !this.subscriptionInitialized) {
      this.socket.send(JSON.stringify({ type: 'subscribe', chunk_ids: added, private: true }))
      this.pendingSubscriptionAcks++
    }
    this.sentChunks = new Set(this.subscribedChunks)
    this.subscriptionInitialized = true
  }

  private requestResync(reason: 'reconnect' | 'gap' | 'subscription') {
    if (reason === 'gap') clientTelemetry.record('ws_gap')
    if (reason === 'reconnect') clientTelemetry.record('ws_recovered')
    for (const listener of this.resyncListeners) listener(reason)
  }

  private scheduleReconnect() {
    if (this.closedByUser) {
      return
    }
    if (this.reconnectTimer !== null) return
    this.setStatus('reconnecting')
    this.reconnectAttempt += 1
    // Spread reconnects after a server/network outage across a bounded window.
    const delay = Math.round(Math.min(1000 * 2 ** this.reconnectAttempt, 15000) * (0.75 + Math.random() * 0.5))
    this.reconnectTimer = window.setTimeout(() => this.connect(), delay)
  }

  private setStatus(status: RealtimeStatus) {
    if (status === 'reconnecting') clientTelemetry.record('ws_reconnecting')
    for (const listener of this.statusListeners) {
      listener(status)
    }
  }
}

export const realtimeClient = new RealtimeClient()
