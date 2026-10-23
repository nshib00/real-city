import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PlayerBalloon } from './PlayerBalloon'

describe('PlayerBalloon', () => {
  it('shows the player nickname and level rather than the city name', () => {
    const { container } = render(<PlayerBalloon player={{ player_id: 'other', name: 'Аэрон', level: 4, tile_x: 8, tile_y: 12 }} />)

    expect(screen.getByText('Аэрон')).toBeTruthy()
    expect(screen.getByTitle('Уровень 4').textContent).toContain('4')
    expect(container.querySelector('[data-model-level="4"] svg')).not.toBeNull()
  })
})
