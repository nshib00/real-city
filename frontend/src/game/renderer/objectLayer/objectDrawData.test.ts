import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../../state/useGameStore'
import { resolveBuildingModelAsset } from '../../renderers/buildingRegistry'
import { OIL_WELL_ASSET_REVISION } from '../../renderers/buildingAssetManifests'
import { buildingDrawCommands, canDrawBuildingInObjectLayer } from './objectDrawData'

describe('object draw data', () => {
  it('turns visible buildings into sorted Pixi draw commands', () => {
    const commands = buildingDrawCommands([
      building({ id: 'b', tile: { x: 5, y: 5 } }),
      building({ id: 'a', tile: { x: 1, y: 1 } }),
    ])

    expect(commands.map((command) => command.id)).toEqual(['a', 'b'])
    expect(commands[0]).toMatchObject({
      textureUrl: '/assets/buildings/center/town_hall/town_hall_l01_active.png?v=town-hall-vertical-2026-10-26',
      anchor: { x: 0.5 },
      size: { width: 512, height: 384 },
    })
  })

  it('uses shape-aware sprite lookup for roads and walls', () => {
    const road = building({ id: 'road-1', kind: 'standard_road', tile: { x: 0, y: 0 } })
    const neighbor = building({ id: 'road-2', kind: 'standard_road', tile: { x: 1, y: 0 } })

    expect(buildingDrawCommands([road], { allBuildings: [road, neighbor] })[0]).toMatchObject({
      textureUrl: '/assets/buildings/roads/common_road/common_road_end_e_active.png?v=road-kits-v2-2026-11-02',
      anchor: { x: 0.5, y: 0.625 },
      size: { width: 256, height: 256 },
    })
  })

  it('draws wooden walls as single-tile isometric sprites', () => {
    const wall = building({ id: 'wall-1', kind: 'wooden_wall', tile: { x: 0, y: 0 } })
    const neighbor = building({ id: 'wall-2', kind: 'wooden_wall', tile: { x: 1, y: 0 } })

    expect(buildingDrawCommands([wall], { allBuildings: [wall, neighbor] })[0]).toMatchObject({
      textureUrl: '/assets/buildings/roads/wooden_wall/wooden_wall_l01_end_e_active.png',
      anchor: { x: 0.5, y: 0.625 },
      size: { width: 256, height: 256 },
    })
  })

  it('renders oversized mine sprites at the same map footprint as other buildings', () => {
    for (const kind of ['mine', 'copper_mine'] as const) {
      const [command] = buildingDrawCommands([building({ kind })])

      expect(command).toMatchObject({
        anchor: { x: 0.5, y: 0.625 },
        size: { width: 512 * 0.58, height: 512 * 0.58 },
      })
    }
  })

  it('draws every oil well level and state with the matching runtime assets', () => {
    for (const level of [1, 2, 3]) {
      for (const state of ['active', 'construction', 'damaged', 'ruined'] as const) {
        const well = building({
          kind: 'oil_well',
          level,
          status: state === 'construction' ? 'construction' : 'active',
          state: state === 'construction' ? 'building' : state,
          health: state === 'ruined' ? 0 : state === 'damaged' ? 70 : 100,
        })
        const [command] = buildingDrawCommands([well])
        const base = `/assets/buildings/industry/oil_well/oil_well_l${String(level).padStart(2, '0')}_${state}`
        expect(command).toMatchObject({
          textureUrl: `${base}.png?v=${OIL_WELL_ASSET_REVISION}`,
          anchor: { x: 0.5, y: 292 / 384 },
          size: { width: 512, height: 384 },
        })
        expect(resolveBuildingModelAsset(well)).toBe(`${base}.glb?v=${OIL_WELL_ASSET_REVISION}`)
      }
    }
  })

  it('marks the selected building for Pixi styling', () => {
    expect(buildingDrawCommands([building({ id: 'selected' })], { selectedBuildingId: 'selected' })[0].selected).toBe(true)
  })

  it('keeps unsupported building kinds in Pixi with procedural fallback', () => {
    const [command] = buildingDrawCommands([building({ kind: 'mint' })])

    expect(command.textureUrl).toBeNull()
    expect(canDrawBuildingInObjectLayer(building({ kind: 'mint' }))).toBe(true)
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
