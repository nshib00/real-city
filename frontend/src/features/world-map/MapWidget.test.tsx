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

  it('shows compact colored markers for every player building', () => {
    useGameStore.setState({
      buildings: [
        building('field_bed', 'Грядка ветролиста', { x: 12, y: 18 }),
        building('dugout', 'Землянка', { x: 14, y: 18 }),
        building('tower', 'Сторожевая башня', { x: 16, y: 18 }),
      ],
    })
    render(<MapWidget />)

    fireEvent.click(screen.getByLabelText('Карта мира'))

    const fieldMarker = screen.getByLabelText('Грядка ветролиста')
    const houseMarker = screen.getByLabelText('Землянка')
    const defenseMarker = screen.getByLabelText('Сторожевая башня')

    expect(fieldMarker.classList.contains('world-building-marker-fields')).toBe(true)
    expect(houseMarker.classList.contains('world-building-marker-housing')).toBe(true)
    expect(defenseMarker.classList.contains('world-building-marker-defense')).toBe(true)
    expect(fieldMarker.getAttribute('title')).toBe('Грядка ветролиста')
  })

  it('names world districts with public letters while keeping tile coordinates numeric', () => {
    useGameStore.setState({
      selectedTile: { x: 34, y: 70 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
    render(<MapWidget />)

    fireEvent.click(screen.getByLabelText('Карта мира'))

    expect(screen.getByLabelText('Район A')).toBeTruthy()
    expect(screen.getByLabelText('Район Y')).toBeTruthy()
    expect(screen.getByText('Район L · 34:70')).toBeTruthy()
  })

  it('places the current position marker at the tile location inside its district', () => {
    useGameStore.setState({
      selectedTile: { x: 34, y: 70 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
    render(<MapWidget />)

    fireEvent.click(screen.getByLabelText('Карта мира'))

    const marker = screen.getByLabelText('Текущая позиция: район L, тайл 34:70')
    expect(marker.style.left).toBe('21.5625%')
    expect(marker.style.top).toBe('44.0625%')
  })

  it('focuses and selects a building from its world map marker', () => {
    useGameStore.setState({
      buildings: [building('warehouse', 'Склад материалов', { x: 48, y: 96 })],
    })
    render(<MapWidget />)

    fireEvent.click(screen.getByLabelText('Карта мира'))
    fireEvent.click(screen.getByLabelText('Склад материалов'))

    expect(useGameStore.getState().selectedTile).toEqual({ x: 48, y: 96 })
    expect(useGameStore.getState().viewport.center).toEqual({ x: 48, y: 96 })
    expect(useGameStore.getState().selectedBuildingId).toBe('warehouse-id')
  })
})

function building(kind: BuildingKind, name = 'Ратуша', tile = { x: 14, y: 22 }): PlacedBuilding {
  return {
    id: `${kind}-id`,
    kind,
    name,
    level: 1,
    tile,
    status: 'active',
    health: 100,
    owner: 'test',
    startedAt: 0,
    completesAt: null,
  }
}
