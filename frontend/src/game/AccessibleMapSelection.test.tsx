import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { AccessibleMapSelection } from './AccessibleMapSelection'
import { useGameStore } from './state/useGameStore'

afterEach(cleanup)
it('сохраняет выбранное здание после центрирования камеры', () => {
  const state = useGameStore.getState()
  useGameStore.setState({ buildings: [], buildingIndexById: {}, monsters: [], selectedBuildingId: null })
  state.addBuilding({ id: 'inspection', kind: 'dugout', name: 'Землянка', level: 1, tile: { x: 4, y: 4 }, owner: 'p1', health: 80, status: 'active', state: 'active', startedAt: 0, completesAt: null })
  render(<AccessibleMapSelection />)
  fireEvent.change(screen.getByLabelText('X'), { target: { value: '4' } })
  fireEvent.change(screen.getByLabelText('Y'), { target: { value: '4' } })
  fireEvent.click(screen.getByRole('button', { name: 'Осмотреть клетку' }))
  expect(useGameStore.getState().selectedBuildingId).toBe('inspection')
  expect(useGameStore.getState().viewport.center).toEqual({ x: 4, y: 4 })
})
it('осматривает координаты без выполнения активного инструмента и отклоняет дроби', () => {
  useGameStore.setState({ buildings: [], monsters: [], selectedTile: null, tool: 'attack' })
  render(<AccessibleMapSelection />)
  fireEvent.click(screen.getByText('Выбрать клетку по координатам'))
  fireEvent.change(screen.getByLabelText('X'), { target: { value: '1.5' } })
  fireEvent.click(screen.getByRole('button', { name: 'Осмотреть клетку' }))
  expect(useGameStore.getState().selectedTile).toBeNull()
  expect(screen.getByRole('status').textContent).toContain('целыми')
  fireEvent.change(screen.getByLabelText('X'), { target: { value: '12' } })
  fireEvent.change(screen.getByLabelText('Y'), { target: { value: '14' } })
  fireEvent.click(screen.getByRole('button', { name: 'Осмотреть клетку' }))
  expect(useGameStore.getState().selectedTile).toEqual({ x: 12, y: 14 })
  expect(useGameStore.getState().tool).toBe('select')
  expect(screen.getByRole('status').textContent).toContain('12, 14')
})
