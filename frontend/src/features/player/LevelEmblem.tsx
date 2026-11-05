import { useState } from 'react'

import { playerLevels } from './levels'

export type LevelEmblemSize = 'small' | 'medium' | 'large'

export function LevelEmblem({ level, size, className = '' }: { level: number; size: LevelEmblemSize; className?: string }) {
  const safeLevel = Math.min(15, Math.max(1, Math.floor(level || 1)))
  const definition = playerLevels[safeLevel - 1]
  const title = definition?.title ?? `Уровень ${safeLevel}`
  const iconId = definition?.icon ?? `level-${String(safeLevel).padStart(2, '0')}`
  const source = `${import.meta.env.BASE_URL}assets/player-levels/${iconId}/${size}.png`
  const [failedSource, setFailedSource] = useState('')

  if (failedSource === source) {
    return <span className={`level-emblem level-emblem-fallback level-emblem-${size} ${className}`} role="img" aria-label={`Уровень ${safeLevel}: ${title}`}>{safeLevel}</span>
  }

  return <img className={`level-emblem level-emblem-${size} ${className}`} src={source} alt={`Уровень ${safeLevel}: ${title}`} onError={() => setFailedSource(source)} />
}
