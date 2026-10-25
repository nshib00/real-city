import { beforeEach, describe, expect, it } from 'vitest'
import { useGameStore } from '../game/state/useGameStore'
import { selectAmbience } from './ambience'

describe('атмосфера видимой карты', () => {
  beforeEach(() => useGameStore.setState({ worldTiles: [], buildings: [], viewport: { center: { x: 0, y: 0 }, radius: 1 }, camera: { x: 0, y: 0, zoom: 1 } }))

  it('выбирает максимум два биома и не включает далёкую постройку', () => {
    useGameStore.setState({
      worldTiles: [
        { x: 0, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'forest', elevation: 0, safe_zone: false, forest_density: 3 },
        { x: 1, y: 0, chunk_x: 0, chunk_y: 0, terrain: 'water', elevation: 0, safe_zone: false, forest_density: 0 },
        { x: 100, y: 100, chunk_x: 6, chunk_y: 6, terrain: 'mountain', elevation: 0, safe_zone: false, forest_density: 0 },
      ],
      buildings: [{ id: 'far', kind: 'oil_well', name: 'Скважина', level: 1, tile: { x: 100, y: 100 }, status: 'active', health: 100, owner: 'p', startedAt: 0, completesAt: null }],
    })
    const selected = selectAmbience()
    expect([...selected.keys()]).toEqual(['ambience.forest', 'ambience.river'])
    expect(selected.has('ambience.oil_well')).toBe(false)
  })
})
