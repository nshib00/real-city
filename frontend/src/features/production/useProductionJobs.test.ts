import { describe, expect, it } from 'vitest'

import { productionJobsPollInterval } from './useProductionJobs'

describe('production job polling', () => {
  it('keeps a short interval for running jobs and relaxes idle polling only while realtime is connected', () => {
    expect(productionJobsPollInterval([{ state: 'running' }], true)).toBe(5000)
    expect(productionJobsPollInterval([{ state: 'running' }], false)).toBe(5000)
    expect(productionJobsPollInterval([], true)).toBe(30_000)
    expect(productionJobsPollInterval([], false)).toBe(10_000)
    expect(productionJobsPollInterval([{ state: 'ready' }], true)).toBe(30_000)
  })
})
