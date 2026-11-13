import { access, readFile, readdir, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { isRuntimeAsset } from './runtime-assets.mjs'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const assetsDir = path.join(root, 'public', 'assets')
const maxTotalBytes = Number(process.env.ASSET_BUDGET_TOTAL_MB ?? 900) * 1024 * 1024
const maxFileBytes = Number(process.env.ASSET_BUDGET_FILE_MB ?? 25) * 1024 * 1024
const maxGlbBytes = Number(process.env.ASSET_BUDGET_GLB_MB ?? 450) * 1024 * 1024
const maxPngBytes = Number(process.env.ASSET_BUDGET_PNG_MB ?? 420) * 1024 * 1024
const audioDir = path.join(assetsDir, 'audio')
const audioFamilies = new Set(['ui', 'economy', 'build', 'world', 'combat', 'social', 'ambience', 'music'])
const audioFamilyLimit = 150 * 1024
const audioTotalLimit = 5 * 1024 * 1024
const audioPreloadLimit = 300 * 1024

const files = (await walk(assetsDir)).filter((file) => isRuntimeAsset(path.relative(assetsDir, file.path)))
const totalBytes = files.reduce((sum, file) => sum + file.size, 0)
const glbBytes = files.filter((file) => file.path.endsWith('.glb')).reduce((sum, file) => sum + file.size, 0)
const pngBytes = files.filter((file) => file.path.endsWith('.png')).reduce((sum, file) => sum + file.size, 0)
const oversized = files.filter((file) => file.size > maxFileBytes).sort((left, right) => right.size - left.size)

if (totalBytes > maxTotalBytes || glbBytes > maxGlbBytes || pngBytes > maxPngBytes || oversized.length > 0) {
  console.error(`Runtime asset budget exceeded: ${formatBytes(totalBytes)} / ${formatBytes(maxTotalBytes)}.`)
  console.error(`GLB: ${formatBytes(glbBytes)} / ${formatBytes(maxGlbBytes)}; PNG: ${formatBytes(pngBytes)} / ${formatBytes(maxPngBytes)}.`)
  for (const file of oversized.slice(0, 20)) {
    console.error(`Oversized asset: ${path.relative(root, file.path)} (${formatBytes(file.size)} / ${formatBytes(maxFileBytes)})`)
  }
  process.exit(1)
}

console.log(`Runtime asset budget ok: ${formatBytes(totalBytes)} across ${files.length} files; GLB ${formatBytes(glbBytes)}, PNG ${formatBytes(pngBytes)}.`)

const resourceIconsDir = path.join(assetsDir, 'resources', 'icons')
const resourceIconManifest = JSON.parse(await readFile(path.join(resourceIconsDir, 'manifest.json'), 'utf8'))
for (const resource of resourceIconManifest.resources) {
  const runtimeIcon = path.join(resourceIconsDir, 'runtime', resource.file.replace(/\.png$/, '.webp'))
  try {
    await access(runtimeIcon)
  } catch {
    console.error(`Missing runtime resource icon: ${path.relative(root, runtimeIcon)}`)
    process.exit(1)
  }
}

const audioFiles = (await walk(audioDir)).filter((file) => /\.(mp3|m4a|ogg|opus|wav)$/i.test(file.path))
const audioByPath = new Map(audioFiles.map((file) => [path.relative(audioDir, file.path).split(path.sep).join('/'), file]))
const audioTotal = audioFiles.reduce((sum, file) => sum + file.size, 0)
const familySizes = new Map()
const audioErrors = []
for (const [relativePath, file] of audioByPath) {
  const family = relativePath.split('/')[0].split('.')[0]
  if (!audioFamilies.has(family)) {
    audioErrors.push(`Unknown audio family: ${relativePath}`)
    continue
  }
  if (family !== 'ambience' && family !== 'music') {
    const soundGroup = path.basename(relativePath).split('.').slice(0, 2).join('.')
    familySizes.set(soundGroup, (familySizes.get(soundGroup) ?? 0) + file.size)
  }
}
for (const [family, bytes] of familySizes) {
  const limit = family === 'combat.monster' ? 600 * 1024 : audioFamilyLimit
  if (bytes > limit) audioErrors.push(`${family}: ${formatBytes(bytes)} / ${formatBytes(limit)}`)
}
const musicBytes = [...audioByPath].filter(([name]) => name.startsWith('music/')).reduce((sum, [, file]) => sum + file.size, 0)
if (musicBytes > 5 * 1024 * 1024) audioErrors.push(`Music: ${formatBytes(musicBytes)} / 5 MB`)
if (audioTotal > audioTotalLimit) audioErrors.push(`Audio catalog: ${formatBytes(audioTotal)} / ${formatBytes(audioTotalLimit)}`)

const preloadManifest = JSON.parse(await readFile(path.join(audioDir, 'preload.json'), 'utf8'))
if (!Array.isArray(preloadManifest.files) || !preloadManifest.files.every((file) => typeof file === 'string')) {
  audioErrors.push('audio/preload.json must contain a files array of relative paths')
}
const preloadPaths = Array.isArray(preloadManifest.files) ? preloadManifest.files : []
const uniquePreloadPaths = new Set(preloadPaths)
if (uniquePreloadPaths.size !== preloadPaths.length) audioErrors.push('audio/preload.json has duplicate paths')
let preloadBytes = 0
for (const relativePath of uniquePreloadPaths) {
  if (typeof relativePath !== 'string' || !audioByPath.has(relativePath)) {
    audioErrors.push(`Missing audio preload asset: ${String(relativePath)}`)
    continue
  }
  preloadBytes += audioByPath.get(relativePath).size
}
if (preloadBytes > audioPreloadLimit) audioErrors.push(`Audio preload: ${formatBytes(preloadBytes)} / ${formatBytes(audioPreloadLimit)}`)
if (audioErrors.length) {
  for (const error of audioErrors) console.error(error)
  process.exit(1)
}
console.log(`Audio budget ok: ${formatBytes(audioTotal)} total; ${formatBytes(preloadBytes)} preload; ${audioFiles.length} files.`)

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const result = []
  for (const entry of entries) {
    const entryPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      result.push(...await walk(entryPath))
    } else if (entry.isFile()) {
      const info = await stat(entryPath)
      result.push({ path: entryPath, size: info.size })
    }
  }
  return result
}

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024) {
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }
  if (bytes >= 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }
  return `${(bytes / 1024).toFixed(1)} KB`
}
