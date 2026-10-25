import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { useGameStore } from '../../game/state/useGameStore'
import { getChunks } from '../../shared/api/world'
import { useAuthStore } from '../auth/useAuthStore'
import type { Player } from '../auth/types'
import { MapWidget } from './MapWidget'

vi.mock('../../shared/api/world', () => ({ getChunks: vi.fn(async () => ({ chunks: [] })) }))

function renderMapWidget() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<MapWidget />, { wrapper: ({ children }) => <QueryClientProvider client={client}>{children}</QueryClientProvider> })
}

describe('MapWidget', () => {
  beforeEach(() => {
    vi.mocked(getChunks).mockReset()
    vi.mocked(getChunks).mockResolvedValue({ chunks: [] })
    useAuthStore.setState({ player: { id: 'test' } as Player })
    useGameStore.setState({
      selectedBuildingId: null,
      selectedTile: null,
      buildings: [],
      camera: { x: 0, y: 0, zoom: 1 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
  })

  it('disables town hall teleport until an active town hall exists', () => {
    const { rerender } = renderMapWidget()

    expect(screen.getByLabelText('К ратуше')).toHaveProperty('disabled', true)

    act(() => {
      useGameStore.setState({ buildings: [{ ...building('town_hall'), status: 'construction', completesAt: Date.now() + 1000 }] })
    })
    rerender(<MapWidget />)

    expect(screen.getByLabelText('К ратуше')).toHaveProperty('disabled', true)
  })

  it('focuses and selects the active town hall', async () => {
    useGameStore.setState({ buildings: [building('town_hall')] })
    renderMapWidget()

    fireEvent.click(screen.getByLabelText('К ратуше'))

    await waitFor(() => expect(useGameStore.getState().selectedTile).toEqual({ x: 14, y: 22 }))
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
    renderMapWidget()

    fireEvent.click(screen.getByLabelText('Карта мира'))

    const fieldMarker = screen.getByLabelText('Грядка ветролиста')
    const houseMarker = screen.getByLabelText('Землянка')
    const defenseMarker = screen.getByLabelText('Сторожевая башня')

    expect(fieldMarker.classList.contains('world-building-marker-fields')).toBe(true)
    expect(houseMarker.classList.contains('world-building-marker-housing')).toBe(true)
    expect(defenseMarker.classList.contains('world-building-marker-defense')).toBe(true)
    expect(fieldMarker.getAttribute('title')).toBe('Грядка ветролиста')
  })

  it('names world districts and numbers cells within each district', () => {
    useGameStore.setState({
      selectedTile: { x: 34, y: 70 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
    renderMapWidget()

    fireEvent.click(screen.getByLabelText('Карта мира'))

    expect(screen.getByLabelText('Район A')).toBeTruthy()
    expect(screen.getByLabelText('Район Y')).toBeTruthy()
    expect(screen.getByText('Район L · клетка L195')).toBeTruthy()
  })

  it('places the current position marker at the tile location inside its district', () => {
    useGameStore.setState({
      selectedTile: { x: 34, y: 70 },
      viewport: { center: { x: 0, y: 0 }, radius: 1 },
    })
    renderMapWidget()

    fireEvent.click(screen.getByLabelText('Карта мира'))

    const marker = screen.getByLabelText('Текущая позиция: клетка L195')
    expect(marker.style.left).toBe('21.5625%')
    expect(marker.style.top).toBe('44.0625%')
  })

  it('focuses and selects a building from its world map marker', async () => {
    useGameStore.setState({
      buildings: [building('warehouse', 'Склад материалов', { x: 48, y: 96 })],
    })
    renderMapWidget()

    fireEvent.click(screen.getByLabelText('Карта мира'))
    fireEvent.click(screen.getByLabelText('Склад материалов'))

    await waitFor(() => expect(useGameStore.getState().selectedTile).toEqual({ x: 48, y: 96 }))
    expect(useGameStore.getState().viewport.center).toEqual({ x: 48, y: 96 })
    expect(useGameStore.getState().selectedBuildingId).toBe('warehouse-id')
  })

  it('keeps the previous district visible until the destination chunks arrive', async () => {
    let finishLoading!: (value: { chunks: [] }) => void
    vi.mocked(getChunks).mockImplementationOnce(() => new Promise((resolve) => { finishLoading = resolve }))
    useGameStore.setState({ buildings: [building('warehouse', 'Склад материалов', { x: 48, y: 96 })] })
    renderMapWidget()

    fireEvent.click(screen.getByLabelText('Карта мира'))
    fireEvent.click(screen.getByLabelText('Склад материалов'))

    expect(useGameStore.getState().viewport.center).toEqual({ x: 0, y: 0 })
    await act(async () => finishLoading({ chunks: [] }))
    await waitFor(() => expect(useGameStore.getState().viewport.center).toEqual({ x: 48, y: 96 }))
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
