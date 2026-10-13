import type { PlacedBuilding } from '../state/useGameStore'
import { BuildingSpriteImage } from './BuildingSpriteImage'

export function MineModel({ building }: { building: PlacedBuilding }) {
  return <BuildingSpriteImage building={building} />
}
