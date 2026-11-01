import { expect, test } from 'playwright/test'
import type { Player } from '../../../src/features/auth/types'

const now = '2026-10-30T12:00:00Z'
const player: Player = {
  id: 'design-player', email: 'design@example.invalid', name: 'Город Эолии', role: 'user', status: 'active',
  created_at: now, updated_at: now,
  profile: { display_name: 'Город Эолии', city_name: 'Тихая долина', avatar_url: '', level: 1, xp: 0,
    next_level_xp: 100, updated_at: now,
    settings: { notifications: { attack_alerts: true, production_ready: true, market_updates: false }, render_quality: 'low' } },
}

test('исходный игровой экран с пустым выбором', async ({ page }, info) => {
  const unknown: string[] = []
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.text().includes('ui.error_boundary')) errors.push(message.text()) })
  await page.clock.setFixedTime(new Date(now))
  await page.addInitScript(() => {
    localStorage.setItem('real-city.access-token', 'design-access')
    localStorage.setItem('real-city.refresh-token', 'design-refresh')
  })
  await page.routeWebSocket('**/api/v1/realtime?*', socket => {
    // Соединение стабильно, события мира в этом снимке отсутствуют.
    socket.onMessage(() => {})
  })
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '')
    const lists: Record<string, string> = {
      '/buildings': 'buildings', '/buildings/catalog': 'buildings', '/resources/nodes': 'nodes',
      '/monsters': 'monsters', '/monster-loot': 'loot', '/threats': 'threats',
      '/production/jobs': 'jobs', '/production/recipes': 'recipes', '/players/nearby': 'players',
      '/combat/attacks': 'attacks', '/combat/history': 'records', '/chat/messages': 'messages', '/market/orders': 'orders',
    }
    if (path === '/players/me') return route.fulfill({ json: player })
    if (path === '/players/me/presence') return route.fulfill({ json: { status: 'ok' } })
    if (path === '/economy/inventory') return route.fulfill({ json: { inventory: {
      player_id: player.id, coin_capacity: 2000, updated_at: now,
      items: [{ resource: 'coins', amount: 50 }],
    } } })
    if (path === '/world/chunks' || path === '/world/viewport') return route.fulfill({ json: { chunks: [{
      map_id: 'design-world', chunk_x: 0, chunk_y: 0, version: 1,
      tiles: Array.from({ length: 256 }, (_, i) => ({ x: i % 16, y: Math.floor(i / 16), chunk_x: 0, chunk_y: 0,
        terrain: 'grass', elevation: 0, safe_zone: true })),
    }] } })
    if (lists[path]) return route.fulfill({ json: { [lists[path]]: [] } })
    unknown.push(`${route.request().method()} ${path}`)
    return route.fulfill({ status: 501, json: { error: { code: 'unmocked_design_request', message: path } } })
  })
  await page.goto('/')
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
  await expect(page.getByLabel('Ресурсы', { exact: true })).toContainText('Монеты')
  await expect(page.getByLabel('Инструменты', { exact: true })).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  await expect(page.locator('canvas').first()).toBeVisible()
  await page.screenshot({ path: info.outputPath('baseline.png'), animations: 'disabled' })
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
  expect(errors).toEqual([])
  expect([...new Set(unknown)]).toEqual([])
})
