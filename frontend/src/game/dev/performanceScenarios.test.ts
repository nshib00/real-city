import { describe, expect, it } from 'vitest'

import { createPerformanceScenario, resolvePerformanceScenarioFromSearch } from './performanceScenarios'

describe('performance scenarios', () => {
  it('builds a deterministic heavy object scenario around the viewport center', () => {
    const scenario = createPerformanceScenario('mixed', {
      center: { x: 10, y: -4 },
      buildingCount: 120,
      monsterCount: 40,
      resourceCount: 25,
      tileRadius: 3,
      now: Date.parse('2026-10-12T10:00:00Z'),
    })

    expect(scenario.buildings).toHaveLength(120)
    expect(scenario.monsters).toHaveLength(40)
    expect(scenario.resources).toHaveLength(25)
    expect(scenario.tiles).toHaveLength(49)
    expect(new Set(scenario.buildings.map((building) => building.id)).size).toBe(120)
    expect(scenario.buildings.some((building) => building.status === 'construction')).toBe(true)
    expect(scenario.monsters.some((monster) => monster.state === 'wandering')).toBe(true)
  })

  it('resolves only explicit dev query scenarios', () => {
    expect(resolvePerformanceScenarioFromSearch('?perf=buildings&perfBuildings=12&perfMonsters=3', true)).toMatchObject({
      name: 'buildings',
      buildings: expect.arrayContaining([expect.objectContaining({ id: 'perf-building-0' })]),
      monsters: expect.arrayContaining([expect.objectContaining({ id: 'perf-monster-0' })]),
    })
    expect(resolvePerformanceScenarioFromSearch('?perf=buildings&perfBuildings=12&perfMonsters=3', true)?.buildings).toHaveLength(12)
    expect(resolvePerformanceScenarioFromSearch('?perf=buildings&perfBuildings=12&perfMonsters=3', true)?.monsters).toHaveLength(3)
    expect(resolvePerformanceScenarioFromSearch('?perf=buildings', false)).toBeNull()
    expect(resolvePerformanceScenarioFromSearch('?perf=unknown', true)).toBeNull()
  })
})
