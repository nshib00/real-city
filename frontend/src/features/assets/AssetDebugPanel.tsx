import { useEffect, useMemo, useState } from 'react'

import { BuildingModelPreview } from '../../game/renderers/BuildingModelPreview'
import type { PlacedBuilding } from '../../game/state/useGameStore'
import type { ObjectAtlasLoadResult } from '../../game/renderer/objectLayer/objectTextureCache'
import {
  buildingAssetLevel,
  buildingAssetState,
  canResolveBuildingModelAsset,
  registeredBuildingAssetFamilies,
  resolveBuildingAtlasSource,
  resolveBuildingModelAsset,
  resolveBuildingSpriteAsset,
} from '../../game/renderers/buildingRegistry'

export function shouldShowAssetDebugPanel(search = typeof window === 'undefined' ? '' : window.location.search) {
  return import.meta.env.DEV && new URLSearchParams(search).has('assets')
}

export function AssetDebugPanel() {
  const rows = useMemo(() => registeredBuildingAssetFamilies().map((manifest) => {
    const previewBuilding = previewBuildingFor(manifest.kind)
    const shape = manifest.shapeDefault ? 'straight_ew' : undefined
    const sprite = resolveBuildingSpriteAsset(previewBuilding, { shape })
    const model = resolveBuildingModelAsset(previewBuilding, { shape })
    const hasModel = canResolveBuildingModelAsset(previewBuilding, { shape })
    const atlasSource = resolveBuildingAtlasSource(previewBuilding, { shape })
    const selectedLevel = buildingAssetLevel(previewBuilding)
    const selectedState = buildingAssetState(previewBuilding)
    const errors = [
      manifest.levels.length ? null : 'no levels',
      manifest.states.length ? null : 'no states',
      sprite ? null : 'missing png lookup',
      hasModel ? null : 'missing glb lookup',
    ].filter(Boolean) as string[]
    return { manifest, previewBuilding, sprite, model, hasModel, atlasSource, selectedLevel, selectedState, errors }
  }), [])
  const [atlasResults, setAtlasResults] = useState<Record<string, ObjectAtlasLoadResult>>({})
  const [previewKey, setPreviewKey] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    import('../../game/renderer/objectLayer/objectTextureCache').then(({ loadObjectAtlas }) => {
      rows.forEach((row) => {
        if (!row.atlasSource?.atlas) {
          return
        }

        loadObjectAtlas(row.atlasSource).then((result) => {
          if (cancelled) {
            return
          }
          setAtlasResults((current) => ({ ...current, [result.cacheKey]: result }))
        })
      })
    })

    return () => {
      cancelled = true
    }
  }, [rows])

  return (
    <aside className="asset-debug-panel" aria-label="Asset debug">
      <header>
        <strong>Asset registry</strong>
        <span>{rows.length} families</span>
      </header>
      <div className="asset-debug-list">
        {rows.map(({ manifest, previewBuilding, sprite, model, hasModel, atlasSource, selectedLevel, selectedState, errors }) => {
          const key = `${manifest.kind}:${manifest.assetId}`
          const previewOpen = previewKey === key
          return (
          <article className="asset-debug-row" key={key}>
            <div className="asset-debug-preview">
              {previewOpen ? (
                <BuildingModelPreview building={previewBuilding} className="asset-debug-model-preview" />
              ) : sprite ? (
                <img src={sprite} alt="" draggable={false} />
              ) : (
                <span />
              )}
            </div>
            <div className="asset-debug-meta">
              <strong>{manifest.displayName}</strong>
              <span>{manifest.kind} / {manifest.category}/{manifest.assetId}</span>
              <small>levels {rangeText(manifest.levels)} · states {manifest.states.join(', ')}</small>
              <small>preview l{selectedLevel} {selectedState}</small>
              <small>{atlasDebugText(atlasSource, atlasResults)}</small>
              <span className="asset-debug-actions">
                {model ? <a href={model} target="_blank" rel="noreferrer">GLB</a> : null}
                {hasModel ? (
                  <button type="button" onClick={() => setPreviewKey(previewOpen ? null : key)}>
                    {previewOpen ? 'close preview' : '3D preview'}
                  </button>
                ) : null}
              </span>
              {errors.length ? <em>{errors.join(', ')}</em> : <em>ok</em>}
            </div>
          </article>
          )
        })}
      </div>
    </aside>
  )
}

function previewBuildingFor(kind: PlacedBuilding['kind']): PlacedBuilding {
  return {
    id: `${kind}-asset-debug`,
    kind,
    name: kind,
    level: 1,
    tile: { x: 0, y: 0 },
    owner: 'debug',
    status: 'active',
    state: 'active',
    health: 100,
    maxHealth: 100,
    startedAt: 0,
    completesAt: null,
  }
}

function rangeText(levels: readonly number[]) {
  if (!levels.length) {
    return '-'
  }
  if (levels.length === 1) {
    return String(levels[0])
  }
  return `${levels[0]}-${levels[levels.length - 1]}`
}

function atlasDebugText(atlasSource: ReturnType<typeof resolveBuildingAtlasSource>, atlasResults: Record<string, ObjectAtlasLoadResult>) {
  if (!atlasSource?.atlas) {
    return 'atlas: none · fallback PNG'
  }

  const result = atlasResults[`${atlasSource.assetId}@${atlasSource.atlas.revision ?? atlasSource.revision ?? 'unversioned'}`]
  if (!result) {
    return `atlas: loading · required ${atlasSource.requiredFrames?.length ?? 0}`
  }

  if (result.status === 'fallback') {
    return `atlas: fallback · ${result.reason}`
  }

  const missing = result.missingFrames.length ? ` · missing ${result.missingFrames.length}` : ' · missing 0'
  return `atlas: found · frames ${result.frameCount}${missing}`
}
