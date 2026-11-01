import { expect, test } from 'playwright/test'
import { mockInterfaceWorld } from './ui-fixture'
import { auditVisibleText } from './contrast-audit'
import { readFileSync, writeFileSync } from 'node:fs'

test('карта, панели, масштаб текста, эффекты и потерянные иконки', async ({ page }, info) => {
  const { errors, unknown } = await mockInterfaceWorld(page)
  const fontRequests: string[] = []
  page.on('request', request => { if (request.resourceType() === 'font') fontRequests.push(request.url()) })
  await page.goto('/?perf=mixed&perfBuildings=6&perfMonsters=0&perfResources=2&perfTileRadius=6')
  await page.addStyleTag({ content: '.map-performance-hud { display: none !important; }' })
  const canvas = page.locator('.pixi-stage canvas')
  await expect(canvas).toBeVisible()
  await expect(page.getByLabel('Ресурсы', { exact: true })).toContainText('123,5')
  // Снимок Chromium захватывает готовый кадр; чтение WebGL через drawImage между
  // кадрами даёт нули при preserveDrawingBuffer=false даже у видимой карты.
  expect((await canvas.screenshot({ path: info.outputPath('canvas.png') })).byteLength).toBeGreaterThan(10_000)
  const capture = async (name: string) => page.screenshot({ path: info.outputPath(`${name}.png`), animations: 'disabled' })
  const contrast = async (name: string) => {
    const path = info.outputPath(`contrast-${name}.json`)
    const audit = await auditVisibleText(page)
    writeFileSync(path, JSON.stringify(audit, null, 2))
    await info.attach(`contrast-${name}`, { path, contentType: 'application/json' })
    expect(audit.rows.filter(row => row.ratio < row.required), `Контраст: ${name}`).toEqual([])
  }
  await capture('world')
  await contrast('world')
  const viewport = page.viewportSize()!
  for (const selector of ['#game-tools', '#game-inspector', '.map-navigation']) {
    const box = (await page.locator(selector).boundingBox())!
    expect(box.x).toBeGreaterThanOrEqual(0)
    expect(box.y).toBeGreaterThanOrEqual(0)
    expect(box.x + box.width).toBeLessThanOrEqual(viewport.width + 1)
    expect(box.y + box.height).toBeLessThanOrEqual(viewport.height + 1)
  }
  // trial проверяет в том числе перекрытие кнопки другим элементом.
  await page.getByRole('button', { name: 'Увеличить карту', exact: true }).click()
  await page.getByRole('button', { name: 'Карта вправо', exact: true }).click()
  await page.getByRole('button', { name: 'Строить', exact: true }).click()
  const menu = page.getByLabel('Меню строительства', { exact: true })
  await expect(menu).toBeFocused()
  await capture('build-menu')
  await contrast('build-menu')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('button', { name: 'Строить', exact: true })).toBeFocused()

  await page.getByRole('button', { name: 'Реестр ресурсов', exact: true }).click()
  const registry = page.getByLabel('Реестр ресурсов', { exact: true }).filter({ has: page.locator('h2') })
  await expect(registry).toBeVisible()
  await capture('resource-registry')
  await contrast('resource-registry')
  const icon = registry.locator('.resource-icon').first()
  await icon.evaluate(node => { (node as HTMLElement).style.width = '16px'; (node as HTMLElement).style.height = '16px' })
  await expect(icon.locator('.resource-icon-render')).toBeVisible()
  await expect(icon.locator('.resource-icon-glyph')).toHaveCount(0)
  const before = await icon.boundingBox()
  await icon.locator('img').evaluate(node => { node.dispatchEvent(new Event('error')) })
  await expect(icon.locator('img')).toHaveCount(0)
  expect(await icon.boundingBox()).toEqual(before)
  await capture('resource-fallback')
  await registry.getByRole('button', { name: 'Редкие', exact: true }).click()
  expect(await registry.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true)
  await capture('resource-rare')
  await contrast('resource-rare')
  await page.keyboard.press('Escape')

  await page.emulateMedia({ reducedMotion: 'no-preference' })
  const settings = page.locator('.interface-settings')
  if (!await settings.getAttribute('open').then(value => value !== null)) await settings.locator('summary').click()
  await page.getByRole('button', { name: 'Эффекты: включены', exact: true }).click()
  await expect(page.locator('html')).toHaveAttribute('data-ui-effects', 'off')
  expect(await page.locator('#game-tools button').first().evaluate(node => getComputedStyle(node).transitionDuration)).toBe('0s')
  await page.emulateMedia({ reducedMotion: 'reduce' })

  await page.evaluate(() => { document.documentElement.style.fontSize = '200%' })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(viewport.width)
  await page.getByLabel('Открыть профиль игрока', { exact: true }).click()
  await expect(page.getByRole('dialog', { name: 'Профиль', exact: true })).toBeVisible()
  await capture('text-200-profile')
  await contrast('profile')
  expect(await page.getByRole('dialog', { name: 'Профиль', exact: true }).evaluate(node => getComputedStyle(node).fontFamily)).toContain('Trebuchet MS')
  expect(fontRequests).toEqual([])
  await page.keyboard.press('Escape')
  await page.evaluate(() => { document.documentElement.style.fontSize = '' })
  await page.getByRole('button', { name: 'Союз', exact: true }).click()
  const alliance = page.getByLabel('Союзный дом', { exact: true })
  await expect(alliance.getByLabel('Название союза')).toBeVisible()
  await capture('alliance-market')
  await contrast('alliance-market')
  await page.keyboard.press('Escape')
  // Уменьшение видимой области моделирует доступное браузеру изменение при клавиатуре.
  if (viewport.width <= 768) {
    await page.locator('.game-shell').evaluate(node => { (node as HTMLElement).style.setProperty('--safe-bottom', '34px'); (node as HTMLElement).style.setProperty('--safe-top', '24px') })
    if (viewport.width <= 760) {
      const tools = (await page.locator('#game-tools').boundingBox())!
      expect(tools.y + tools.height).toBeLessThanOrEqual(viewport.height - 34)
    }
    await page.setViewportSize({ width: viewport.width, height: 500 })
    await page.getByRole('button', { name: 'Строить', exact: true }).click()
    const box = (await menu.boundingBox())!
    expect(box.y + box.height).toBeLessThanOrEqual(500)
    await capture('keyboard-viewport')
    await page.keyboard.press('Escape')
  }
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
  expect(errors).toEqual([])
  expect([...new Set(unknown)]).toEqual([])
})

test('вход: шрифт, ошибка и сохранение введённых данных', async ({ page }, info) => {
  test.skip(!/^(320|390|1440)-dpr1$/.test(info.project.name), 'Проверка стартовой сцены на 320, 390 и 1440 px.')
  if (page.viewportSize()!.width === 320) await page.setViewportSize({ width: 320, height: 700 })
  else if (page.viewportSize()!.width === 390) await page.setViewportSize({ width: 390, height: 844 })
  await page.addInitScript(theme => localStorage.setItem('real-city.interface-theme', theme), process.env.REAL_CITY_REVIEW_THEME ?? 'classic')
  await page.route('**/ready', route => route.fulfill({ json: { status: 'ready' } }))
  await page.route('**/api/v1/auth/login', route => route.fulfill({ status: 401, json: { error: { kind: 'unauthorized', message: 'Проверьте почту и пароль.' } } }))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Эолия', exact: true })).toBeVisible()
  const scene = page.locator('.start-scene img')
  const emblem = page.locator('.start-brand img')
  await expect(scene).toBeVisible()
  await expect(emblem).toBeVisible()
  await expect(page.getByRole('status')).toHaveText('Мир доступен')
  expect(await scene.evaluate(node => (node as HTMLImageElement).naturalWidth)).toBeGreaterThan(0)
  expect(await emblem.evaluate(node => (node as HTMLImageElement).naturalWidth)).toBe(256)
  const sceneBox = await scene.boundingBox()
  expect(sceneBox).not.toBeNull()
  expect(sceneBox!.y).toBeGreaterThanOrEqual(0)
  expect(sceneBox!.y + sceneBox!.height).toBeLessThanOrEqual(page.viewportSize()!.height)
  await page.screenshot({ path: info.outputPath('start-page.png') })
  await expect(page.locator('.start-screen')).toHaveScreenshot('start-screen.png', { animations: 'disabled' })
  await expect(page.locator('link[rel="icon"][href="/favicon.ico"]')).toHaveCount(1)
  const favicon = await page.request.get(new URL('/favicon.ico', page.url()).toString())
  expect(favicon.ok()).toBe(true)
  await page.getByLabel('Email', { exact: true }).fill('review@example.invalid')
  await page.getByLabel('Пароль', { exact: true }).fill('review-password')
  await page.getByRole('button', { name: 'Войти', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Проверьте почту и пароль.')
  await expect(page.getByLabel('Email', { exact: true })).toHaveValue('review@example.invalid')
  await expect(page.getByLabel('Пароль', { exact: true })).toHaveValue('review-password')
  expect(await page.getByLabel('Аккаунт', { exact: true }).evaluate(node => getComputedStyle(node).fontFamily)).toContain('Trebuchet MS')
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
  await page.screenshot({ path: info.outputPath('auth-error.png') })
  if (page.viewportSize()!.width === 390) {
    const password = page.getByLabel('Пароль', { exact: true })
    await password.focus()
    await page.setViewportSize({ width: 390, height: 500 })
    await expect(password).toBeFocused()
    const box = await password.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.y + box!.height).toBeLessThanOrEqual(500)
  }
  const audit = await auditVisibleText(page)
  writeFileSync(info.outputPath('auth-contrast.json'), JSON.stringify(audit, null, 2))
  expect(audit.rows.filter(row => row.ratio < row.required)).toEqual([])
})

test('иконки, орнаменты и состояния при DPR 1/2 и масштабе 100/200%', async ({ page }, info) => {
  test.skip(!info.project.name.startsWith('1440'), 'Полный лист принимается на desktop при обоих DPR; мобильные потребители проверяются отдельно.')
  await page.goto('/design.html')
  const states = page.getByRole('region', { name: 'Дизайн-система' })
  await states.scrollIntoViewIfNeeded()
  await states.screenshot({ path: info.outputPath('states-light-dark.png'), animations: 'disabled' })
  const primary = states.getByRole('button', { name: /^Построить / }).first()
  await primary.hover()
  await primary.screenshot({ path: info.outputPath('button-hover.png') })
  await primary.focus()
  await primary.screenshot({ path: info.outputPath('button-focus.png') })
  await page.mouse.down()
  await primary.screenshot({ path: info.outputPath('button-pressed.png') })
  await page.mouse.up()
  const tooltipButton = states.getByRole('button', { name: 'Строительство', exact: true }).first()
  await tooltipButton.focus()
  await expect(states.getByRole('tooltip').first()).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(states.getByRole('tooltip').first()).toBeHidden()
  const opener = states.getByRole('button', { name: 'Открыть диалог' }).first()
  await opener.click()
  const dialog = page.getByRole('dialog', { name: 'Стоимость строительства' })
  await dialog.screenshot({ path: info.outputPath('ornament-craft.png') })
  await page.locator('html').evaluate(node => { node.dataset.uiEra = 'technology' })
  await dialog.screenshot({ path: info.outputPath('ornament-technology.png') })
  await page.keyboard.press('Escape')
  await expect(opener).toBeFocused()
  const html = readFileSync(new URL('../../../docs/assets/ui/review/icons/index.html', import.meta.url), 'utf8')
  await page.setContent(html)
  // Лист содержит настоящие исходники всех 55 знаков и 80 ресурсов.
  const iconCount = JSON.parse(readFileSync(new URL('../../public/assets/ui/icons/manifest.json', import.meta.url), 'utf8')).icons.length
  const resourceCount = JSON.parse(readFileSync(new URL('../../public/assets/ui/resources/manifest.json', import.meta.url), 'utf8')).resources.length
  await expect(page.locator('article')).toHaveCount((iconCount + resourceCount) * 3)
  for (const zoom of [1, 2]) {
    await page.locator('body').evaluate((node, zoom) => { node.style.zoom = String(zoom) }, zoom)
    for (const background of ['dark', 'light', 'gray']) {
      const section = page.locator(background === 'dark' ? 'section.dark:not(.gray)' : `section.${background}`)
      await section.screenshot({ path: info.outputPath(`icons-${background}-${zoom * 100}.png`) })
    }
  }
  await page.evaluate(() => {
    document.body.style.zoom = '1'
    const keys = new Set(['select', 'build', 'repair', 'attack', 'market', 'alliance', 'chat', 'wood', 'stone', 'coins', 'shield', 'offline'])
    const section = document.querySelector('section')!
    document.querySelectorAll('section').forEach(node => { if (node !== section) node.remove() })
    section.querySelectorAll('article').forEach(node => {
      const label = node.querySelector('b')!
      if (!keys.delete(label.textContent!)) node.remove()
      else label.style.display = 'none'
    })
  })
  await page.locator('section').screenshot({ path: info.outputPath('pilot-without-labels.png') })
  await page.locator('b').evaluateAll(nodes => nodes.forEach(node => { node.style.display = '' }))
  await page.locator('section').screenshot({ path: info.outputPath('pilot-with-labels.png') })
})

test('цветовые симуляции над миром и читаемые подписи', async ({ page }, info) => {
  const { errors } = await mockInterfaceWorld(page)
  await page.goto('/?perf=mixed&perfBuildings=6&perfMonsters=0&perfResources=2&perfTileRadius=6')
  await page.addStyleTag({ content: '.map-performance-hud { display: none !important; }' })
  await expect(page.locator('.pixi-stage canvas')).toBeVisible()
  // Матрицы полной дихромазии Machado et al.; только диагностическое представление.
  const matrices = {
    protanopia: '0.152286 1.052583 -0.204868 0 0 0.114503 0.786281 0.099216 0 0 -0.003882 -0.048116 1.051998 0 0 0 0 0 1 0',
    deuteranopia: '0.367322 0.860646 -0.227968 0 0 0.280085 0.672501 0.047413 0 0 -0.011820 0.042940 0.968881 0 0 0 0 0 1 0',
    tritanopia: '1.255528 -0.076749 -0.178779 0 0 -0.078411 0.930809 0.147602 0 0 0.004733 0.691367 0.303900 0 0 0 0 0 1 0',
  }
  for (const [name, matrix] of Object.entries(matrices)) {
    await page.evaluate(({ name, matrix }) => {
      document.getElementById('review-filter')?.remove()
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
      svg.id = 'review-filter'; svg.setAttribute('width', '0'); svg.setAttribute('height', '0')
      svg.innerHTML = `<filter id="${name}" color-interpolation-filters="linearRGB"><feColorMatrix type="matrix" values="${matrix}"/></filter>`
      document.body.append(svg)
      document.querySelector<HTMLElement>('.game-shell')!.style.filter = `url(#${name})`
    }, { name, matrix })
    await page.screenshot({ path: info.outputPath(`${name}.png`), animations: 'disabled' })
    await expect(page.getByRole('button', { name: 'Строить', exact: true })).toHaveAccessibleName('Строить')
  }
  expect(errors).toEqual([])
})

test('доступные имена, возврат фокуса и восстановление карты после перезагрузки', async ({ page }) => {
  const { errors, unknown } = await mockInterfaceWorld(page)
  await page.goto('/')
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()

  const unnamedControls = await page.locator('button:visible, input:visible, select:visible, textarea:visible').evaluateAll(nodes =>
    nodes.flatMap(node => {
      const element = node as HTMLButtonElement
      const name = [element.getAttribute('aria-label'), element.getAttribute('title'), element.getAttribute('alt'), element.labels ? [...element.labels].map(label => label.textContent).join(' ') : '', element.textContent]
        .filter(Boolean).join(' ').replace(/\s+/g, ' ').trim()
      return name ? [] : [`${element.tagName.toLowerCase()}.${element.className}`]
    }),
  )
  expect(unnamedControls).toEqual([])

  await page.locator('#game-tools').focus()
  await page.getByRole('button', { name: 'Строить', exact: true }).click()
  const menu = page.getByLabel('Меню строительства', { exact: true })
  await expect(menu).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('button', { name: 'Строить', exact: true })).toBeFocused()

  await page.getByLabel('Открыть профиль игрока', { exact: true }).click()
  const profile = page.getByRole('dialog', { name: 'Профиль', exact: true })
  await expect(profile).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByLabel('Открыть профиль игрока', { exact: true })).toBeFocused()

  await page.reload()
  await expect(page.getByLabel('Карта', { exact: true })).toBeVisible()
  await expect(page.locator('.pixi-stage canvas')).toBeVisible()
  expect(errors).toEqual([])
  expect(unknown).toEqual([])
})

test('профиль карты: загрузка, кадры, реакция на действие и перекрытие UI', async ({ page }, info) => {
  test.skip(info.project.name !== '1440-dpr1', 'Воспроизводимый профиль снимается на desktop 1440×900; мобильное устройство требует отдельного физического прогона.')
  const { errors, unknown } = await mockInterfaceWorld(page)
  const uiResponses: { url: string; bytes: number }[] = []
  page.on('response', async response => {
    const type = response.request().resourceType()
    if (!['stylesheet', 'font', 'image'].includes(type)) return
    try { uiResponses.push({ url: new URL(response.url()).pathname, bytes: (await response.body()).byteLength }) } catch {}
  })
  const startedAt = Date.now()
  await page.goto('/?perf=mixed&perfBuildings=100&perfMonsters=30&perfResources=50&perfTileRadius=16')
  await expect(page.locator('.pixi-stage canvas')).toBeVisible()
  await expect(page.locator('.map-performance-hud')).toContainText('mixed')
  const readyMs = Date.now() - startedAt
  const frameProfile = await page.evaluate(async () => {
    const frames: number[] = []
    let previous = performance.now()
    const endAt = previous + 5000
    await new Promise<void>(resolve => {
      const tick = (now: number) => {
        frames.push(now - previous)
        previous = now
        if (now >= endAt) resolve()
        else requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    })
    const sorted = [...frames].sort((a, b) => a - b)
    const percentile = (p: number) => sorted[Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * p))] ?? 0
    return { count: frames.length, fps: frames.length / 5, p50Ms: percentile(.5), p95Ms: percentile(.95) }
  })
  const coverage = await page.evaluate(() => {
    const map = document.querySelector<HTMLElement>('#game-map')!
    const bounds = map.getBoundingClientRect()
    const selector = '.resource-bar, #game-tools, #game-inspector, .event-log, .notification-stack, .map-navigation, .world-status, .placement-status, .first-city-help'
    const rects = [...document.querySelectorAll<HTMLElement>(selector)].filter(node => {
      const style = getComputedStyle(node), rect = node.getBoundingClientRect()
      return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0
    }).map(node => {
      const rect = node.getBoundingClientRect()
      return { x1: Math.max(bounds.left, rect.left), y1: Math.max(bounds.top, rect.top), x2: Math.min(bounds.right, rect.right), y2: Math.min(bounds.bottom, rect.bottom) }
    }).filter(rect => rect.x2 > rect.x1 && rect.y2 > rect.y1)
    const xs = [...new Set([bounds.left, bounds.right, ...rects.flatMap(rect => [rect.x1, rect.x2])])].sort((a, b) => a - b)
    let covered = 0
    for (let i = 0; i + 1 < xs.length; i++) {
      const left = xs[i], right = xs[i + 1], intervals = rects.filter(rect => rect.x1 < right && rect.x2 > left).map(rect => [rect.y1, rect.y2] as const).sort((a, b) => a[0] - b[0])
      let start = -1, end = -1, height = 0
      for (const [top, bottom] of intervals) {
        if (top > end) { height += Math.max(0, end - start); start = top; end = bottom }
        else end = Math.max(end, bottom)
      }
      height += Math.max(0, end - start)
      covered += (right - left) * height
    }
    return { mapAreaPx: bounds.width * bounds.height, coveredAreaPx: covered, coveredPercent: bounds.width * bounds.height ? covered / (bounds.width * bounds.height) * 100 : 0 }
  })
  const zoomButton = page.getByRole('button', { name: 'Увеличить карту', exact: true })
  const mapOrigin = page.locator('.map-origin')
  const beforeAction = await mapOrigin.getAttribute('style')
  await page.evaluate(() => {
    const target = document.querySelector<HTMLElement>('.map-origin')!
    const started = performance.now()
    const observer = new MutationObserver(() => {
      ;(window as Window & { __mapActionLatency?: number }).__mapActionLatency = performance.now() - started
      observer.disconnect()
    })
    observer.observe(target, { attributes: true, attributeFilter: ['style'] })
  })
  await zoomButton.click()
  await expect.poll(() => mapOrigin.getAttribute('style')).not.toBe(beforeAction)
  const actionMs = await page.evaluate(() => (window as Window & { __mapActionLatency?: number }).__mapActionLatency ?? null)
  const report = {
    environment: { viewport: page.viewportSize(), browser: info.project.name, syntheticScenario: 'mixed 100 buildings / 50 resources / 30 monsters / radius 16' },
    readyMs,
    cssUiImageBytes: uiResponses.reduce((sum, entry) => sum + entry.bytes, 0),
    cssUiImageRequests: uiResponses.length,
    frameProfile,
    actionResponseMs: actionMs,
    mapCoverage: coverage,
  }
  console.log(`browser-performance-profile ${JSON.stringify(report)}`)
  await info.attach('browser-performance-profile.json', { body: JSON.stringify(report, null, 2), contentType: 'application/json' })
  expect(actionMs).not.toBeNull()
  expect(coverage.coveredPercent).toBeLessThan(100)
  expect(errors).toEqual([])
  expect(unknown).toEqual([])
})
