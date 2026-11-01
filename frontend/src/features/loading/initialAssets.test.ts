import { describe, expect, it, vi } from 'vitest'
import { loadInitialAssetTasks, type InitialAssetTask } from './initialAssets'

vi.mock('pixi.js', () => ({ Assets: { load: vi.fn() } }))

describe('начальная загрузка файлов', () => {
  it('считает только завершённые файлы и повторяет неудавшуюся группу', async () => {
    const completed = new Set<string>()
    const loadAtlas = vi.fn()
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(undefined)
    const tasks: InitialAssetTask[] = [
      { urls: ['/terrain.png'], group: 'terrain', load: async () => undefined },
      { urls: ['/monster.json', '/monster.webp'], group: 'objects', load: loadAtlas },
    ]
    const progress: number[] = []
    const groups: string[] = []

    const first = await loadInitialAssetTasks(tasks, completed, (state) => { progress.push(state.loaded); groups.push(state.group) })
    expect(first).toEqual({ loaded: 1, failed: 2, total: 3 })
    expect(completed).toEqual(new Set(['/terrain.png']))
    expect(progress).toContain(1)
    expect(groups).toEqual(['terrain', 'terrain', 'objects', 'objects'])

    const second = await loadInitialAssetTasks(tasks, completed, (state) => progress.push(state.loaded))
    expect(second).toEqual({ loaded: 3, failed: 0, total: 3 })
    expect(loadAtlas).toHaveBeenCalledTimes(2)
  })
})
