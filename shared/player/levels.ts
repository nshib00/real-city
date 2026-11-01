import definitions from '../../data/player/levels.json'
export const playerLevels = definitions
export const levelThresholds = playerLevels.map((level) => level.xp)
export function playerProgress(xp: number) {
 const total = Number.isFinite(xp) ? Math.max(0, Math.floor(xp)) : 0
 const index = playerLevels.reduce((i, level, candidate) => total >= level.xp ? candidate : i, 0)
 const current = playerLevels[index]
 const next = playerLevels[index + 1]
 const earned = total - current.xp
 return { ...current, totalXp: total, nextLevelXp: next?.xp ?? null, earned,
   remaining: next ? next.xp - total : 0, percent: next ? Math.min(100, Math.floor(earned / (next.xp - current.xp) * 100)) : 0 }
}
