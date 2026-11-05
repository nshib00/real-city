import ws from 'k6/ws'
import { check } from 'k6'

const base = (__ENV.BASE_URL || 'http://127.0.0.1:8080').replace(/^http/, 'ws')
const token = __ENV.TOKEN || ''

export const options = {
  scenarios: { fanout: { executor: 'constant-vus', vus: Number(__ENV.WS_VUS || 50), duration: __ENV.DURATION || '1m' } },
  thresholds: { ws_connecting: ['p(95)<1000'], checks: ['rate>0.95'] },
}

export default function () {
  if (!token) throw new Error('TOKEN is required for WebSocket load test')
  const response = ws.connect(`${base}/api/v1/realtime?token=${encodeURIComponent(token)}`, {}, (socket) => {
    socket.on('open', () => socket.send(JSON.stringify({ type: 'subscribe', chunk_ids: [__ENV.CHUNK_ID || 'dev-world:0:0'], private: true })))
    socket.on('message', (message) => check(message, { 'valid envelope': (value) => {
      try { return typeof JSON.parse(value).type === 'string' } catch { return false }
    } }))
    socket.setTimeout(() => socket.close(), Number(__ENV.HOLD_MS || 30000))
  })
  check(response, { 'upgrade 101': (r) => r && r.status === 101 })
}
