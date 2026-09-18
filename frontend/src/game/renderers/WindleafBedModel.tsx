import type { PlacedBuilding } from '../state/useGameStore'
import { BuildingSpriteImage } from './BuildingSpriteImage'

export function WindleafBedModel({ building }: { building: PlacedBuilding }) {
  return <BuildingSpriteImage building={building} />
}
