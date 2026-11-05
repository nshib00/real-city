import { expect, test } from 'playwright/test'

test('карта сохраняет кадры при zoom, pan и 60 сек прокрутки через швы', async ({ page, request }, info) => {
  test.setTimeout(150_000)
  const password = `Map${crypto.randomUUID()}!`
  const email = `map-perf-${crypto.randomUUID()}@example.invalid`
  const account = await request.post('/api/v1/auth/register', { data: { email, name: `MapPerf${Date.now()}`, password } })
  expect(account.status(), await account.text()).toBe(201)
  const tokens = await account.json()
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('real-city.access-token', access)
    localStorage.setItem('real-city.refresh-token', refresh)
  }, { access: tokens.access_token, refresh: tokens.refresh_token })

  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('response', (response) => {
    if (response.url().includes('/api/v1/world/chunks') && response.status() >= 500) errors.push(`chunk HTTP ${response.status()}`)
  })
  await page.goto('/?perf=mixed&perfBuildings=24&perfMonsters=8&perfResources=6&perfTileRadius=8')
  const map = page.getByLabel('Карта', { exact: true })
  await expect(map.locator('canvas')).toBeVisible({ timeout: 30_000 })
  await map.focus()
  const started = Date.now()
  let actions = 0
  while (Date.now() - started < 60_000) {
    await map.press('ArrowRight')
    await map.press(actions % 2 ? '+' : '-')
    actions++
    await page.waitForTimeout(250)
  }
  const canvas = map.locator('canvas')
  await expect(canvas).toBeVisible()
  const size = await canvas.evaluate((element) => ({ width: element.width, height: element.height }))
  expect(size.width).toBeGreaterThan(0)
  expect(size.height).toBeGreaterThan(0)
  const hud = await page.getByLabel('Performance HUD').innerText()
  const frame = hud.match(/frame p50\/p95 ([\d.]+)\/([\d.]+) ms/)
  expect(frame, hud).not.toBeNull()
  expect(Number(frame![2])).toBeGreaterThan(0)
  expect(errors).toEqual([])
  info.annotations.push({ type: 'map-soak', description: `${actions} pan/zoom cycles in 60 s; canvas ${size.width}×${size.height}; ${hud.replaceAll('\n', ', ')}` })
})
