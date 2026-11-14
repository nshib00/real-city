import { expect, test } from 'playwright/test'

test.describe('Pixi object layer smoke', () => {
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
            updated_at: '2026-10-12T00:00:00Z',
          },
          created_at: '2026-10-12T00:00:00Z',
          updated_at: '2026-10-12T00:00:00Z',
        },
      })
    })
    await page.route('/api/v1/world/chunks?**', async (route) => {
      await route.fulfill({ json: { chunks: [] } })
    })
    await page.route('/api/v1/production/recipes', async (route) => {
      await route.fulfill({ json: { recipes: [] } })
    })
    await page.route('/api/v1/production/jobs', async (route) => {
      await route.fulfill({ json: { jobs: [] } })
    })
  })

  test('renders the Pixi canvas and loads the synthetic object scene', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/?perf=mixed&perfBuildings=24&perfMonsters=8&perfResources=6&perfTileRadius=8')

    const canvas = page.locator('.pixi-stage canvas')
    await expect(canvas).toBeVisible()
    await expect(page.getByLabel('Performance HUD')).toContainText('mixed')

    await expect.poll(() => canvas.evaluate((node) => {
      const { width, height } = node as HTMLCanvasElement
      return width > 0 && height > 0
    })).toBe(true)
    await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
  })
})
