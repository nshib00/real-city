import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../../state/useGameStore'
import { buildingDrawCommands } from './objectDrawData'
import { buildingOverlayDrawCommands } from './buildingOverlayDrawData'

describe('building overlay draw data', () => {
  it('creates manifest-backed working overlays with deterministic frame indexes', () => {
    const [command] = buildingDrawCommands([building({ id: 'yard-1', kind: 'lumber_yard' })])
    const overlays = buildingOverlayDrawCommands([command], { zoom: 1, nowMs: 1000 })

    expect(overlays).toHaveLength(1)
    expect(overlays[0]).toMatchObject({
      id: 'yard-1:working',
      buildingId: 'yard-1',
      key: 'working',
      animation: { type: 'overlay', fps: 8, frames: 12, loop: true },
    })
  })

  it('uses shared overlays for construction, damage and ready states', () => {
    const commands = buildingDrawCommands([
      building({ id: 'mine-1', kind: 'mine', status: 'construction', state: 'building' }),
      building({ id: 'mine-2', kind: 'mine', health: 12, maxHealth: 100 }),
      building({ id: 'field-1', kind: 'field_bed', fieldStageReady: true }),
    ])
    const keys = buildingOverlayDrawCommands(commands, { zoom: 1, nowMs: 0 }).map((overlay) => overlay.key).sort()

    expect(keys).toEqual(['construction_dust', 'damaged_smoke', 'ready_to_collect'].sort())
  })

  it('adds fire for nearly destroyed buildings', () => {
    const [command] = buildingDrawCommands([building({ id: 'mine-1', kind: 'mine', health: 10, maxHealth: 100 })])

    expect(buildingOverlayDrawCommands([command], { zoom: 1, nowMs: 0 }).map((overlay) => overlay.key).sort()).toEqual([
      'damaged_fire',
      'damaged_smoke',
    ])
  })

  it('does not add default working overlays to every active building', () => {
    const [command] = buildingDrawCommands([building({ kind: 'mine' })])

    expect(buildingOverlayDrawCommands([command], { zoom: 1, nowMs: 0 })).toEqual([])
  })

  it('filters low-priority overlays at far zoom', () => {
    const [working] = buildingDrawCommands([building({ id: 'yard-1', kind: 'lumber_yard' })])
    const [damaged] = buildingDrawCommands([building({ id: 'yard-2', kind: 'lumber_yard', health: 12, maxHealth: 100 })])

    expect(buildingOverlayDrawCommands([working], { zoom: 0.4, nowMs: 0 })).toEqual([])
    expect(buildingOverlayDrawCommands([damaged], { zoom: 0.4, nowMs: 0 }).map((overlay) => overlay.key)).toEqual(['damaged_smoke'])
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
