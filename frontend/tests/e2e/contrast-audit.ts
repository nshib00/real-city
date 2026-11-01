import type { Page } from 'playwright/test'

export async function auditVisibleText(page: Page) {
  return page.evaluate(() => {
    type Color = [number, number, number, number]
    const color = (value: string): Color => {
      const values = value.match(/[\d.]+/g)?.map(Number) ?? [0, 0, 0]
      return [values[0], values[1], values[2], values[3] ?? 1]
    }
    const over = (fg: Color, bg: Color): Color => {
      const alpha = fg[3] + bg[3] * (1 - fg[3])
      return [0, 1, 2].map(i => alpha ? (fg[i] * fg[3] + bg[i] * bg[3] * (1 - fg[3])) / alpha : 0).concat(alpha) as Color
    }
    const luminance = (rgb: Color) => rgb.slice(0, 3).map(v => {
      const n = v / 255; return n <= .04045 ? n / 12.92 : ((n + .055) / 1.055) ** 2.4
    }).reduce((sum, n, i) => sum + n * [.2126, .7152, .0722][i], 0)
    const rows = []
    for (const node of document.querySelectorAll<HTMLElement>('.game-shell *, .component-states *, .ownership-review *, .auth-screen *')) {
      const text = [...node.childNodes].filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent).join('').trim()
      if (!text || node.closest('[aria-hidden="true"], [inert], [hidden], button:disabled') || !node.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) continue
      const rect = node.getBoundingClientRect()
      if (rect.right <= 0 || rect.left >= innerWidth || rect.bottom <= 0 || rect.top >= innerHeight || !rect.width || !rect.height) continue
      if (getComputedStyle(node).clipPath !== 'none') continue
      const style = getComputedStyle(node)
      const chain: HTMLElement[] = []; let parent: HTMLElement | null = node
      while (parent) {
        chain.unshift(parent)
        if (parent.classList.contains('game-shell')) break
        parent = parent.parentElement
      }
      const ratios = ([0, 255] as const).map(base => {
        let bg: Color = [base, base, base, 1]
        for (const layer of chain) bg = over(color(getComputedStyle(layer).backgroundColor), bg)
        const fg = over(color(style.color), bg)
        return (Math.max(luminance(fg), luminance(bg)) + .05) / (Math.min(luminance(fg), luminance(bg)) + .05)
      })
      const required = parseFloat(style.fontSize) >= 24 || (parseFloat(style.fontSize) >= 18.66 && Number(style.fontWeight) >= 700) ? 3 : 4.5
      rows.push({ text: text.slice(0, 100), selector: node.className, ratio: Number(Math.min(...ratios).toFixed(2)), required })
    }
    return { scope: 'Видимый текст, сплошные CSS-фоны с alpha; худшая подложка чёрная/белая. Градиенты, изображения, общий opacity и нетекстовые границы требуют визуального ревью.', rows }
  })
}
