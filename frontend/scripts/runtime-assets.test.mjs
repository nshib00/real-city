import assert from 'node:assert/strict'
import { test } from 'node:test'

import { isRuntimeAsset } from './runtime-assets.mjs'

test('keeps the monster fallback sprite while excluding source previews and combined models', () => {
  assert.equal(isRuntimeAsset('monsters/resource_guardian/resource_guardian_preview.png'), true)
  assert.equal(isRuntimeAsset('buildings/industry/mine/mine_levels.glb'), false)
  assert.equal(isRuntimeAsset('buildings/industry/mine/mine_l01_active_LOD0.glb'), true)
  assert.equal(isRuntimeAsset('buildings/center/town_hall/town_hall_l01_active_LOD0.glb'), true)
  for (const kit of ['ground_road', 'common_road', 'paved_road']) {
    assert.equal(isRuntimeAsset(`buildings/roads/${kit}/${kit}_cross_active.glb`), true)
    assert.equal(isRuntimeAsset(`buildings/roads/${kit}/${kit}.blend`), false)
  }
  assert.equal(isRuntimeAsset('terrain/tiles/road.glb'), false)
  assert.equal(isRuntimeAsset('resources/icons/coins.png'), false)
  assert.equal(isRuntimeAsset('resources/icons/runtime/coins.webp'), true)
  assert.equal(isRuntimeAsset('terrain/tiles/grass.png'), false)
  assert.equal(isRuntimeAsset('terrain/tiles/mountain_detail_staging/mountain_detail_ridge.png'), false)
  assert.equal(isRuntimeAsset('terrain/tiles/runtime/grass.webp'), true)
  assert.equal(isRuntimeAsset('buildings/industry/mine/preview/mine.png'), false)
})
