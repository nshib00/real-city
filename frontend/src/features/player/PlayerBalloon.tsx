import type { NearbyPlayer } from '../../shared/api/playerPresence'
import { playerLevels } from './levels'
import { LevelEmblem } from './LevelEmblem'

export function PlayerBalloon({ player }: { player: NearbyPlayer }) {
  const levelTitle = playerLevels[player.level - 1]?.title ?? `Уровень ${player.level}`
  return (
    <>
      <span className="map-player-balloon" data-model-level={player.level} aria-hidden="true">
        <svg viewBox="0 0 72 102" fill="none">
          <ellipse cx="36" cy="18" rx="25" ry="14" fill="#edc675" />
          <path d="M11 19C11 43 22 56 36 61C50 56 61 43 61 19" fill="#c88458" stroke="#815141" strokeWidth="2" />
          <path d="M26 5C18 27 25 49 36 61M46 5C54 27 47 49 36 61" stroke="#f4dfa1" strokeWidth="3" />
          <path d="M24 49L29 77M48 49L43 77" stroke="#7a5545" strokeWidth="2" />
          <circle cx="36" cy="72" r="7" fill="#e6b393" />
          <path d="M28 85C29 78 43 78 44 85" fill="#416b72" />
          <path d="M25 82L28 96H44L47 82Z" fill="#92704d" stroke="#6b4d37" strokeWidth="2" />
          <path d="M31 82V95M41 82V95" stroke="#bd9b68" strokeWidth="2" />
        </svg>
        <span className="map-player-rank-emblem">
          <LevelEmblem level={player.level} size="small" />
        </span>
      </span>
      <span className="map-player-label">
        <span className="map-player-level" title={`Уровень ${player.level}`}><span aria-hidden="true">★</span> {player.level} · {levelTitle}</span>
        <span className="map-player-name">{player.name}</span>
      </span>
    </>
  )
}
