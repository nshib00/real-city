import { Assets } from 'pixi.js'

import type { WorldTile } from '../../shared/contracts'
import type { MonsterEntity, PlacedBuilding } from '../../game/state/useGameStore'
import { buildingDrawCommands } from '../../game/renderer/objectLayer/objectDrawData'
import { objectAtlasUrls } from '../../game/renderer/objectLayer/objectTextureCache'
import { terrainPreloadUrls } from '../../game/renderer/terrainTextures'
import { resolveMonsterAtlasSource } from '../../game/renderers/monsterAssetRegistry'
import { resourceIconUrl } from '../resources/ResourceIcon'

export type InitialAssetGroup = 'terrain' | 'objects' | 'interface'
export type InitialAssetTask = {
  urls: readonly string[]
  group: InitialAssetGroup
  load: () => Promise<unknown>
}

export function initialAssetTasks(input: {
  tiles: readonly WorldTile[]
  buildings: readonly PlacedBuilding[]
  allBuildings: readonly PlacedBuilding[]
  monsters: readonly MonsterEntity[]
}): InitialAssetTask[] {
  const tasks: InitialAssetTask[] = []
  const seen = new Set<string>()
  const add = (urls: readonly string[], group: InitialAssetGroup, load: () => Promise<unknown>) => {
    if (!urls.length || urls.some((url) => seen.has(url))) return
    urls.forEach((url) => seen.add(url))
    tasks.push({ urls, group, load })
  }

  for (const url of terrainPreloadUrls(input.tiles)) {
    add([url], 'terrain', () => Assets.load(url))
  }

  for (const command of buildingDrawCommands(input.buildings, { allBuildings: input.allBuildings })) {
    if (command.textureUrl) {
      const url = command.textureUrl
      add([url], 'objects', () => Assets.load(url))
    }
  }

  for (const type of new Set(input.monsters.map((monster) => monster.type))) {
    const source = resolveMonsterAtlasSource(type)
    const urls = source && objectAtlasUrls(source)
    if (urls) {
      // Loading the spritesheet JSON through Pixi also loads its image.
      add([urls.jsonUrl, urls.imageUrl], 'objects', () => Assets.load(urls.jsonUrl))
    }
  }

  for (const id of ['population', 'coins', 'aeolian-crystal']) {
    const url = resourceIconUrl(id)
    add([url], 'interface', () => loadImage(url))
  }

  return tasks
}

function loadImage(url: string) {
  const image = new Image()
  image.src = url
  return image.decode()
}

export type InitialAssetProgress = {
  loaded: number
  failed: number
  total: number
  group: InitialAssetGroup
}

export async function loadInitialAssetTasks(
  tasks: readonly InitialAssetTask[],
  completed: Set<string>,
  onProgress: (progress: InitialAssetProgress) => void,
) {
  const pending = tasks.filter((task) => !task.urls.every((url) => completed.has(url)))
  let failed = 0
  const total = tasks.reduce((count, task) => count + task.urls.length, 0)
  const report = (group: InitialAssetGroup) => onProgress({ loaded: completed.size, failed, total, group })

  for (const group of ['terrain', 'objects', 'interface'] as const) {
    const groupTasks = pending.filter((task) => task.group === group)
    if (!groupTasks.length) continue
    let index = 0
    report(group)
    await Promise.all(Array.from({ length: Math.min(6, groupTasks.length) }, async () => {
      while (index < groupTasks.length) {
        const task = groupTasks[index++]
        try {
          await task.load()
          task.urls.forEach((url) => completed.add(url))
        } catch {
          failed += task.urls.length
        }
        report(group)
      }
    }))
  }

  return { loaded: completed.size, failed, total }
}
