import { describe, expect, it } from 'vitest'

import { shouldShowAssetDebugPanel } from './AssetDebugPanel'

describe('AssetDebugPanel visibility', () => {
  it('is gated by the assets query flag in dev builds', () => {
    expect(shouldShowAssetDebugPanel('?assets=1')).toBe(true)
    expect(shouldShowAssetDebugPanel('?debug=1')).toBe(false)
  })
})

