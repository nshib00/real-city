import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { useGameStore } from '../../game/state/useGameStore'
import { MapWidget } from './MapWidget'

describe('MapWidget', () => {
  beforeEach(() => {
    useGameStore.setState({
      selectedBuildingId: null,
      selectedTile: null,
      buildings: [],
      camera: { x: 0, y: 0, zoom: 1 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
  })

  it('disables town hall teleport until an active town hall exists', () => {
    const { rerender } = render(<MapWidget />)

    expect(screen.getByLabelText('К ратуше')).toHaveProperty('disabled', true)

    act(() => {
      useGameStore.setState({ buildings: [{ ...building('town_hall'), status: 'construction', completesAt: Date.now() + 1000 }] })
    })
    rerender(<MapWidget />)

    expect(screen.getByLabelText('К ратуше')).toHaveProperty('disabled', true)
  })

  it('focuses and selects the active town hall', () => {
    useGameStore.setState({ buildings: [building('town_hall')] })
    render(<MapWidget />)

    fireEvent.click(screen.getByLabelText('К ратуше'))

    expect(useGameStore.getState().selectedTile).toEqual({ x: 14, y: 22 })
    expect(useGameStore.getState().viewport.center).toEqual({ x: 14, y: 22 })
    expect(useGameStore.getState().selectedBuildingId).toBe('town_hall-id')
  })
})

function building(kind: BuildingKind): PlacedBuilding {
  return {
    id: `${kind}-id`,
    kind,
    name: 'Ратуша',
    level: 1,
    tile: { x: 14, y: 22 },
    status: 'active',
    health: 100,
    owner: 'test',
    startedAt: 0,
    completesAt: null,
  }
}
