import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { useEventReadState } from './useEventReadState'
import { useAuthStore } from '../auth/useAuthStore'
import { useGameStore } from '../../game/state/useGameStore'

beforeEach(() => { localStorage.clear(); vi.spyOn(document, 'hidden', 'get').mockReturnValue(false) })
afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('deduplicates frames and acknowledges only visible events, preserving the cursor across remounts', () => {
  const { result, rerender, unmount } = renderHook(({ visible }) => useEventReadState('p1', ['a', 'a', 'b'], visible), { initialProps: { visible: false } })
  expect(result.current).toBe(2)
  rerender({ visible: true })
  expect(result.current).toBe(0)
  unmount()
  expect(renderHook(() => useEventReadState('p1', ['a', 'b', 'c'], false)).result.current).toBe(1)
})

it('keeps accounts separate and tolerates corrupted storage', () => {
  localStorage.setItem('real-city.events.read.p1', '["a"]')
  localStorage.setItem('real-city.events.read.p2', '{bad')
  const { result, rerender } = renderHook(({ player }) => useEventReadState(player, ['a'], false), { initialProps: { player: 'p1' } })
  expect(result.current).toBe(0)
  rerender({ player: 'p2' })
  expect(result.current).toBe(1)
})

it('waits for the browser tab to become visible', () => {
  vi.mocked(vi.spyOn(document, 'hidden', 'get')).mockReturnValue(true)
  const { result } = renderHook(() => useEventReadState('p1', ['a'], true))
  expect(result.current).toBe(1)
  act(() => {
    vi.spyOn(document, 'hidden', 'get').mockReturnValue(false)
    document.dispatchEvent(new Event('visibilitychange'))
  })
  expect(result.current).toBe(0)
})

it('clears the previous account defense events on an account change', () => {
  useAuthStore.getState().setPlayer({ id: 'p1' } as never)
  useGameStore.setState({ cannonShots: [{ id: 'private' }] as never })
  useAuthStore.getState().setPlayer({ id: 'p1' } as never)
  expect(useGameStore.getState().cannonShots).toHaveLength(1)
  useAuthStore.getState().setPlayer({ id: 'p2' } as never)
  expect(useGameStore.getState().cannonShots).toEqual([])
})
