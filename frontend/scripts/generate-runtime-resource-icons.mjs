import { execFileSync } from 'node:child_process'
import { mkdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const iconsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public/assets/resources/icons')
const outputDir = path.join(iconsDir, 'runtime')
const manifest = JSON.parse(await readFile(path.join(iconsDir, 'manifest.json'), 'utf8'))
await mkdir(outputDir, { recursive: true })

for (const resource of manifest.resources) {
  if (!/^[a-z0-9_-]+\.png$/.test(resource.file)) throw new Error(`Недопустимое имя значка: ${resource.file}`)
  execFileSync('magick', [
    path.join(iconsDir, resource.file),
    '-resize', '96x96', '-strip', '-quality', '88',
    path.join(outputDir, resource.file.replace(/\.png$/, '.webp')),
  ])
}

console.log(`Подготовлено значков: ${manifest.resources.length}`)
