import http from 'k6/http'
import { check, sleep } from 'k6'

const base = __ENV.BASE_URL || 'http://127.0.0.1:8080'
const token = __ENV.TOKEN || ''
const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }

export const options = {
  scenarios: {
    chunks: { executor: 'constant-vus', vus: Number(__ENV.CHUNK_VUS || 4), duration: __ENV.DURATION || '1m', exec: 'chunks' },
    viewport: { executor: 'constant-vus', vus: Number(__ENV.VIEWPORT_VUS || 4), duration: __ENV.DURATION || '1m', exec: 'viewport' },
    commands: { executor: 'constant-vus', vus: Number(__ENV.COMMAND_VUS || 1), duration: __ENV.DURATION || '1m', exec: 'commands' },
  },
  thresholds: { http_req_failed: ['rate<0.05'], http_req_duration: ['p(95)<1000'] },
}

export function chunks() {
  const x = (__VU + __ITER) % 8
  const response = http.get(`${base}/api/v1/world/chunks?x=${x}&y=2&radius=1`, { tags: { operation: 'chunks' } })
  check(response, { 'chunks 200': (r) => r.status === 200 })
  sleep(0.2)
}

export function viewport() {
  const x = (__VU + __ITER) % 8 * 16
  const response = http.get(`${base}/api/v1/world/viewport?x=${x}&y=32&radius=48`, { tags: { operation: 'viewport' } })
  check(response, { 'viewport 200': (r) => r.status === 200 })
  sleep(0.2)
}

export function commands() {
  if (!token || __ENV.ENABLE_MUTATIONS !== '1') { sleep(1); return }
  const tile = Number(__ENV.PLACEMENT_TILE_START || 100) + __VU * 100 + __ITER
  const placement = http.post(`${base}/api/v1/buildings`, JSON.stringify({ type: __ENV.BUILDING_TYPE || 'road', tile_x: tile, tile_y: Number(__ENV.PLACEMENT_TILE_Y || 100) }), { headers, tags: { operation: 'placement' } })
  check(placement, { 'placement processed': (r) => r.status < 500 })
  const chat = http.post(`${base}/api/v1/chat/messages`, JSON.stringify({ channel: 'global', body: `load-${__VU}-${__ITER}` }), { headers, tags: { operation: 'chat' } })
  check(chat, { 'chat processed': (r) => r.status < 500 })
  sleep(1)
}
