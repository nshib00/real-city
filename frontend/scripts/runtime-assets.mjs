import path from 'node:path'

const runtimeGlbDirectories = [
  'buildings/center/town_hall/',
  'buildings/housing/stone_house/',
  'buildings/housing/villa/',
  'buildings/industry/',
]

export function isRuntimeAsset(relativePath) {
  const normalized = relativePath.split(path.sep).join('/')
  const segments = normalized.split('/')
  if (segments.some((segment) => segment === 'preview' || segment.startsWith('backup_') || segment.endsWith('_test'))) return false
  const fileName = segments.at(-1).toLowerCase()
  if (/^monsters\/[^/]+\/[^/]+_preview\.png$/.test(normalized)) return true
  if (normalized.includes('.backup-') || /\.blend1?$/.test(fileName)) return false
  if (/(?:^|[_-])(?:contact_sheet|review|preview)(?:[_-]|\.)/.test(fileName)) return false
  if (fileName.endsWith('.glb')) {
    return !fileName.endsWith('_levels.glb') && runtimeGlbDirectories.some((directory) => normalized.startsWith(directory))
  }
  if (/^resources\/icons\/[^/]+\.png$/.test(normalized)) return false
  if (normalized.startsWith('terrain/tiles/') && fileName.endsWith('.png')) return false
  return true
}
