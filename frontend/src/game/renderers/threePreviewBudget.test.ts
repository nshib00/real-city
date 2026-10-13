import { beforeEach, describe, expect, it } from 'vitest'

import {
  MAX_ACTIVE_THREE_PREVIEWS,
  acquireThreePreviewSlot,
  activeThreePreviewCount,
  releaseThreePreviewSlot,
  resetThreePreviewBudgetForTests,
} from './threePreviewBudget'

describe('threePreviewBudget', () => {
  beforeEach(() => {
    resetThreePreviewBudgetForTests()
  })

  it('limits active Three previews', () => {
    for (let index = 0; index < MAX_ACTIVE_THREE_PREVIEWS; index += 1) {
      expect(acquireThreePreviewSlot()).toBe(true)
    }

    expect(acquireThreePreviewSlot()).toBe(false)
    expect(activeThreePreviewCount()).toBe(MAX_ACTIVE_THREE_PREVIEWS)
  })

  it('releases preview slots without going negative', () => {
    expect(acquireThreePreviewSlot()).toBe(true)
    releaseThreePreviewSlot()
    releaseThreePreviewSlot()

    expect(activeThreePreviewCount()).toBe(0)
    expect(acquireThreePreviewSlot()).toBe(true)
  })
})
