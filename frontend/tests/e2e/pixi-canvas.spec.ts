import { expect, test } from '@playwright/test'

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

  test('renders a nonblank Pixi canvas under object load', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/?perf=mixed&perfBuildings=260&perfMonsters=80&perfResources=40&perfTileRadius=18')

    const canvas = page.locator('.pixi-stage canvas')
    await expect(canvas).toBeVisible()
    await expect(page.getByLabel('Performance HUD')).toContainText('mixed')

    await expect.poll(async () => {
      return canvas.evaluate((node) => {
        const source = node as HTMLCanvasElement
        const probe = document.createElement('canvas')
        probe.width = Math.min(96, source.width)
        probe.height = Math.min(96, source.height)
        const context = probe.getContext('2d')
        if (!context || probe.width === 0 || probe.height === 0) {
          return 0
        }
        context.drawImage(source, 0, 0, probe.width, probe.height)
        const pixels = context.getImageData(0, 0, probe.width, probe.height).data
        let nonblank = 0
        for (let index = 0; index < pixels.length; index += 4) {
          if (pixels[index + 3] > 0) {
            nonblank += 1
          }
        }
        return nonblank
      })
    }).toBeGreaterThan(0)
  })
})
