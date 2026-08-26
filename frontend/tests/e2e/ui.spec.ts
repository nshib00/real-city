import { expect, test } from '@playwright/test'

test.describe('strategy interface smoke', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('real-city.access-token', 'e2e-access')
      localStorage.setItem('real-city.refresh-token', 'e2e-refresh')
    })
    await page.route('/api/v1/players/me', async (route) => {
      await route.fulfill({
        json: {
          id: 'player_e2e',
          email: 'e2e@example.com',
          name: 'E2E City',
          status: 'active',
          role: 'user',
          profile: {
            display_name: 'E2E City',
            avatar_url: '',
            settings: {
              notifications: { raid_alerts: true, production_ready: true, market_updates: false },
              render_quality: 'medium',
            },
            updated_at: '2026-08-25T00:00:00Z',
          },
          created_at: '2026-08-25T00:00:00Z',
          updated_at: '2026-08-25T00:00:00Z',
        },
      })
    })
    await page.route('/api/v1/world/chunks?**', async (route) => {
      await route.fulfill({
        json: {
          chunks: [
            {
              map_id: 'world_e2e',
              chunk_x: 0,
              chunk_y: 0,
              version: 1,
              tiles: [
                { x: 0, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'grass', elevation: 4, safe_zone: true },
                { x: 1, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 5, safe_zone: false },
                { x: 0, y: 1, chunk_x: 0, chunk_y: 0, terrain: 'mountain', elevation: 8, safe_zone: false },
              ],
            },
          ],
        },
      })
    })
  })

  test('renders map and panels on desktop', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByLabel('Карта')).toBeVisible()
    await expect(page.getByLabel('Ресурсы')).toContainText('Монеты')
    await expect(page.getByLabel('Инструменты')).toBeVisible()
    await expect(page.getByLabel('Инспектор')).toBeVisible()
  })

  test('keeps core controls reachable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    await expect(page.getByLabel('Карта')).toBeVisible()
    await expect(page.getByLabel('Ресурсы')).toBeVisible()
    await expect(page.getByLabel('Инструменты')).toBeVisible()
  })
})
