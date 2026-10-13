import { beforeEach, describe, expect, it } from 'vitest'

import { recordPixiFrame, registerPixiContext, renderPerformanceSnapshot, resetRenderPerformanceMetricsForTests } from './renderPerformanceMetrics'

describe('render performance metrics', () => {
  beforeEach(() => {
    resetRenderPerformanceMetricsForTests()
  })

  it('tracks active Pixi contexts and rolling FPS', () => {
    const releaseA = registerPixiContext()
    const releaseB = registerPixiContext()
    recordPixiFrame(1000)
    recordPixiFrame(1050)
    recordPixiFrame(1100)

    expect(renderPerformanceSnapshot()).toMatchObject({
      activePixiContexts: 2,
      fps: 20,
    })

    releaseA()
    releaseB()

    expect(renderPerformanceSnapshot().activePixiContexts).toBe(0)
  })
})
