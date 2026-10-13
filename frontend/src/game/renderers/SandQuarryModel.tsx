import type { PlacedBuilding } from '../state/useGameStore'
import { BuildingSpriteImage } from './BuildingSpriteImage'

export function SandQuarryModel({ building }: { building: PlacedBuilding }) {
  return <BuildingSpriteImage building={building} />
}
