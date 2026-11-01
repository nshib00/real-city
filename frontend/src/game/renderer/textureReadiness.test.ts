import { expect, it, vi } from 'vitest'
import { TextureReadiness } from './textureReadiness'

it('ограничивает повторы, восстанавливает текстуру и разделяет версии', async () => {
  let now = 0
  const load = vi.fn().mockRejectedValue(new Error('offline'))
  const redraw = vi.fn()
  const failed = vi.fn()
  const cache = new TextureReadiness(load, failed, () => now)
  for (let attempt = 0; attempt < 3; attempt++) {
    expect(cache.ready('/sprite.png?v=1', redraw)).toBe(false)
    expect(cache.ready('/sprite.png?v=1', redraw)).toBe(false)
    await Promise.resolve()
    now += 4000
  }
  for (let i = 0; i < 10; i++) cache.ready('/sprite.png?v=1', redraw)
  expect(load).toHaveBeenCalledTimes(3)
  expect(cache.diagnostics().retryable).toBe(0)
  cache.retryFailed()
  load.mockResolvedValue({})
  cache.ready('/sprite.png?v=1', redraw)
  await Promise.resolve()
  expect(cache.ready('/sprite.png?v=1', redraw)).toBe(true)
  expect(cache.ready('/sprite.png?v=2', redraw)).toBe(false)
  await Promise.resolve()
  expect(cache.diagnostics()).toMatchObject({ loaded: 2, loading: 0, failed: 0 })
  expect(failed).toHaveBeenCalledTimes(3)
})

it('уведомляет новую сцену при совместной загрузке и не опрашивает старые ошибки бесконечно', async () => {
  let complete!: (value: unknown) => void
  let now = 0
  const load = vi.fn(() => new Promise((resolve) => { complete = resolve }))
  const first = vi.fn(), next = vi.fn()
  const cache = new TextureReadiness(load, vi.fn(), () => now)
  cache.ready('/shared.png', first)
  cache.ready('/shared.png', next)
  complete({})
  await Promise.resolve()
  expect(first).toHaveBeenCalledTimes(1)
  expect(next).toHaveBeenCalledTimes(1)
  const failed = new TextureReadiness(() => Promise.reject(new Error()), vi.fn(), () => now)
  failed.ready('/old.png', next)
  await Promise.resolve()
  now = 6000
  expect(failed.diagnostics().retryable).toBe(0)
})
