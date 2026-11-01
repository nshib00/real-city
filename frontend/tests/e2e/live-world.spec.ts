import { test, expect } from 'playwright/test'

// Accounts are provisioned only in the disposable CI database by cmd/test-admin.
// No gameplay endpoint bypasses timers, costs, ownership or XP rules.
test('two players: upgrade, production, trade, private chat, destruction and XP', async ({ page, request }, info) => {
  test.setTimeout(720_000)
  const password = process.env.REAL_CITY_E2E_PASSWORD
  test.skip(!password, 'Provision test accounts with cmd/test-admin and set REAL_CITY_E2E_PASSWORD')
  const nonce = `${Date.now()}-${info.project.name}`
  const email = `e2e-${info.project.name}-a@example.invalid`
  const rivalEmail = `e2e-${info.project.name}-b@example.invalid`
  const login = async (mail: string) => {
    const response = await request.post('/api/v1/auth/login', { data: { email: mail, password } })
    expect(response.ok(), await response.text()).toBe(true)
    return response.json()
  }
  const rival = await login(rivalEmail)
  const frames: any[] = []
  page.on('websocket', socket => socket.on('framereceived', frame => { try { frames.push(JSON.parse(String(frame.payload))) } catch {} }))
  await page.goto('/')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Пароль', { exact: true }).fill(password!)
  await page.getByRole('button', { name: 'Войти', exact: true }).click()
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
  const token = await page.evaluate(() => localStorage.getItem('real-city.access-token'))
  expect(token).toBeTruthy()
  const headers = { Authorization: `Bearer ${token}` }
  const otherHeaders = { Authorization: `Bearer ${rival.access_token}` }
  const json = async (method: string, path: string, data?: unknown, other = false) => {
    const response = await request.fetch(`/api/v1${path}`, { method, headers: { ...(other ? otherHeaders : headers), 'Idempotency-Key': `${nonce}-${crypto.randomUUID()}` }, data })
    expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBe(true)
    return response.json()
  }
  // A retry owns the same disposable fixture accounts. Remove only their
  // previous scenario objects/reserves before starting a new attempt.
  for (const other of [false, true]) {
    for (const building of (await json('GET', '/buildings', undefined, other)).buildings) {
      if (['town_hall', 'lumber_yard'].includes(building.type)) await json('DELETE', `/buildings/${building.id}`, undefined, other)
    }
  }
  const ownId = (await json('GET', '/players/me')).id
  for (const order of (await json('GET', '/market/orders?status=open&limit=100')).orders) {
    if (order.player_id === ownId || order.player_id === rival.player.id) await json('DELETE', `/market/orders/${order.id}`, undefined, order.player_id === rival.player.id)
  }
  const snapshot = await json('GET', '/world/viewport?x=80&y=80&radius=64')
  const tiles = snapshot.chunks.flatMap((c: any) => c.tiles).filter((t: any) => t.terrain === 'grass')
  const place = async (type: string, other = false, near?: any) => {
    let attempts = 0
    for (const tile of tiles) {
      if (near && (Math.abs(tile.x - near.tile_x) + Math.abs(tile.y - near.tile_y) > 6)) continue
      if (++attempts > 25) break
      const response = await request.post('/api/v1/buildings', { headers: { ...(other ? otherHeaders : headers), 'Idempotency-Key': `${nonce}-${type}-${tile.x}-${tile.y}` }, data: { type, tile_x: tile.x, tile_y: tile.y } })
      if (response.status() === 201) return (await response.json()).building
      expect([400, 409, 422], await response.text()).toContain(response.status())
    }
    throw new Error(`No free tile for ${type}`)
  }
  const center = await place('town_hall')
  const victim = await place('town_hall', true, center)
  let factory = await place('lumber_yard', false, center)
  factory = (await json('PATCH', `/buildings/${factory.id}`, { action: 'rush_complete' })).building
  expect(factory.state).toBe('active')
  const xpBefore = (await json('GET', '/players/me')).profile.xp
  factory = (await json('PATCH', `/buildings/${factory.id}`, { action: 'upgrade' })).building
  expect(factory.state).toBe('building')
  expect((await json('GET', '/players/me')).profile.xp).toBe(xpBefore)
  factory = (await json('PATCH', `/buildings/${factory.id}`, { action: 'rush_complete' })).building
  expect(factory.level).toBe(2)
  expect((await json('GET', '/players/me')).profile.xp).toBeGreaterThan(xpBefore)
  const { job } = await json('POST', '/production/jobs', { building_id: factory.id, recipe_id: 'planks_from_wood' })

  const sell = (await json('POST', '/market/orders', { side: 'sell', resource: 'throwing_knives', amount: 6, price: 12 })).order
  await json('POST', '/market/orders', { side: 'buy', resource: 'throwing_knives', amount: 2, price: 4 }, true)
  const orders = (await json('GET', '/market/orders?status=open')).orders
  expect(orders.find((o: any) => o.id === sell.id)?.filled_amount).toBe(2)
  await json('DELETE', `/market/orders/${sell.id}`)

  const secret = (await json('POST', '/chat/messages', { channel: 'private', recipient: rival.player.id, body: `Проверка приватности ${nonce}` })).message
  const history = await json('GET', '/chat/messages?channel=private&limit=1', undefined, true)
  expect(history.messages.some((m: any) => m.id === secret.id)).toBe(true)
  expect(history.next_cursor).toBeTruthy()
  const earlier = await json('GET', `/chat/messages?channel=private&limit=1&before=${encodeURIComponent(history.next_cursor)}`, undefined, true)
  expect(earlier.messages.some((m: any) => m.id === secret.id)).toBe(false)
  const outsiderResponse = await request.post('/api/v1/auth/register', { data: { email: `outsider-${nonce}@example.invalid`, name: `Outside${Date.now()}`, password } })
  expect(outsiderResponse.status()).toBe(201)
  const outsider = await outsiderResponse.json()
  const privateResponse = await request.get('/api/v1/chat/messages?channel=private', { headers: { Authorization: `Bearer ${outsider.access_token}` } })
  expect((await privateResponse.json()).messages).toEqual([])

  const attackXP = (await json('GET', '/players/me')).profile.xp
  await json('POST', `/buildings/${victim.id}/weapons`, { weapon: 'throwing_knives' })
  const rules = (await json('GET', '/combat/rules')).rules
  await page.waitForTimeout(rules.attack_cooldown_seconds * 1000 + 100)
  await json('POST', `/buildings/${victim.id}/weapons`, { weapon: 'throwing_knives' })
  expect((await json('GET', `/buildings/${victim.id}`, undefined, true)).building.state).toBe('ruined')
  const record = (await json('GET', '/combat/history')).records.find((r: any) => r.building_id === victim.id && r.destroyed)
  expect(record.xp).toBeGreaterThan(0)
  expect((await json('GET', '/players/me')).profile.xp - attackXP).toBe(record.xp)
  await expect.poll(() => frames.some(f => f.type === 'combat.resolved' && f.payload?.building_id === victim.id && f.payload?.destroyed)).toBe(true)
  const outsiderCombat = await request.get('/api/v1/combat/history', { headers: { Authorization: `Bearer ${outsider.access_token}` } })
  expect((await outsiderCombat.json()).records).toEqual([])

  // Wait for the real level-2 timer. Worker completion and collection stay server-owned.
  await expect.poll(() => Date.now() >= Date.parse(job.completes_at), { timeout: 520_000, intervals: [2000] }).toBe(true)
  const resourceAmount = (r: any, id: string) => r.inventory.items.find((v: any) => v.resource === id)?.amount ?? 0
  const before = await json('GET', '/economy/inventory')
  const collected = await json('PATCH', `/production/jobs/${job.id}`, { action: 'complete' })
  expect(resourceAmount(collected, 'planks')).toBeGreaterThan(resourceAmount(before, 'planks'))
  const replay = await json('PATCH', `/production/jobs/${job.id}`, { action: 'complete' })
  expect(resourceAmount(replay, 'planks')).toBe(resourceAmount(collected, 'planks'))
  await page.context().setOffline(true)
  await page.context().setOffline(false)
  await page.reload()
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
})
