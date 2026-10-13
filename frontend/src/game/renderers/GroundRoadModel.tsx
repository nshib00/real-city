import type { PlacedBuilding } from '../state/useGameStore'
import { modularPathSpriteAsset, type ModularPathShape } from './groundRoad'

export function GroundRoadModel({ building, shape }: { building: PlacedBuilding; shape: ModularPathShape }) {
  const asset = modularPathSpriteAsset(building, shape)
  if (!asset) {
    return null
  }
  return <img className="building-sprite-image modular-path-sprite-image" src={asset} alt="" aria-hidden="true" draggable={false} />
}
