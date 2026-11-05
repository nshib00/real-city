import { describe, expect, it } from 'vitest'

import type { PlacedBuilding } from '../state/useGameStore'
import { groundRoadShapeFor, groundRoadShapeFromMask, groundRoadSpriteAsset, modularPathShapeFor, modularPathSpriteAsset } from './groundRoad'

describe('ground road renderer assets', () => {
  it('selects the modular road shape from neighboring ground roads', () => {
    const center = road('center', 10, 10)
    const buildings = [
      center,
      road('north', 10, 9),
      road('east', 11, 10),
      road('south', 10, 11),
      building('tower', 9, 10),
    ]

    expect(groundRoadShapeFor(center, buildings)).toBe('t_nes')
  })

  it('uses all exported road shape names', () => {
    expect(groundRoadShapeFromMask({ n: false, e: false, s: false, w: false })).toBe('single')
    expect(groundRoadShapeFromMask({ n: true, e: false, s: false, w: false })).toBe('end_n')
    expect(groundRoadShapeFromMask({ n: false, e: true, s: false, w: false })).toBe('end_e')
    expect(groundRoadShapeFromMask({ n: false, e: false, s: true, w: false })).toBe('end_s')
    expect(groundRoadShapeFromMask({ n: false, e: false, s: false, w: true })).toBe('end_w')
    expect(groundRoadShapeFromMask({ n: true, e: false, s: true, w: false })).toBe('straight_ns')
    expect(groundRoadShapeFromMask({ n: false, e: true, s: false, w: true })).toBe('straight_ew')
    expect(groundRoadShapeFromMask({ n: true, e: true, s: false, w: false })).toBe('corner_ne')
    expect(groundRoadShapeFromMask({ n: false, e: true, s: true, w: false })).toBe('corner_es')
    expect(groundRoadShapeFromMask({ n: false, e: false, s: true, w: true })).toBe('corner_sw')
    expect(groundRoadShapeFromMask({ n: true, e: false, s: false, w: true })).toBe('corner_wn')
    expect(groundRoadShapeFromMask({ n: true, e: true, s: true, w: false })).toBe('t_nes')
    expect(groundRoadShapeFromMask({ n: false, e: true, s: true, w: true })).toBe('t_esw')
    expect(groundRoadShapeFromMask({ n: true, e: false, s: true, w: true })).toBe('t_swn')
    expect(groundRoadShapeFromMask({ n: true, e: true, s: false, w: true })).toBe('t_wne')
    expect(groundRoadShapeFromMask({ n: true, e: true, s: true, w: true })).toBe('cross')
  })

  it('points each state to generated png assets', () => {
    expect(groundRoadSpriteAsset(road('active', 0, 0), 'straight_ew')).toBe('/assets/buildings/roads/ground_road/ground_road_straight_ew_active.png?v=road-kits-v2-2026-11-02')
    expect(groundRoadSpriteAsset({ ...road('construction', 0, 0), status: 'construction' }, 'end_n')).toBe('/assets/buildings/roads/ground_road/ground_road_end_n_construction.png?v=road-kits-v2-2026-11-02')
    expect(groundRoadSpriteAsset({ ...road('damaged', 0, 0), health: 20, maxHealth: 100 }, 'corner_ne')).toBe('/assets/buildings/roads/ground_road/ground_road_corner_ne_damaged.png?v=road-kits-v2-2026-11-02')
    expect(groundRoadSpriteAsset({ ...road('ruined', 0, 0), health: 0 }, 'cross')).toBe('/assets/buildings/roads/ground_road/ground_road_cross_ruined.png?v=road-kits-v2-2026-11-02')
  })

  it('points upgraded roads and wall variants to their generated png assets', () => {
    expect(modularPathSpriteAsset(building('standard_road', 0, 0), 'straight_ns')).toBe('/assets/buildings/roads/common_road/common_road_straight_ns_active.png?v=road-kits-v2-2026-11-02')
    expect(modularPathSpriteAsset(building('paved_road', 0, 0), 'corner_es')).toBe('/assets/buildings/roads/paved_road/paved_road_corner_es_active.png?v=road-kits-v2-2026-11-02')
    expect(modularPathSpriteAsset(building('wooden_wall', 0, 0), 'end_w')).toBe('/assets/buildings/roads/wooden_wall/wooden_wall_l01_end_w_active.png')
    expect(modularPathSpriteAsset(building('stone_wall', 0, 0), 't_swn')).toBe('/assets/buildings/roads/stone_wall/stone_wall_l04_t_swn_active.png')
    expect(modularPathSpriteAsset(building('concrete_wall', 0, 0), 'cross')).toBe('/assets/buildings/roads/concrete_wall/concrete_wall_l08_cross_active.png')
    expect(modularPathSpriteAsset(building('modern_wall', 0, 0), 'single')).toBe('/assets/buildings/roads/modern_wall/modern_wall_l11_single_active.png')
  })

  it('connects wall shapes to neighboring walls without connecting them to roads', () => {
    const center = building('wooden_wall', 10, 10, 'center')
    const buildings = [
      center,
      building('stone_wall', 10, 9, 'north'),
      building('modern_wall', 11, 10, 'east'),
      road('south-road', 10, 11),
      building('tower', 9, 10),
    ]

    expect(modularPathShapeFor(center, buildings)).toBe('corner_ne')
  })
})

function road(id: string, x: number, y: number): PlacedBuilding {
  return building('road', x, y, id)
}

function building(kind: PlacedBuilding['kind'], x: number, y: number, id: string = kind): PlacedBuilding {
  return {
    id,
    kind,
    name: id,
    level: 1,
    tile: { x, y },
    status: 'active',
    state: 'active',
    health: 100,
    maxHealth: 100,
    owner: 'test',
    startedAt: 0,
    completesAt: null,
  }
}
