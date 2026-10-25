import { lazy, Suspense } from 'react'

import type { PlacedBuilding } from '../state/useGameStore'

const LazyBuildingGlbModel = lazy(() => import('./BuildingGlbModel').then((module) => ({ default: module.BuildingGlbModel })))

export function BuildingModelPreview({ building, className = '' }: { building: PlacedBuilding; className?: string }) {
  return (
    <div className={`building-model-preview ${className}`.trim()} data-testid="building-model-preview">
      <Suspense fallback={<span className="building-model-preview-status">Загрузка 3D</span>}>
        <LazyBuildingGlbModel building={building} />
      </Suspense>
      <span className="building-model-preview-hint">Тяните для вращения · колесо — масштаб</span>
    </div>
  )
}
