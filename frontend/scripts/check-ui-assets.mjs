import { readFile, readdir, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const ui = path.join(root, 'public/assets/ui')
const icons = JSON.parse(await readFile(path.join(ui, 'icons/manifest.json'), 'utf8'))
const resources = JSON.parse(await readFile(path.join(ui, 'resources/manifest.json'), 'utf8'))
const catalog = await readFile(path.join(root, '../shared/catalog/resources.ts'), 'utf8')
const expected = [...catalog.matchAll(/\{ id: '([^']+)'/g)].map((match) => match[1])
const errors = []
const ids = resources.resources.map((item) => item.id)
if (new Set(ids).size !== ids.length || expected.some((id) => !ids.includes(id)) || ids.some((id) => !expected.includes(id))) errors.push('Resource catalog coverage mismatch')
const required = [...icons.icons.flatMap((id) => [`icons/${id}.svg`, `icons/small/${id}.svg`]), ...resources.resources.map((item) => `resources/${item.file}`), 'ornaments/craft.svg', 'ornaments/technology.svg']
let total = 0
const shapes = new Set()
for (const relative of required) {
  const file = path.join(ui, relative)
  const svg = await readFile(file, 'utf8')
  const bytes = (await stat(file)).size
  total += bytes
  if (bytes > 4096) errors.push(`SVG exceeds 4 KB: ${relative}`)
  // Разрешён только небольшой декларативный SVG: без ссылок, CSS, шрифтов и событий.
  if (!svg.startsWith('<svg ') || !svg.includes('xmlns="http://www.w3.org/2000/svg"') || !/viewBox="0 0 (16 16|24 24|32 32)"/.test(svg)) errors.push(`Invalid canvas: ${relative}`)
  if (/<!|<\?|\b(?:href|style|on\w+)\s*=|url\s*\(|@|javascript:|data:/i.test(svg)) errors.push(`Unsafe SVG: ${relative}`)
  for (const tag of svg.matchAll(/<\/?([\w:-]+)/g)) {
    if (!['svg', 'g', 'path'].includes(tag[1])) errors.push(`Forbidden element ${tag[1]}: ${relative}`)
  }
  if (relative.startsWith('icons/')) {
    if (!svg.includes('stroke="currentColor"')) errors.push(`Missing currentColor: ${relative}`)
    if (shapes.has(svg)) errors.push(`Duplicate geometry: ${relative}`)
    shapes.add(svg)
  }
}
if (total > 128 * 1024) errors.push(`UI exceeds 128 KB: ${total}`)
let startTotal = 0
for (const [file, limit] of [['settlement.svg', 12], ['settlement-480.webp', 20], ['settlement-960.webp', 40]]) {
  const bytes = (await stat(path.join(ui, 'start', file))).size
  startTotal += bytes
  if (bytes > limit * 1024) errors.push(`Start scene exceeds ${limit} KiB: ${file}`)
}
if (startTotal > 72 * 1024) errors.push(`Start scene exceeds 72 KiB: ${startTotal}`)
// Потребители не должны незаметно возвращать старые знаки.
async function checkConsumers(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name)
    if (entry.isDirectory()) await checkConsumers(file)
    else if (/\.tsx?$/.test(file) && (await readFile(file, 'utf8')).includes("from 'lucide-react'")) errors.push(`Legacy icon import: ${file}`)
  }
}
await checkConsumers(path.join(root, 'src'))
if (errors.length) { console.error(errors.join('\n')); process.exit(1) }
console.log(`UI assets ok: ${icons.icons.length} functional icons, ${ids.length} resources, 2 ornaments; ${(total / 1024).toFixed(1)} KB / 128 KB.`)
console.log(`Start scene ok: ${(startTotal / 1024).toFixed(1)} KiB / 72 KiB.`)
