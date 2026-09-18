import type { PlacedBuilding } from '../state/useGameStore'
import { BuildingSpriteImage } from './BuildingSpriteImage'

export function LumberYardModel({ building }: { building: PlacedBuilding }) {
  return <BuildingSpriteImage building={building} />
}
