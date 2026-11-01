import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useGameStore } from '../../game/state/useGameStore'
import { ToolBar } from './ToolBar'

describe('ToolBar', () => {
  beforeEach(() => {
    useGameStore.setState({ tool: 'select' })
  })

  it('switches active tool mode', () => {
    render(<ToolBar />)

    fireEvent.click(screen.getByLabelText('Атака'))

    expect(useGameStore.getState().tool).toBe('attack')
    expect(screen.getByLabelText('Атака').getAttribute('aria-pressed')).toBe('true')
  })
  it('opens sound settings outside the toolbar and closes with Escape', () => {
    render(<ToolBar />)
    expect(screen.queryByText('1–5 — инструменты')).toBeNull()
    const opener = screen.getByRole('button', { name: 'Настройки звука' })
    opener.focus()
    fireEvent.click(opener)
    const panel = screen.getByRole('complementary', { name: 'Настройки звука' })
    expect(panel.closest('.tool-bar')).toBeNull()
    expect(screen.getByRole('slider', { name: /Общая громкость:/ })).toBeTruthy()
    fireEvent.keyDown(panel, { key: 'Escape' })
    expect(screen.queryByRole('complementary', { name: 'Настройки звука' })).toBeNull()
    expect(document.activeElement).toBe(opener)
  })
  it('switches with digits, cancels preview and ignores typing', () => {
    render(<ToolBar />)
    fireEvent.keyDown(window, { key: '5' })
    expect(useGameStore.getState().tool).toBe('attack')
    useGameStore.setState({ placementPreviewKind: 'dugout', tool: 'build' })
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(useGameStore.getState().placementPreviewKind).toBeNull()
    expect(useGameStore.getState().tool).toBe('select')
    const input = document.createElement('input')
    document.body.append(input)
    fireEvent.keyDown(input, { key: '5' })
    expect(useGameStore.getState().tool).toBe('select')
    input.remove()
  })
})
