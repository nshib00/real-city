import type { PlacedBuilding } from '../state/useGameStore'
import { BuildingSpriteImage } from './BuildingSpriteImage'

export function GlassWorkshopModel({ building }: { building: PlacedBuilding }) {
  return <BuildingSpriteImage building={building} />
}
