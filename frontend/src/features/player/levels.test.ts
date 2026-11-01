import { describe, expect, it } from 'vitest'
import { playerLevels, playerProgress } from './levels'
describe('shared player levels', () => {
 it('handles exact thresholds, invalid input and maximum XP', () => {
  for (const item of playerLevels) expect(playerProgress(item.xp).level).toBe(item.level)
  expect(playerProgress(450)).toMatchObject({ level:2,earned:250,remaining:250,percent:50,nextLevelXp:700 })
  expect(playerProgress(Number.NaN)).toMatchObject({ level:1,totalXp:0 })
  expect(playerProgress(18121201)).toMatchObject({ level:15,nextLevelXp:null,earned:1,remaining:0 })
 })
})
