import { expect, it } from 'vitest'
import { formatAmount } from './formatAmount'
it('сохраняет малые запасы и ограничивает длину больших значений', () => {
  expect(formatAmount(1)).toBe('1')
  expect(formatAmount(0)).toBe('0')
  expect(formatAmount(123_500_000)).toContain('123,5')
  expect(formatAmount(123_500_000).length).toBeLessThan(15)
})
