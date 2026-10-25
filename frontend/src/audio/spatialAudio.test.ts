import { describe, expect, it } from 'vitest'
import { spatialSound } from './spatialAudio'

describe('пространственный звук', () => {
  it('учитывает панораму, расстояние и циклическую карту', () => {
    expect(spatialSound({ x: 0, y: 0 }, { x: 0, y: 0 }, 1)).toEqual({ gain: 1, pan: 0 })
    expect(spatialSound({ x: 10, y: 0 }, { x: 0, y: 0 }, 1).pan).toBeGreaterThan(0)
    expect(spatialSound({ x: 0, y: 10 }, { x: 0, y: 0 }, 1).pan).toBeLessThan(0)
    expect(spatialSound({ x: 80, y: 0 }, { x: 0, y: 0 }, 1).gain).toBe(0)
    expect(spatialSound({ x: 159, y: 0 }, { x: 0, y: 0 }, 1).gain).toBeGreaterThan(0)
  })
})
