import { execFileSync } from 'node:child_process'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public/assets/terrain/tiles')
const output = path.join(root, 'runtime')
const variants = [
  'grass', 'forest', 'forest_thinned', 'forest_sparse', 'water', 'oil_well', 'ruins',
  'ruins_town_square', 'ruins_archive', 'ruins_mint', 'ruins_storage', 'ruins_greenhouse',
  'ruins_water_station', 'ruins_bastion', 'ruins_mechanic_workshop', 'ruins_wind_shrine',
  'ruins_ore_obelisk', 'ruins_rift_watch', 'ruins_river_lighthouse',
]
const mountains = ['ridge', 'spire', 'snowcap']
await mkdir(output, { recursive: true })

for (const name of variants) {
  execFileSync('magick', [path.join(root, `${name}.png`), '-define', 'webp:lossless=true', '-quality', '100', path.join(output, `${name}.webp`)])
}
for (const variant of mountains) {
  const name = `mountain_detail_${variant}`
  execFileSync('magick', [path.join(root, 'mountain_detail_staging', `${name}.png`), '-define', 'webp:lossless=true', '-quality', '100', path.join(output, `${name}.webp`)])
}

console.log(`Подготовлено тайлов местности: ${variants.length + mountains.length}`)
