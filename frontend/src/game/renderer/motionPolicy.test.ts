import { afterEach, expect, it, vi } from 'vitest'
import { observeWorldMotion, worldMotionEnabled } from './motionPolicy'
afterEach(() => { delete document.documentElement.dataset.uiEffects; vi.unstubAllGlobals() })
it('любой запрет движения имеет приоритет над включёнными эффектами', () => {
  vi.stubGlobal('matchMedia', () => ({ matches: true }))
  document.documentElement.dataset.uiEffects = 'on'
  expect(worldMotionEnabled()).toBe(false)
  vi.stubGlobal('matchMedia', () => ({ matches: false }))
  expect(worldMotionEnabled()).toBe(true)
  document.documentElement.dataset.uiEffects = 'off'
  expect(worldMotionEnabled()).toBe(false)
})
it('наблюдает только атрибут настройки и освобождает слушателей', async () => {
  const removeEventListener = vi.fn(), addEventListener = vi.fn()
  vi.stubGlobal('matchMedia', () => ({ matches: false, removeEventListener, addEventListener }))
  const changed = vi.fn(), stop = observeWorldMotion(changed)
  document.documentElement.dataset.uiEffects = 'off'
  await Promise.resolve()
  expect(changed).toHaveBeenCalledTimes(1)
  stop()
  document.documentElement.dataset.uiEffects = 'on'
  await Promise.resolve()
  expect(changed).toHaveBeenCalledTimes(1)
  expect(removeEventListener).toHaveBeenCalledWith('change', changed)
})
