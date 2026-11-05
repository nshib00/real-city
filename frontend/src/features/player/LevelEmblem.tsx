import { playerLevels } from './levels'

export type LevelEmblemSize = 'small' | 'medium' | 'large'

export function LevelEmblem({ level, size, className = '' }: { level: number; size: LevelEmblemSize; className?: string }) {
  const safeLevel = Math.min(15, Math.max(1, Math.floor(level || 1)))
  const definition = playerLevels[safeLevel - 1]
  const title = definition?.title ?? `Уровень ${safeLevel}`
  // Legacy city emblems remain in the asset tree but do not represent the new player statuses.
  return <span className={`level-emblem level-emblem-fallback level-emblem-${size} ${className}`} role="img" aria-label={`Уровень ${safeLevel}: ${title}`}>{safeLevel}</span>
}
