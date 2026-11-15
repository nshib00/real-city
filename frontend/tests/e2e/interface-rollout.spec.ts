import { expect, test } from 'playwright/test'
import { mockInterfaceWorld } from './ui-fixture'

test('смена темы сохраняет карту, выбор и черновик чата', async ({ page }, info) => {
  const { errors } = await mockInterfaceWorld(page)
  const mutations: string[] = []
  page.on('request', request => {
    if (request.method() !== 'GET' && !request.url().includes('/players/me/presence')) mutations.push(`${request.method()} ${new URL(request.url()).pathname}`)
  })
  await page.goto('/?perf=mixed&perfBuildings=24&perfMonsters=4&perfResources=8&perfTileRadius=12')
  await expect(page.getByRole('main', { name: 'Загрузка игры' })).toHaveCount(0)
  const closeHelp = page.getByRole('button', { name: 'Закрыть помощь', exact: true })
  if (await closeHelp.isVisible()) await closeHelp.click()
  const canvas = page.locator('.pixi-stage canvas')
  await expect(canvas).toBeVisible()
  await page.addStyleTag({ content: '.map-performance-hud, .map-debug { display: none !important; }' })
  await canvas.evaluate((node) => node.setAttribute('data-rollout-probe', 'retained'))
  const canvasBox = await canvas.boundingBox()
  expect(canvasBox).not.toBeNull()
  await canvas.click({ position: { x: canvasBox!.width / 2, y: canvasBox!.height / 2 } })
  await expect(page.locator('#game-inspector h2')).toContainText('Клетка')
  const selected = await page.locator('#game-inspector h2').textContent()
  const expand = page.getByRole('button', { name: 'Развернуть чат и события', exact: true })
  if (await expand.isVisible()) {
    await expand.focus()
    await page.keyboard.press('Enter')
  }
  const eventsTab = page.getByRole('tab', { name: /^События/ })
  await eventsTab.focus()
  await page.keyboard.press('ArrowRight')
  await expect(page.getByRole('tab', { name: /^Чат/ })).toHaveAttribute('aria-selected', 'true')
  await page.getByLabel('Сообщение в чат', { exact: true }).fill('Черновик без отправки')
  const collapse = page.getByRole('button', { name: 'Свернуть чат и события', exact: true })
  await collapse.focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('button', { name: 'Развернуть чат и события', exact: true })).toBeVisible()
  const settings = page.locator('.interface-settings')
  if (!await settings.getAttribute('open').then(value => value !== null)) {
    await settings.locator('summary').focus()
    await page.keyboard.press('Enter')
    await expect(settings).toHaveAttribute('open', '')
    await settings.locator('summary').evaluate((node) => (node as HTMLElement).blur())
  }
  const feedbackBox = await page.locator('.action-feedback').boundingBox()
  const inspectorBox = await page.locator('#game-inspector').boundingBox()
  expect(feedbackBox).not.toBeNull()
  expect(inspectorBox).not.toBeNull()
  const overlaps = feedbackBox!.x < inspectorBox!.x + inspectorBox!.width
    && feedbackBox!.x + feedbackBox!.width > inspectorBox!.x
    && feedbackBox!.y < inspectorBox!.y + inspectorBox!.height
    && feedbackBox!.y + feedbackBox!.height > inspectorBox!.y
  expect(overlaps, `Настройки перекрывают инспектор в ${info.project.name}`).toBe(false)
  for (const theme of ['aeolian', 'classic']) {
    await page.getByRole('combobox', { name: 'Оформление', exact: true }).selectOption(theme)
    await expect(page.locator('html')).toHaveAttribute('data-interface-theme', theme)
    await expect(canvas).toHaveAttribute('data-rollout-probe', 'retained')
    await expect(page.locator('#game-inspector h2')).toHaveText(selected ?? '')
    await expect(page.getByLabel('Сообщение в чат', { exact: true })).toHaveValue('Черновик без отправки')
    await page.screenshot({ path: info.outputPath(`${theme}.png`), animations: 'disabled' })
    await expect(page).toHaveScreenshot(`rollout-${theme}.png`, { animations: 'disabled', caret: 'hide', maxDiffPixels: 600 })
  }
  const reopen = page.getByRole('button', { name: 'Развернуть чат и события', exact: true })
  await reopen.focus()
  await page.keyboard.press('Enter')
  await expect(page.getByLabel('Сообщение в чат', { exact: true })).toHaveValue('Черновик без отправки')
  expect(errors).toEqual([])
  expect(mutations).toEqual([])
})
