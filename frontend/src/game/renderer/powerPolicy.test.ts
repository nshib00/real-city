import { afterEach, describe, expect, it, vi } from 'vitest'
import { mapRenderBudget, observePageVisibility } from './powerPolicy'

afterEach(() => vi.restoreAllMocks())

describe('map power policy', () => {
  it('caps pixels and frames only in the laptop build', () => {
    expect(mapRenderBudget(true, 2)).toEqual({ maxFPS: 30, resolution: 1 })
    expect(mapRenderBudget(false, 2)).toEqual({ maxFPS: 60, resolution: 2 })
    expect(mapRenderBudget(true, NaN).resolution).toBe(1)
  })
  it('pauses a hidden page, resumes it and removes the listener', () => {
    const listener = vi.fn()
    const hidden = vi.spyOn(document, 'hidden', 'get').mockReturnValue(true)
    const stop = observePageVisibility(listener)
    expect(listener).toHaveBeenLastCalledWith(false)
    hidden.mockReturnValue(false)
    document.dispatchEvent(new Event('visibilitychange'))
    expect(listener).toHaveBeenLastCalledWith(true)
    stop()
    document.dispatchEvent(new Event('visibilitychange'))
    expect(listener).toHaveBeenCalledTimes(2)
  })
})
