import type { PlacedBuilding } from '../state/useGameStore'
import { buildingSpriteAsset } from './buildingSpriteAssets'

export function BuildingSpriteImage({ building }: { building: PlacedBuilding }) {
  const asset = buildingSpriteAsset(building)
  if (!asset) {
    return null
  }

  return <img className="building-sprite-image" src={asset} alt="" aria-hidden="true" draggable={false} />
}
