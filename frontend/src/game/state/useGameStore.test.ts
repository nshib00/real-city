import { describe, expect, it } from 'vitest'

import { useGameStore } from './useGameStore'

describe('useGameStore', () => {
  it('selects a tile without recentering the loaded viewport', () => {
    useGameStore.setState({ viewport: { center: { x: 3, y: 4 }, radius: 1 } })

    useGameStore.getState().selectTile({ x: 12, y: -4 })

    expect(useGameStore.getState().selectedTile).toEqual({ x: 12, y: 156 })
    expect(useGameStore.getState().viewport.center).toEqual({ x: 3, y: 4 })
  })

  it('clamps viewport radius', () => {
    useGameStore.getState().setViewportRadius(99)
    expect(useGameStore.getState().viewport.radius).toBe(4)
  })

  it('persists collapsed chat and notification preferences', () => {
    localStorage.clear()

    useGameStore.getState().setChatCollapsed(true)
    useGameStore.getState().setNotificationsCollapsed(true)

    expect(useGameStore.getState().uiPreferences.isChatCollapsed).toBe(true)
    expect(useGameStore.getState().uiPreferences.areNotificationsCollapsed).toBe(true)
    expect(JSON.parse(localStorage.getItem('real-city.ui-preferences') ?? '{}')).toMatchObject({
      isChatCollapsed: true,
      areNotificationsCollapsed: true,
    })
  })

  it('focuses map camera on a selected world tile', () => {
    useGameStore.getState().focusTile({ tile: { x: 40, y: 80 }, viewportWidth: 1200, viewportHeight: 800 })

    expect(useGameStore.getState().selectedTile).toEqual({ x: 40, y: 80 })
    expect(useGameStore.getState().viewport.center).toEqual({ x: 40, y: 80 })
  })

  it('completes construction when timer expires', () => {
    const now = 2000
    useGameStore.setState({
      buildings: [
        {
          id: 'dugout-test',
          kind: 'dugout',
          name: 'Землянка',
          level: 1,
          tile: { x: 1, y: 1 },
          status: 'construction',
          state: 'building',
          health: 100,
          owner: 'Северный двор',
          startedAt: 1000,
          completesAt: now,
        },
      ],
    })

    useGameStore.getState().tickConstructions(now)

    expect(useGameStore.getState().buildings[0].status).toBe('active')
    expect(useGameStore.getState().buildings[0].state).toBe('active')
    expect(useGameStore.getState().buildings[0].completesAt).toBeNull()
    expect(useGameStore.getState().constructionNow).toBe(now)
  })
})
