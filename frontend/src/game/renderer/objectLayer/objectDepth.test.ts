import { describe, expect, it } from 'vitest'

import { gridToScreen, nearestWrappedScreenCoord } from '../../coordinates/iso'
import { objectLayerSortKey, projectedObjectSortKey } from './objectDepth'

describe('object layer depth', () => {
  it('sorts isometric objects by their base tile diagonal', () => {
    expect(objectLayerSortKey({ x: 5, y: 5 })).toBeGreaterThan(objectLayerSortKey({ x: 4, y: 4 }))
    expect(objectLayerSortKey({ x: 5, y: 4 })).toBeGreaterThan(objectLayerSortKey({ x: 4, y: 5 }))
    expect(objectLayerSortKey({ x: 0, y: 6 })).toBeGreaterThan(objectLayerSortKey({ x: 159, y: -154 }))
  })

  it('keeps layer and footprint offsets centralized', () => {
    expect(objectLayerSortKey({ x: 2, y: 3 }, 20, 4)).toBe(objectLayerSortKey({ x: 2, y: 3 }) + 24)
  })

  it('sorts wrapped objects by their visible position instead of their raw map coordinate', () => {
    const screenTarget = gridToScreen({ x: 0, y: 0 })
    const behind = nearestWrappedScreenCoord({ x: 159, y: 0 }, screenTarget)
    const inFront = nearestWrappedScreenCoord({ x: 0, y: 1 }, screenTarget)

    expect(objectLayerSortKey({ x: 159, y: 0 })).toBeGreaterThan(objectLayerSortKey({ x: 0, y: 1 }))
    expect(projectedObjectSortKey(behind)).toBeLessThan(projectedObjectSortKey(inFront))
    expect(projectedObjectSortKey(behind, 0.5)).toBe(projectedObjectSortKey(behind) + 0.5)

    const left = nearestWrappedScreenCoord({ x: 159, y: 1 }, screenTarget)
    const right = nearestWrappedScreenCoord({ x: 0, y: 0 }, screenTarget)
    expect(left.y).toBe(right.y)
    expect(projectedObjectSortKey(left)).toBeLessThan(projectedObjectSortKey(right))
  })
})
