import { readdir, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const assetsDir = path.join(root, 'public', 'assets')
const maxTotalBytes = Number(process.env.ASSET_BUDGET_TOTAL_MB ?? 1200) * 1024 * 1024
const maxFileBytes = Number(process.env.ASSET_BUDGET_FILE_MB ?? 25) * 1024 * 1024

const files = (await walk(assetsDir)).filter((file) => isRuntimeAsset(path.relative(assetsDir, file.path)))
const totalBytes = files.reduce((sum, file) => sum + file.size, 0)
const oversized = files.filter((file) => file.size > maxFileBytes).sort((left, right) => right.size - left.size)

if (totalBytes > maxTotalBytes || oversized.length > 0) {
  console.error(`Runtime asset budget exceeded: ${formatBytes(totalBytes)} / ${formatBytes(maxTotalBytes)}.`)
  for (const file of oversized.slice(0, 20)) {
    console.error(`Oversized asset: ${path.relative(root, file.path)} (${formatBytes(file.size)} / ${formatBytes(maxFileBytes)})`)
  }
  process.exit(1)
}

console.log(`Runtime asset budget ok: ${formatBytes(totalBytes)} across ${files.length} files.`)

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

function isRuntimeAsset(relativePath) {
  const normalized = relativePath.split(path.sep).join('/')
  const fileName = path.basename(normalized).toLowerCase()
  if (normalized.includes('.backup-')) {
    return false
  }
  if (fileName.endsWith('.blend') || fileName.endsWith('.blend1') || fileName.endsWith('.glb')) {
    return false
  }
  if (fileName.includes('contact_sheet') || fileName.includes('review') || fileName.includes('preview')) {
    return false
  }
  return true
}
