import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  clearObjectAtlasCache,
  extractAtlasFrameNames,
  loadObjectAtlas,
  objectAtlasCacheKey,
  objectAtlasUrls,
} from './objectTextureCache'

const { loadPixiAsset } = vi.hoisted(() => ({
  loadPixiAsset: vi.fn((url: string) => {
    if (url.includes('.atlas.json')) {
      return Promise.resolve({
        frames: {
          'lumber_yard_l01_active.png': {},
          'lumber_yard_working_0000.png': {},
        },
      })
    }
    return Promise.resolve({})
  }),
}))

vi.mock('pixi.js', () => ({
  Assets: {
    load: loadPixiAsset,
  },
}))

describe('object texture cache', () => {
  beforeEach(() => {
    clearObjectAtlasCache()
    loadPixiAsset.mockClear()
  })

  it('builds cache keys and revised atlas URLs from manifest metadata', () => {
    const source = {
      assetId: 'lumber_yard',
      basePath: '/assets/buildings/industry/lumber_yard',
      revision: 'sprite-rev',
      atlas: {
        image: 'lumber_yard.webp',
        json: 'lumber_yard.atlas.json',
        revision: 'atlas-rev',
      },
    }

    expect(objectAtlasCacheKey(source)).toBe('lumber_yard@atlas-rev')
    expect(objectAtlasUrls(source)).toEqual({
      imageUrl: '/assets/buildings/industry/lumber_yard/lumber_yard.webp?v=atlas-rev',
      jsonUrl: '/assets/buildings/industry/lumber_yard/lumber_yard.atlas.json?v=atlas-rev',
    })
  })

  it('loads atlas JSON and image through Pixi Assets and reports missing frames', async () => {
    const result = await loadObjectAtlas({
      assetId: 'lumber_yard',
      basePath: '/assets/buildings/industry/lumber_yard',
      atlas: {
        image: 'lumber_yard.webp',
        json: 'lumber_yard.atlas.json',
        revision: 'atlas-rev',
      },
      fallbackUrl: '/assets/buildings/industry/lumber_yard/lumber_yard_l01_active.png',
      requiredFrames: [
        'lumber_yard_l01_active.png',
        'lumber_yard_working_0000.png',
        'lumber_yard_working_0001.png',
      ],
    })

    expect(result).toMatchObject({
      status: 'atlas',
      cacheKey: 'lumber_yard@atlas-rev',
      frameCount: 2,
      missingFrames: ['lumber_yard_working_0001.png'],
    })
    expect(loadPixiAsset).toHaveBeenCalledWith('/assets/buildings/industry/lumber_yard/lumber_yard.atlas.json?v=atlas-rev')
    expect(loadPixiAsset).toHaveBeenCalledWith('/assets/buildings/industry/lumber_yard/lumber_yard.webp?v=atlas-rev')
  })

  it('reuses the cached promise for the same asset revision', async () => {
    const source = {
      assetId: 'lumber_yard',
      basePath: '/assets/buildings/industry/lumber_yard',
      atlas: {
        image: 'lumber_yard.webp',
        json: 'lumber_yard.atlas.json',
        revision: 'atlas-rev',
      },
    }

    await Promise.all([loadObjectAtlas(source), loadObjectAtlas(source)])

    expect(loadPixiAsset).toHaveBeenCalledTimes(2)
  })

  it('returns fallback state without Pixi calls when atlas is absent', async () => {
    const result = await loadObjectAtlas({
      assetId: 'mine',
      basePath: '/assets/buildings/industry/mine',
      fallbackUrl: '/assets/buildings/industry/mine/mine_l01_active.png',
    })

    expect(result).toEqual({
      status: 'fallback',
      cacheKey: 'mine@unversioned',
      assetId: 'mine',
      fallbackUrl: '/assets/buildings/industry/mine/mine_l01_active.png',
      reason: 'missing-atlas',
    })
    expect(loadPixiAsset).not.toHaveBeenCalled()
  })

  it('extracts frame names from Pixi and array-style atlas payloads', () => {
    expect(extractAtlasFrameNames({ data: { frames: { 'a.png': {}, 'b.png': {} } } })).toEqual(['a.png', 'b.png'])
    expect(extractAtlasFrameNames({ frames: [{ filename: 'c.png' }, { name: 'd.png' }, { id: 'e.png' }] })).toEqual(['c.png', 'd.png', 'e.png'])
  })
})
