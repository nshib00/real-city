import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import { buildingOverlayKeys, buildingVisualState } from './buildingAnimationRegistry'

describe('building animation registry', () => {
  it('maps active buildings with animation metadata to working overlays', () => {
    const visualState = buildingVisualState(building({ kind: 'lumber_yard', level: 3 }))

    expect(visualState.baseState).toBe('active')
    expect(visualState.overlays.map((overlay) => overlay.key)).toEqual(['working'])
    expect(visualState.overlays[0]?.animation).toMatchObject({ type: 'overlay', fps: 8, loop: true })
  })

  it('exposes visual overlay intents even before an asset provides metadata', () => {
    expect(buildingOverlayKeys(building({ kind: 'mine', status: 'construction', state: 'building' }))).toContain('construction_dust')
    expect(buildingVisualState(building({ kind: 'mine', status: 'construction', state: 'building' })).overlays).toEqual([])
  })

  it('uses damaged smoke metadata when a building falls below critical health', () => {
    const visualState = buildingVisualState(building({ kind: 'lumber_yard', health: 20, maxHealth: 100 }))

    expect(visualState.baseState).toBe('damaged')
    expect(visualState.overlays.map((overlay) => overlay.key)).toEqual(['damaged_smoke'])
    expect(visualState.overlays[0]?.animation).toMatchObject({ type: 'shared_overlay', id: 'smoke_small' })
  })
})

function building(overrides: Partial<PlacedBuilding>): PlacedBuilding {
  return {
    id: 'building-1',
    kind: 'town_hall',
    name: 'Постройка',
    level: 1,
    tile: { x: 0, y: 0 },
    owner: 'test',
    status: 'active',
    state: 'active',
    health: 100,
    maxHealth: 100,
    startedAt: 0,
    completesAt: null,
    ...overrides,
  }
}
