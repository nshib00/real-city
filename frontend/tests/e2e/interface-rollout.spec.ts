import { expect, test } from 'playwright/test'
import { mockInterfaceWorld } from './ui-fixture'

test('смена темы сохраняет карту, выбор и черновик чата', async ({ page }, info) => {
  const { errors } = await mockInterfaceWorld(page)
  const mutations: string[] = []
  page.on('request', request => {
    if (request.method() !== 'GET' && !request.url().includes('/players/me/presence')) mutations.push(`${request.method()} ${new URL(request.url()).pathname}`)
  })
  await page.goto('/?perf=mixed&perfBuildings=24&perfMonsters=4&perfResources=8&perfTileRadius=12')
  const canvas = page.locator('.pixi-stage canvas')
  await expect(canvas).toBeVisible()
  await canvas.evaluate((node) => node.setAttribute('data-rollout-probe', 'retained'))
  await page.getByText('Выбрать клетку по координатам', { exact: true }).click()
  await page.getByLabel('X', { exact: true }).fill('12')
  await page.getByLabel('Y', { exact: true }).fill('14')
  await page.getByRole('button', { name: 'Осмотреть клетку', exact: true }).click()
  await expect(page.locator('#game-inspector')).toBeFocused()
  const selected = await page.locator('#game-inspector h2').textContent()
  const expand = page.getByRole('button', { name: 'Развернуть чат и события', exact: true })
  if (await expand.isVisible()) await expand.click()
  await page.getByRole('tab', { name: /^Чат/ }).click()
  await page.getByLabel('Сообщение в чат', { exact: true }).fill('Черновик без отправки')
  for (const theme of ['aeolian', 'classic']) {
    await page.getByLabel('Оформление', { exact: true }).selectOption(theme)
    await expect(page.locator('html')).toHaveAttribute('data-interface-theme', theme)
    await expect(canvas).toHaveAttribute('data-rollout-probe', 'retained')
    await expect(page.locator('#game-inspector h2')).toHaveText(selected ?? '')
    await expect(page.getByLabel('Сообщение в чат', { exact: true })).toHaveValue('Черновик без отправки')
    await page.screenshot({ path: info.outputPath(`${theme}.png`), animations: 'disabled' })
    await expect(page).toHaveScreenshot(`rollout-${theme}.png`, { animations: 'disabled', caret: 'hide' })
  }
  await page.getByRole('button', { name: 'Свернуть чат и события', exact: true }).click()
  await page.getByRole('button', { name: 'Развернуть чат и события', exact: true }).click()
  await expect(page.getByLabel('Сообщение в чат', { exact: true })).toHaveValue('Черновик без отправки')
  expect(errors).toEqual([])
  expect(mutations).toEqual([])
})
