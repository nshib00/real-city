import type { PlacedBuilding } from '../state/useGameStore'
import { BuildingSpriteImage } from './BuildingSpriteImage'

export function WoodHouseModel({ building }: { building: PlacedBuilding }) {
  return <BuildingSpriteImage building={building} />
}
