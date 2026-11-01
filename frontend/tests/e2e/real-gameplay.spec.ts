import { test, expect } from 'playwright/test'

test('real login, shared map, construction, harvest and WebSocket deltas', async ({ page, request }) => {
 const nonce = `${Date.now()}${Math.floor(Math.random()*10000)}`
 const email = `e2e${nonce}@example.invalid`, password = 'StrongPass123!'
 const registered = await request.post('/api/v1/auth/register', { data: { email, name: `E2E${nonce}`, password } })
 expect(registered.status()).toBe(201)
 const frames: any[] = []
 page.on('websocket', socket => socket.on('framereceived', frame => { try { frames.push(JSON.parse(String(frame.payload))) } catch {} }))
 await page.goto('/')
 await page.getByLabel('Email', { exact: true }).fill(email)
 await page.getByLabel('Пароль', { exact: true }).fill(password)
 await page.getByRole('button', { name: 'Войти', exact: true }).click()
 await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
 await expect(page.locator('.pixi-stage canvas')).toBeVisible()
 await expect.poll(() => frames.some(f => f.type === 'ack' && f.payload?.command === 'subscribe')).toBe(true)
 const token = await page.evaluate(() => localStorage.getItem('real-city.access-token'))
 const headers = { Authorization: `Bearer ${token}` }
 const snapshot = await (await request.get('/api/v1/world/chunks?x=0&y=0&radius=1', { headers })).json()
 const tiles = snapshot.chunks.flatMap((c: any) => c.tiles).filter((t: any) => t.x < 32 && t.y < 32)
 // Fixture commands use the real authenticated API; no route stubs or fake WS are used.
 let built: any
 for (const tile of tiles.filter((t: any) => t.terrain === 'grass')) {
  const response = await request.post('/api/v1/buildings', { headers: { ...headers, 'Idempotency-Key': `e2ebuild-${nonce}-${tile.x}-${tile.y}` }, data: { type: 'town_hall', tile_x: tile.x, tile_y: tile.y } })
  if (response.status() === 201) { built = (await response.json()).building; break }
  expect([400,409,422]).toContain(response.status())
 }
 expect(built?.id).toBeTruthy()
 await expect.poll(() => frames.some(f => f.type === 'world.building.placed' && f.payload?.building?.id === built.id)).toBe(true)
 const completed = await (await request.get(`/api/v1/buildings/${built.id}`, { headers })).json()
 expect(completed.building.state).toBe('active')
 const before = await (await request.get('/api/v1/economy/inventory', { headers })).json()
 const wood = (response: any) => response.inventory.items.find((v: any) => v.resource === 'wood')?.amount ?? 0
 const forest = tiles.find((t: any) => t.terrain === 'forest' && t.forest_density > 0)
 expect(forest).toBeTruthy()
 const gathered = await request.post('/api/v1/world/tiles/chop-forest', { headers, data: { tile_x: forest.x, tile_y: forest.y } })
 expect(gathered.ok()).toBe(true)
 const after = await gathered.json()
 expect(wood(after.inventory)).toBeGreaterThan(wood(before.inventory))
 await expect.poll(() => frames.some(f => f.type === 'world.tile.changed' && f.payload?.tile?.x === forest.x && f.payload?.tile?.y === forest.y)).toBe(true)
 await page.reload()
 await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
 await expect(page.getByLabel('Ресурсы', { exact: true })).toBeVisible()
})
