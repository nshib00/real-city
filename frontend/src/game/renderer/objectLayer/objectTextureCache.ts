import { Assets } from 'pixi.js'

import type { RuntimeAssetManifest } from '../../renderers/assetManifestTypes'

export type ObjectAtlasFrameMap = Record<string, unknown>

export type ObjectAtlasSource = {
  assetId: string
  basePath: string
  atlas?: RuntimeAssetManifest['atlas']
  revision?: string
  fallbackUrl?: string | null
  requiredFrames?: readonly string[]
}

export type LoadedObjectAtlas = {
  status: 'atlas'
  cacheKey: string
  assetId: string
  imageUrl: string
  jsonUrl: string
  frameNames: readonly string[]
  frameCount: number
  missingFrames: readonly string[]
  resource: unknown
}

export type FallbackObjectAtlas = {
  status: 'fallback'
  cacheKey: string
  assetId: string
  fallbackUrl: string | null
  reason: 'missing-atlas' | 'load-failed'
  error?: unknown
}

export type ObjectAtlasLoadResult = LoadedObjectAtlas | FallbackObjectAtlas

const atlasLoads = new Map<string, Promise<ObjectAtlasLoadResult>>()

export function objectAtlasCacheKey(source: Pick<ObjectAtlasSource, 'assetId' | 'atlas' | 'revision'>) {
  const revision = source.atlas?.revision ?? source.revision ?? 'unversioned'
  return `${source.assetId}@${revision}`
}

export function objectAtlasUrls(source: Pick<ObjectAtlasSource, 'basePath' | 'atlas' | 'revision'>) {
  if (!source.atlas) {
    return null
  }

  const revision = source.atlas.revision ?? source.revision
  return {
    imageUrl: withOptionalRevision(`${source.basePath}/${source.atlas.image}`, revision),
    jsonUrl: withOptionalRevision(`${source.basePath}/${source.atlas.json}`, revision),
  }
}

export function loadObjectAtlas(source: ObjectAtlasSource): Promise<ObjectAtlasLoadResult> {
  const cacheKey = objectAtlasCacheKey(source)
  const existing = atlasLoads.get(cacheKey)
  if (existing) {
    return existing
  }

  const promise = loadObjectAtlasUncached(source, cacheKey)
  atlasLoads.set(cacheKey, promise)
  return promise
}

export function clearObjectAtlasCache() {
  atlasLoads.clear()
}

async function loadObjectAtlasUncached(source: ObjectAtlasSource, cacheKey: string): Promise<ObjectAtlasLoadResult> {
  const urls = objectAtlasUrls(source)
  if (!urls) {
    return {
      status: 'fallback',
      cacheKey,
      assetId: source.assetId,
      fallbackUrl: source.fallbackUrl ?? null,
      reason: 'missing-atlas',
    }
  }

  try {
    // Pixi's spritesheet loader fetches the image declared in meta.image.
    // Loading it separately here duplicates a large GPU texture.
    const jsonResource = await Assets.load(urls.jsonUrl)
    const frameNames = extractAtlasFrameNames(jsonResource)
    return {
      status: 'atlas',
      cacheKey,
      assetId: source.assetId,
      imageUrl: urls.imageUrl,
      jsonUrl: urls.jsonUrl,
      frameNames,
      frameCount: frameNames.length,
      missingFrames: missingRequiredFrames(source.requiredFrames ?? [], frameNames),
      resource: jsonResource,
    }
  } catch (error) {
    return {
      status: 'fallback',
      cacheKey,
      assetId: source.assetId,
      fallbackUrl: source.fallbackUrl ?? null,
      reason: 'load-failed',
      error,
    }
  }
}

export function extractAtlasFrameNames(resource: unknown): string[] {
  const frames = atlasFramesFromResource(resource)
  if (!frames) {
    return []
  }

  if (Array.isArray(frames)) {
    return frames
      .map((frame) => frameNameFromArrayEntry(frame))
      .filter((frameName): frameName is string => Boolean(frameName))
  }

  return Object.keys(frames)
}

function atlasFramesFromResource(resource: unknown): unknown {
  if (!isRecord(resource)) {
    return null
  }

  if ('frames' in resource) {
    return resource.frames
  }

  const data = resource.data
  if (isRecord(data) && 'frames' in data) {
    return data.frames
  }

  const textureData = resource.textureSource
  if (isRecord(textureData) && 'frames' in textureData) {
    return textureData.frames
  }

  return null
}

function frameNameFromArrayEntry(frame: unknown) {
  if (!isRecord(frame)) {
    return null
  }

  if (typeof frame.filename === 'string') {
    return frame.filename
  }
  if (typeof frame.name === 'string') {
    return frame.name
  }
  if (typeof frame.id === 'string') {
    return frame.id
  }
  return null
}

function missingRequiredFrames(requiredFrames: readonly string[], availableFrames: readonly string[]) {
  const available = new Set(availableFrames)
  return requiredFrames.filter((frame) => !available.has(frame))
}

function withOptionalRevision(url: string, revision?: string) {
  return revision ? `${url}?v=${revision}` : url
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
