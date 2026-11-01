import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { InterfaceNavigation } from './InterfaceNavigation'

describe('InterfaceNavigation', () => {
  it('cycles regions in both directions, including a mounted build menu', () => {
    render(<><InterfaceNavigation /><section id="game-map" tabIndex={0} /><nav id="game-tools" tabIndex={-1}><button>Инструмент</button></nav><section id="game-build-menu" tabIndex={-1} /><aside id="game-inspector" tabIndex={-1} /><section id="game-events" tabIndex={-1} /></>)
    screen.getByText('Инструмент').focus()
    fireEvent.keyDown(window, { key: 'F6' })
    expect(document.activeElement?.id).toBe('game-build-menu')
    fireEvent.keyDown(window, { key: 'F6' })
    expect(document.activeElement?.id).toBe('game-inspector')
    fireEvent.keyDown(window, { key: 'F6', shiftKey: true })
    expect(document.activeElement?.id).toBe('game-build-menu')
    document.getElementById('game-events')?.focus()
    fireEvent.keyDown(window, { key: 'F6' })
    expect(document.activeElement?.id).toBe('game-map')
  })

  it('does not escape a modal and skips an inert region', () => {
    const { rerender } = render(<><InterfaceNavigation /><section id="game-map" tabIndex={0} /><nav id="game-tools" tabIndex={-1} inert /><aside id="game-inspector" tabIndex={-1} /><section role="dialog" aria-modal="true"><button>Подтвердить</button></section></>)
    screen.getByText('Подтвердить').focus()
    fireEvent.keyDown(window, { key: 'F6' })
    expect(document.activeElement).toBe(screen.getByText('Подтвердить'))
    rerender(<><InterfaceNavigation /><section id="game-map" tabIndex={0} /><nav id="game-tools" tabIndex={-1} inert /><aside id="game-inspector" tabIndex={-1} /></>)
    document.getElementById('game-map')?.focus()
    fireEvent.keyDown(window, { key: 'F6' })
    expect(document.activeElement?.id).toBe('game-inspector')
  })
})
