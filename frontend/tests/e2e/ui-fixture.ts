import type { Page } from 'playwright/test'
import { resourceCatalog } from '../../../shared/catalog/resources'
import { readFileSync } from 'node:fs'

const { chunk_size: CHUNK_SIZE, size_tiles: WORLD_SIZE } = JSON.parse(readFileSync(new URL('../../../data/world/config.json', import.meta.url), 'utf8')) as { chunk_size: number; size_tiles: number }

export const reviewTime = '2026-10-30T12:00:00Z'

/** Реальные React/Pixi и ассеты, изолированный API: проверки не меняют игровой сервер. */
export async function mockInterfaceWorld(page: Page, options: { objects?: boolean; terrain?: string; theme?: string } = {}) {
  const errors: string[] = []
  const unknown: string[] = []
  const actions: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.text().includes('ui.error_boundary')) errors.push(message.text()) })
  await page.clock.setFixedTime(new Date(reviewTime))
  await page.addInitScript((theme) => {
    localStorage.setItem('real-city.access-token', 'ui-review')
    localStorage.setItem('real-city.refresh-token', 'ui-review')
    if (theme) localStorage.setItem('real-city.interface-theme', theme)
  }, options.theme ?? process.env.REAL_CITY_REVIEW_THEME)
  await page.routeWebSocket('**/api/v1/realtime?*', socket => { socket.onMessage(() => {}) })
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace('/api/v1', '')
    if (route.request().method() !== 'GET' && path !== '/players/me/presence') actions.push(`${route.request().method()} ${path}`)
    const lists: Record<string, string> = {
      '/buildings': 'buildings', '/buildings/catalog': 'buildings', '/resources/nodes': 'nodes',
      '/monsters': 'monsters', '/monster-loot': 'loot', '/threats': 'threats',
      '/production/jobs': 'jobs', '/production/recipes': 'recipes', '/players/nearby': 'players',
      '/combat/history': 'records', '/combat/attacks': 'attacks', '/market/orders': 'orders',
    }
    if (path === '/players/me') return route.fulfill({ json: {
      id: 'player_e2e', email: 'review@example.invalid', name: 'Город Эолии', role: 'user', status: 'active',
      created_at: reviewTime, updated_at: reviewTime,
      profile: { display_name: 'Город Эолии', city_name: 'Тихая долина', avatar_url: '', level: 3, xp: 1000,
        next_level_xp: 1900, updated_at: reviewTime,
        settings: { notifications: { attack_alerts: true, production_ready: true, market_updates: false }, render_quality: 'low' } },
    } })
    if (path === '/players/me/presence') return route.fulfill({ json: { status: 'ok' } })
    if (path === '/alliances/me') return route.fulfill({ json: { profile: { alliance: null, self: null, members: [], invites: [], treasury: [], buffs: [], aid: [] } } })
    if (options.objects && path === '/buildings') return route.fulfill({ json: { buildings: [
      { id: 'review-own', owner_id: 'player_e2e', type: 'dugout', name: 'Землянка', level: 1, state: 'active', health: 35, max_health: 80, tile_x: 4, tile_y: 4, footprint_w: 1, footprint_h: 1, started_at: reviewTime, completes_at: null },
      { id: 'review-rival', owner_id: 'rival', type: 'wood_house', name: 'Деревянный дом', level: 1, state: 'active', health: 100, max_health: 100, tile_x: 8, tile_y: 4, footprint_w: 1, footprint_h: 1, started_at: reviewTime, completes_at: null },
      { id: 'review-center', owner_id: 'player_e2e', type: 'town_hall', name: 'Ратуша', level: 1, state: 'active', health: 100, max_health: 100, tile_x: 0, tile_y: 0, footprint_w: 1, footprint_h: 1, started_at: reviewTime, completes_at: null },
    ] } })
    if (options.objects && path.endsWith('/repair')) return route.fulfill({ json: { repair: { workers: 1, duration_seconds: 30, cost: [{ resource: 'wood', amount: 10 }] } } })
    if (options.objects && path === '/players/rival') return route.fulfill({ json: { id: 'rival', display_name: 'Соседний город', level: 3 } })
    if (options.objects && path === '/combat/rules') return route.fulfill({ json: { rules: { attack_range_tiles: 5, attack_cooldown_seconds: 30, summon_cost_coins: 100, summon_cooldown_seconds: 60, summon_max_alive: 1, summon_lifetime_seconds: 600 } } })
    if (path === '/economy/inventory') return route.fulfill({ json: { inventory: {
      player_id: 'player_e2e', coin_capacity: 2000000000, updated_at: reviewTime,
      items: resourceCatalog.map(resource => ({ resource: resource.id, amount: 123456789 })),
    } } })
    if (path === '/chat/messages') return route.fulfill({ json: { messages: [], read_state: { read_at: reviewTime, unread: 0 } } })
    if (path === '/world/chunks' || path === '/world/viewport') {
      const cx = Number(url.searchParams.get('x') ?? 0)
      const cy = Number(url.searchParams.get('y') ?? 0)
      const chunks = []
      for (let dy = -1; dy <= 0; dy++) for (let dx = -1; dx <= 0; dx++) {
        const count = WORLD_SIZE / CHUNK_SIZE
        const coord = { x: ((cx + dx) % count + count) % count, y: ((cy + dy) % count + count) % count }
        const chunk_x = coord.x, chunk_y = coord.y
        chunks.push({ map_id: 'review-world', chunk_x, chunk_y, version: 1,
          tiles: Array.from({ length: CHUNK_SIZE * 8 }, (_, index) => ({
            x: (chunk_x * CHUNK_SIZE + index % CHUNK_SIZE) % WORLD_SIZE, y: (chunk_y * CHUNK_SIZE + Math.floor(index / CHUNK_SIZE)) % WORLD_SIZE, chunk_x, chunk_y,
            terrain: options.terrain ?? (options.objects ? ['grass', 'grass', 'forest', 'water', 'mountain', 'ruins'][(index % CHUNK_SIZE + Math.floor(index / CHUNK_SIZE)) % 6] : 'grass'), elevation: 0, safe_zone: !options.objects,
          })) })
      }
      return route.fulfill({ json: { chunks } })
    }
    if (lists[path]) return route.fulfill({ json: { [lists[path]]: [] } })
    unknown.push(`${route.request().method()} ${path}`)
    return route.fulfill({ status: 501, json: { error: { code: 'unmocked_review_request', message: path } } })
  })
  return { errors, unknown, actions }
}
