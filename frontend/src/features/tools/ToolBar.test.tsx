import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'

import { useGameStore } from '../../game/state/useGameStore'
import { ToolBar } from './ToolBar'

describe('ToolBar', () => {
  const renderToolBar = () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    return render(<QueryClientProvider client={client}><ToolBar /></QueryClientProvider>)
  }

  beforeEach(() => {
    useGameStore.setState({
      tool: 'select',
      uiPreferences: { ...useGameStore.getState().uiPreferences, buildMenuOpen: false },
    })
  })

  it('opens the build menu and returns to selection mode', () => {
    renderToolBar()

    fireEvent.click(screen.getByRole('button', { name: /Строить/ }))
    expect(useGameStore.getState().tool).toBe('build')
    expect(useGameStore.getState().uiPreferences.buildMenuOpen).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: 'Выбор' }))
    expect(useGameStore.getState().tool).toBe('select')
    expect(useGameStore.getState().uiPreferences.buildMenuOpen).toBe(false)
  })
  it('opens building with its shortcut, cancels preview and ignores typing', () => {
    renderToolBar()
    fireEvent.keyDown(window, { key: '2' })
    expect(useGameStore.getState().uiPreferences.buildMenuOpen).toBe(true)
    useGameStore.setState({ placementPreviewKind: 'dugout', tool: 'build' })
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(useGameStore.getState().placementPreviewKind).toBeNull()
    expect(useGameStore.getState().tool).toBe('select')
    const input = document.createElement('input')
    document.body.append(input)
    fireEvent.keyDown(input, { key: '2' })
    expect(useGameStore.getState().tool).toBe('select')
    input.remove()
  })
})
