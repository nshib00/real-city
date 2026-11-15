import { beforeEach, describe, expect, it } from 'vitest'

import { recordPixiAnimation, recordPixiFrame, recordPixiRedraw, registerPixiContext, renderPerformanceSnapshot, resetRenderPerformanceMetricsForTests } from './renderPerformanceMetrics'

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

  it('tracks redraw phase percentiles, object counts, and animation costs', () => {
    registerPixiContext()
    recordPixiRedraw({
      visible: { tiles: 80, buildings: 24, resources: 6, monsters: 3 },
      pixiChildren: { terrain: 80, objects: 42 },
      retainedCaches: { terrain: 80, buildings: 24, resources: 6, overlays: 2 },
    }, { created: 0, destroyed: 0 }, {
      phases: { terrain: 2, mapOverlays: 1, commandBuild: 3, buildings: 4, resources: 1, monsters: 1, buildingOverlays: 2, total: 14 },
      objects: { buildings: 24, resources: 6, monsters: 3, buildingCommands: 24, resourceCommands: 6, overlayCommands: 2 },
    })
    recordPixiAnimation('monsters', 1.5, 3)
    recordPixiAnimation('buildingOverlays', 0.8, 2)

    const snapshot = renderPerformanceSnapshot()
    expect(snapshot.redraw).toMatchObject({
      samples10s: 1,
      phases: { total: { p50Ms: 14, p95Ms: 14 }, commandBuild: { p50Ms: 3, p95Ms: 3 } },
      objects: { buildings: 24, resources: 6, monsters: 3, overlayCommands: 2 },
    })
    expect(snapshot.animation).toMatchObject({
      monsters: { samples10s: 1, p50Ms: 1.5, p95Ms: 1.5, items: 3 },
      buildingOverlays: { samples10s: 1, p50Ms: 0.8, p95Ms: 0.8, items: 2 },
    })
  })
})
