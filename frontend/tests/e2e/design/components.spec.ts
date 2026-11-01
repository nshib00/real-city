import { expect, test } from 'playwright/test'

test('стенд: DOM, клик, размеры, исходный шрифт и снимок', async ({ page }, info) => {
  await page.clock.install({ time: new Date('2026-10-30T12:00:00Z') })
  await page.goto('/design.html')
  await expect(page.getByRole('heading', { name: 'Эолия: исходные компоненты' })).toBeVisible()
  await page.getByLabel('Инструменты', { exact: true }).getByRole('button', { name: 'Строительство', exact: true }).click()
  await expect(page.getByLabel('Инструменты').getByRole('status')).toHaveText('Режим: build')
  await expect(page.getByRole('button', { name: 'Атака недоступна' })).toBeDisabled()
  await page.getByRole('button', { name: 'Повторить' }).click()
  await expect(page.getByText('Повтор запрошен')).toBeVisible()
  const fonts = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement)
    return ['--font-ui', '--font-display'].map(key => style.getPropertyValue(key).trim())
  })
  expect(fonts).toEqual(Array(2).fill('"Trebuchet MS", "Segoe UI", ui-sans-serif, system-ui, sans-serif'))
  await page.evaluate(() => document.fonts.ready)
  await page.screenshot({ path: info.outputPath('components.png'), fullPage: true, animations: 'disabled' })
  // Отдельно проверяем изменение viewport внутри уже открытой страницы.
  await page.setViewportSize({ width: 320, height: 700 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320)
})
