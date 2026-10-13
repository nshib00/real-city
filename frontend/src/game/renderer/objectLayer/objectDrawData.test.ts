import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../../state/useGameStore'
import { buildingDrawCommands, canDrawBuildingInObjectLayer } from './objectDrawData'

describe('object draw data', () => {
  it('turns visible buildings into sorted Pixi draw commands', () => {
    const commands = buildingDrawCommands([
      building({ id: 'b', tile: { x: 5, y: 5 } }),
      building({ id: 'a', tile: { x: 1, y: 1 } }),
    ])

    expect(commands.map((command) => command.id)).toEqual(['a', 'b'])
    expect(commands[0]).toMatchObject({
      textureUrl: '/assets/buildings/center/town_hall/town_hall_l01_active.png',
      anchor: { x: 0.5 },
      size: { width: 512, height: 384 },
    })
  })

  it('uses shape-aware sprite lookup for roads and walls', () => {
    const road = building({ id: 'road-1', kind: 'standard_road', tile: { x: 0, y: 0 } })
    const neighbor = building({ id: 'road-2', kind: 'standard_road', tile: { x: 1, y: 0 } })

    expect(buildingDrawCommands([road], { allBuildings: [road, neighbor] })[0].textureUrl).toBe(
      '/assets/buildings/roads/common_road/common_road_end_e_active.png',
    )
  })

  it('marks the selected building for Pixi styling', () => {
    expect(buildingDrawCommands([building({ id: 'selected' })], { selectedBuildingId: 'selected' })[0].selected).toBe(true)
  })

  it('keeps unsupported building kinds in Pixi with procedural fallback', () => {
    const [command] = buildingDrawCommands([building({ kind: 'warehouse' })])

    expect(command.textureUrl).toBeNull()
    expect(canDrawBuildingInObjectLayer(building({ kind: 'warehouse' }))).toBe(true)
    expect(canDrawBuildingInObjectLayer(building({ kind: 'coin_storage' }))).toBe(true)
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
