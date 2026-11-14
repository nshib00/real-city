import { expect, test } from 'playwright/test'
import { mockInterfaceWorld } from './ui-fixture'

test.describe('strategy interface smoke', () => {
  test.beforeEach(async ({ page }) => {
    await mockInterfaceWorld(page)
  })

  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    test(`keeps profile and chat usable at ${viewport.width}x${viewport.height}`, async ({ page }) => {
      await page.setViewportSize(viewport)
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.clock.setFixedTime(new Date('2026-10-30T12:00:00Z'))
      await page.route('/api/v1/chat/messages?**', route => route.fulfill({ json: {
        messages: [], read_state: { read_at: '2026-10-30T12:00:00Z', unread: 0 },
      } }))
      await page.goto('/')
      await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
      await page.getByLabel('Открыть профиль игрока').click()
      const profile = page.getByRole('dialog', { name: 'Профиль', exact: true })
      await expect(profile).toBeVisible()
      await expect(profile.getByLabel('Показатели профиля')).toHaveCount(0)
      const box = await profile.boundingBox()
      expect(box).not.toBeNull()
      expect(box!.x).toBeGreaterThanOrEqual(0)
      expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width)
      await page.keyboard.press('Escape')
      await expect(profile).not.toBeVisible()
      const expand = page.getByLabel('Развернуть чат и события')
      if (await expand.isVisible()) await expand.click()
      const chatTab = page.getByRole('tab', { name: 'Чат', exact: true })
      await chatTab.focus()
      await page.keyboard.press('Enter')
      await expect(page.getByLabel('Сообщение в чат')).toBeVisible()
    })
  }

  test('renders map and panels on desktop', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
    await expect(page.getByLabel(/^Монеты:/)).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Инструменты' })).toBeVisible()
    await expect(page.getByRole('complementary', { name: 'Инспектор' })).toBeVisible()
  })

  test('keeps core controls reachable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
    await expect(page.getByLabel('Ресурсы')).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Инструменты' })).toBeVisible()
  })

  test('navigates regions, expands inspector and keeps controls within the viewport', async ({ page }) => {
    await page.goto('/')
    const map = page.locator('#game-map')
    await expect(map).toBeVisible()
    await expect.poll(() => page.locator('html').evaluate(node => getComputedStyle(node).getPropertyValue('--visible-height'))).not.toBe('')
    const navigationHandled = await page.evaluate(() => {
      const event = new KeyboardEvent('keydown', { key: 'F6', bubbles: true, cancelable: true })
      window.dispatchEvent(event)
      return event.defaultPrevented
    })
    expect(navigationHandled).toBe(true)
    const disclosure = page.getByRole('button', { name: 'Развернуть инспектор' })
    if (await disclosure.isVisible()) {
      await disclosure.click()
      await expect(page.getByRole('button', { name: 'Свернуть инспектор' })).toHaveAttribute('aria-expanded', 'true')
      await page.keyboard.press('Escape')
      await expect(page.getByRole('button', { name: 'Развернуть инспектор' })).toHaveAttribute('aria-expanded', 'false')
    }
    const viewport = page.viewportSize()!
    for (const id of ['game-tools', 'game-inspector']) {
      const box = await page.locator(`#${id}`).boundingBox()
      expect(box).not.toBeNull()
      expect(box!.x).toBeGreaterThanOrEqual(0)
      expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width)
      expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height)
    }
    await expect(page.getByRole('button', { name: 'Увеличить карту' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Карта вправо', exact: true })).toBeVisible()
  })
})
