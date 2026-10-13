import { describe, expect, it } from 'vitest'

import { animationFrameIndex, animationPhaseOffsetMs, shouldRenderBuildingOverlay } from './animationClock'

describe('object layer animation clock', () => {
  it('selects looped animation frames from fps and time', () => {
    expect(animationFrameIndex({ nowMs: 0, fps: 8, frames: 12, loop: true })).toBe(0)
    expect(animationFrameIndex({ nowMs: 125, fps: 8, frames: 12, loop: true })).toBe(1)
    expect(animationFrameIndex({ nowMs: 1500, fps: 8, frames: 12, loop: true })).toBe(0)
  })

  it('clamps non-looping animations on the last frame', () => {
    expect(animationFrameIndex({ nowMs: 10_000, fps: 8, frames: 4, loop: false })).toBe(3)
  })

  it('uses stable per-object phase offsets', () => {
    expect(animationPhaseOffsetMs('building-a')).toBe(animationPhaseOffsetMs('building-a'))
    expect(animationPhaseOffsetMs('building-a')).not.toBe(animationPhaseOffsetMs('building-b'))
  })

  it('keeps only important overlays at distant zoom unless selected', () => {
    expect(shouldRenderBuildingOverlay('working', 0.4)).toBe(false)
    expect(shouldRenderBuildingOverlay('damaged_smoke', 0.4)).toBe(true)
    expect(shouldRenderBuildingOverlay('working', 0.4, true)).toBe(true)
  })
})
