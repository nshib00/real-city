import http from 'k6/http'
import { check, sleep } from 'k6'
import { Trend } from 'k6/metrics'

const base = __ENV.BASE_URL || 'http://127.0.0.1:8080'
const tickAverageMs = new Trend('simulation_tick_average_ms')

export const options = {
  scenarios: { ticks: { executor: 'constant-vus', vus: 1, duration: __ENV.DURATION || '1m' } },
  thresholds: { checks: ['rate>0.95'] },
}

function metric(text, prefix) {
  const line = text.split('\n').find((item) => item.startsWith(prefix))
  return line ? Number(line.substring(line.lastIndexOf(' ') + 1)) : null
}

export default function () {
  const response = http.get(`${base}/metrics`, { tags: { operation: 'simulation-metrics' } })
  const enabled = metric(response.body, 'real_city_simulation_enabled ')
  const heartbeat = metric(response.body, 'real_city_simulation_heartbeat_timestamp_seconds ')
  const sum = metric(response.body, 'real_city_simulation_tick_duration_seconds_sum{mode="scheduled",result="ok"}')
  const count = metric(response.body, 'real_city_simulation_tick_duration_seconds_count{mode="scheduled",result="ok"}')
  check(response, {
    'metrics available': (r) => r.status === 200,
    'simulation enabled': () => enabled === 1,
    'tick heartbeat fresh': () => heartbeat !== null && Date.now() / 1000 - heartbeat < Number(__ENV.MAX_HEARTBEAT_AGE || 5),
  })
  if (sum !== null && count > 0) tickAverageMs.add(sum / count * 1000)
  sleep(1)
}
