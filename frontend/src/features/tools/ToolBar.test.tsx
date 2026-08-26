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

    fireEvent.click(screen.getByLabelText('Рейд'))

    expect(useGameStore.getState().tool).toBe('raid')
    expect(screen.getByLabelText('Рейд').getAttribute('aria-pressed')).toBe('true')
  })
})
