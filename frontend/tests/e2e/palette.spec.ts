import { expect, test, type Page } from 'playwright/test'
import { mockInterfaceWorld } from './ui-fixture'
import { auditVisibleText } from './contrast-audit'
import { writeFileSync } from 'node:fs'

async function tokenPairs(page: Page) {
  return page.evaluate(() => {
    type RGB = [number, number, number, number]
    const root = getComputedStyle(document.documentElement)
    const get = (key: string): RGB => {
      const raw = root.getPropertyValue(key).trim()
      if (!raw) throw new Error(`Не определён ${key}`)
      const probe = document.createElement('span'); probe.style.color = raw; document.body.append(probe)
      const value = getComputedStyle(probe).color.match(/[\d.]+/g)!.map(Number); probe.remove()
      return [value[0], value[1], value[2], value[3] ?? 1]
    }
    const over = (fg: RGB, bg: RGB): RGB => [fg[0] * fg[3] + bg[0] * (1 - fg[3]), fg[1] * fg[3] + bg[1] * (1 - fg[3]), fg[2] * fg[3] + bg[2] * (1 - fg[3]), 1]
    const luma = (color: RGB) => color.slice(0, 3).map(value => value / 255).map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4).reduce((sum, value, i) => sum + value * [.2126, .7152, .0722][i], 0)
    const ratio = (a: RGB, b: RGB) => (Math.max(luma(a), luma(b)) + .05) / (Math.min(luma(a), luma(b)) + .05)
    return ['default', 'hover', 'pressed', 'disabled', 'loading', 'error', 'selected'].map(state => {
      const bg = get(`--control-${state}-bg`), fg = get(`--control-${state}-fg`), border = get(`--control-${state}-border`), icon = get(`--control-${state}-icon`), focus = get(`--control-${state}-focus`), outer = get('--control-focus-outer')
      const cases = ([0, 255] as const).map(value => {
        const background = over(bg, [value, value, value, 1])
        return { text: ratio(over(fg, background), background), border: ratio(over(border, background), background), icon: ratio(over(icon, background), background), focus: Math.max(ratio(over(focus, background), background), ratio(over(outer, background), background)) }
      })
      return { state, text: Math.min(...cases.map(row => row.text)), border: Math.min(...cases.map(row => row.border)), icon: Math.min(...cases.map(row => row.icon)), focus: Math.min(...cases.map(row => row.focus)) }
    })
  })
}

for (const terrain of ['grass', 'water', 'mountain', 'forest', 'ruins']) {
  test(`палитры над ${terrain}`, async ({ page }, info) => {
    const { errors, unknown } = await mockInterfaceWorld(page, { terrain, objects: true })
    await page.goto('/')
    await expect(page.locator('.pixi-stage canvas')).toBeVisible()
    await expect(page.getByLabel('Постройки: 2/8', { exact: true })).toBeVisible()
    await page.waitForFunction(async () => {
      const source = '/src/game/renderer/PixiStage.tsx'
      const { mapTextureReadiness } = await import(source)
      const counts = mapTextureReadiness.diagnostics()
      return counts.loaded > 0 && counts.loading === 0
    })
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
    const settings = page.locator('.interface-settings')
    if (await settings.getAttribute('open') === null) await settings.locator('summary').click()
    for (const theme of ['classic', 'aeolian']) {
      await page.getByRole('combobox', { name: 'Оформление', exact: true }).selectOption(theme)
      await expect(page.locator('html')).toHaveAttribute('data-interface-theme', theme)
      const tokens = await tokenPairs(page)
      writeFileSync(info.outputPath(`${theme}-tokens.json`), JSON.stringify(tokens, null, 2))
      expect(tokens.filter(row => row.text < 4.5 || row.border < 3 || row.icon < 3 || row.focus < 3)).toEqual([])
      // Сцена и данные одни и те же; освещение — диагностический фильтр только карты.
      for (const light of ['day', 'dark']) {
        await page.locator('.pixi-stage').evaluate((node, light) => { (node as HTMLElement).style.filter = light === 'dark' ? 'brightness(.4)' : 'none' }, light)
        await page.screenshot({ path: info.outputPath(`${theme}-${light}.png`), animations: 'disabled' })
        const audit = await auditVisibleText(page)
        writeFileSync(info.outputPath(`${theme}-${light}-contrast.json`), JSON.stringify(audit, null, 2))
        expect(audit.rows.filter(row => row.ratio < row.required)).toEqual([])
      }
      const fonts = await page.evaluate(() => ['--font-ui', '--font-display'].map(key => getComputedStyle(document.documentElement).getPropertyValue(key).trim()))
      expect(fonts).toEqual(Array(2).fill('"Trebuchet MS", "Segoe UI", ui-sans-serif, system-ui, sans-serif'))
    }
    expect(errors).toEqual([])
    expect([...new Set(unknown)]).toEqual([])
  })
}

test('состояния компонентов и 48 сочетаний владения/угрозы/выбора', async ({ page }, info) => {
  await page.goto('/design.html')
  const matrix = page.getByRole('region', { name: 'Матрица владения и состояния' })
  await expect(matrix.locator('article')).toHaveCount(48)
  for (const theme of ['classic', 'aeolian']) {
    await page.locator('html').evaluate((node, theme) => { node.dataset.interfaceTheme = theme }, theme)
    await matrix.screenshot({ path: info.outputPath(`${theme}-ownership.png`) })
    const paths = await matrix.locator('.ownership-review-light .ownership-sign path').evaluateAll(nodes => nodes.map(node => node.getAttribute('d')))
    expect(new Set(paths).size).toBe(4)
    const audit = await auditVisibleText(page)
    writeFileSync(info.outputPath(`${theme}-states-contrast.json`), JSON.stringify(audit, null, 2))
    expect(audit.rows.filter(row => row.ratio < row.required)).toEqual([])
    const button = page.getByRole('region', { name: 'Дизайн-система' }).getByRole('button', { name: /^Построить / }).first()
    for (const state of ['hover', 'pressed', 'focus']) {
      await button.hover()
      if (state === 'pressed') await page.mouse.down()
      if (state === 'focus') await button.focus()
      await button.screenshot({ path: info.outputPath(`${theme}-${state}.png`) })
      const audit = await auditVisibleText(page)
      expect(audit.rows.filter(row => row.ratio < row.required)).toEqual([])
      if (state === 'pressed') await page.mouse.up()
    }
  }
})
