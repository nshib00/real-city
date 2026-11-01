import { useEffect, useMemo, useState } from 'react'
import { audioManager } from '../../audio/AudioManager'

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
  const [variants, setVariants] = useState<Record<string, { level: number; state: 'active' | 'construction' | 'damaged' | 'ruined' }>>({})
  const [atlasGeneration, setAtlasGeneration] = useState(0)
  const [audioStatus, setAudioStatus] = useState(audioManager.diagnostics())
  useEffect(() => {
    const timer = window.setInterval(() => setAudioStatus(audioManager.diagnostics()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  const rows = useMemo(() => registeredBuildingAssetFamilies().map((manifest) => {
    const previewBuilding = previewBuildingFor(manifest.kind)
    const variant = variants[manifest.kind]
    if (variant) {
      previewBuilding.level = variant.level
      previewBuilding.status = variant.state === 'construction' ? 'construction' : 'active'
      previewBuilding.state = variant.state === 'construction' ? 'building' : variant.state
      previewBuilding.health = variant.state === 'ruined' ? 0 : variant.state === 'damaged' ? 10 : 100
    }
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
  }), [variants])
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
  }, [rows, atlasGeneration])

  return (
    <aside className="asset-debug-panel" aria-label="Asset debug">
      <section aria-label="Audio debug">
        <strong>Audio</strong> {audioStatus.state} · {audioStatus.voices} voices · {Math.round(audioStatus.cacheBytes / 1024)} KB cache
        <div>Last: {audioStatus.lastSound ?? '—'} · limited: {audioStatus.limited}</div>
        {audioStatus.errors.map((error, index) => <div key={`${index}:${error}`}>{error}</div>)}
      </section>
      <header>
        <strong>Asset registry</strong>
        <span>{rows.length} families</span>
        <button type="button" onClick={() => { void import('../../game/renderer/objectLayer/objectTextureCache').then(({ clearObjectAtlasCache }) => { clearObjectAtlasCache(); setAtlasResults({}); setAtlasGeneration((value) => value + 1) }) }}>Повторить проверку атласов</button>
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
              <label>Уровень {manifest.displayName}<select value={variants[manifest.kind]?.level ?? 1} onChange={(event) => setVariants((current) => ({ ...current, [manifest.kind]: { level: Number(event.target.value), state: current[manifest.kind]?.state ?? 'active' } }))}>{manifest.levels.map((level) => <option key={level} value={level}>{level}</option>)}</select></label>
              <label>Состояние {manifest.displayName}<select value={variants[manifest.kind]?.state ?? 'active'} onChange={(event) => setVariants((current) => ({ ...current, [manifest.kind]: { level: current[manifest.kind]?.level ?? 1, state: event.target.value as 'active' | 'construction' | 'damaged' | 'ruined' } }))}><option value="active">Действующая</option><option value="construction">Строительство</option><option value="damaged">Повреждённая</option><option value="ruined">Разрушенная</option></select></label>
              <small>Выше указан фактически выбранный runtime-вариант; он может использовать fallback.</small>
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
