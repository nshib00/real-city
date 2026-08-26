import { getAccessToken, getRefreshToken, refreshTokens } from '../api/client'
import type { RealtimeEnvelope } from '../../../../shared/events/world'

export type RealtimeStatus = 'connecting' | 'connected' | 'reconnecting' | 'offline'

type Listener = (event: RealtimeEnvelope) => void
type StatusListener = (status: RealtimeStatus) => void

export class RealtimeClient {
  private socket: WebSocket | null = null
  private listeners = new Set<Listener>()
  private statusListeners = new Set<StatusListener>()
  private reconnectTimer: number | null = null
  private reconnectAttempt = 0
  private subscribedChunks = new Set<string>()
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
    this.socket = new WebSocket(`${protocol}//${window.location.host}/api/v1/realtime?token=${encodeURIComponent(token)}`)
    this.socket.onopen = () => {
      this.reconnectAttempt = 0
      this.setStatus('connected')
      this.sendSubscription()
    }
    this.socket.onmessage = (message) => this.handleMessage(message)
    this.socket.onclose = () => this.scheduleReconnect()
    this.socket.onerror = () => this.socket?.close()
  }

  close() {
    this.closedByUser = true
    if (this.reconnectTimer) {
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

  private handleMessage(message: MessageEvent) {
    const event = JSON.parse(String(message.data)) as RealtimeEnvelope
    if (event.seq && event.seq <= this.lastSeq && event.type !== 'ack') {
      return
    }
    if (event.seq) {
      this.lastSeq = event.seq
    }
    for (const listener of this.listeners) {
      listener(event)
    }
  }

  private sendSubscription() {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return
    }
    this.socket.send(JSON.stringify({ type: 'subscribe', chunk_ids: [...this.subscribedChunks], private: true }))
  }

  private scheduleReconnect() {
    if (this.closedByUser) {
      return
    }
    this.setStatus('reconnecting')
    this.reconnectAttempt += 1
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 15000)
    this.reconnectTimer = window.setTimeout(() => this.connect(), delay)
  }

  private setStatus(status: RealtimeStatus) {
    for (const listener of this.statusListeners) {
      listener(status)
    }
  }
}

export const realtimeClient = new RealtimeClient()
