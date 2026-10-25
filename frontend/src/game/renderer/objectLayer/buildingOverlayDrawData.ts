import { fieldCropSpec } from '../../../features/fields/fieldGrowth'
import type { BuildingAnimationKey, AssetAnimationManifest } from '../../renderers/assetManifestTypes'
import { buildingOverlayKeys, buildingVisualState } from '../../renderers/buildingAnimationRegistry'
import type { BuildingDrawCommand } from './objectDrawData'
import { animationFrameIndex, animationPhaseOffsetMs, shouldRenderBuildingOverlay } from './animationClock'

export type BuildingOverlayDrawCommand = {
  id: string
  buildingId: string
  key: BuildingAnimationKey
  animation: AssetAnimationManifest
  tile: { x: number; y: number }
  anchor: { x: number; y: number }
  size: { width: number; height: number }
  sortKey: number
  frameIndex: number
  phase: number
  selected: boolean
  isField: boolean
}

const SHARED_OVERLAY_ANIMATIONS: Partial<Record<BuildingAnimationKey, AssetAnimationManifest>> = {
  construction_dust: {
    type: 'shared_overlay',
    id: 'construction_dust',
    fps: 10,
    frames: 16,
    loop: true,
  },
  damaged_smoke: {
    type: 'shared_overlay',
    id: 'smoke_small',
    fps: 6,
    frames: 18,
    loop: true,
  },
  damaged_fire: {
    type: 'shared_overlay',
    id: 'fire_small',
    fps: 10,
    frames: 12,
    loop: true,
  },
  ready_to_collect: {
    type: 'shared_overlay',
    id: 'ready_marker',
    fps: 4,
    frames: 12,
    loop: true,
  },
  under_attack: {
    type: 'shared_overlay',
    id: 'hit_flash',
    fps: 12,
    frames: 8,
    loop: false,
  },
}

export function buildingOverlayDrawCommands(
  buildings: readonly BuildingDrawCommand[],
  options: {
    zoom: number
    nowMs: number
    viewerId?: string | null
  },
): BuildingOverlayDrawCommand[] {
  return buildings.flatMap((command) => buildingOverlayDrawCommandsFor(command, options))
}

export function buildingOverlayDrawCommandsFor(
  command: BuildingDrawCommand,
  options: {
    zoom: number
    nowMs: number
    viewerId?: string | null
  },
): BuildingOverlayDrawCommand[] {
  const manifestOverlays = new Map(buildingVisualState(command.building).overlays.map((overlay) => [overlay.key, overlay.animation]))

  return runtimeOverlayKeys(command)
    .filter((key) => options.viewerId === undefined || (key !== 'ready_to_collect' && key !== 'working') || command.building.owner === options.viewerId)
    .map((key) => ({ key, animation: manifestOverlays.get(key) ?? SHARED_OVERLAY_ANIMATIONS[key] }))
    .filter((item): item is { key: BuildingAnimationKey; animation: AssetAnimationManifest } => Boolean(item.animation))
    .filter(({ key }) => shouldRenderBuildingOverlay(key, options.zoom, command.selected))
    .map(({ key, animation }) => {
      const frameDuration = animation.frames && animation.fps > 0 ? animation.frames * (1000 / animation.fps) : 1000
      const phaseOffset = animationPhaseOffsetMs(`${command.id}:${key}`, frameDuration)
      const frameIndex = animationFrameIndex({
        nowMs: options.nowMs,
        fps: animation.fps,
        frames: animation.frames,
        loop: animation.loop,
        phaseOffsetMs: phaseOffset,
      })
      const frameCount = Math.max(1, animation.frames ?? 1)

      return {
        id: `${command.id}:${key}`,
        buildingId: command.id,
        key,
        animation,
        tile: command.tile,
        anchor: command.anchor,
        size: command.size,
        sortKey: command.sortKey + 0.5,
        frameIndex,
        phase: frameIndex / frameCount,
        selected: command.selected,
        isField: Boolean(fieldCropSpec(command.building.kind)),
      }
    })
}

function runtimeOverlayKeys(command: BuildingDrawCommand): BuildingAnimationKey[] {
  const keys = buildingOverlayKeys(command.building)
  const runtime = command.building as { underAttack?: boolean; combatState?: string; attackedAt?: number | null }

  if (runtime.underAttack || runtime.combatState === 'under_attack' || runtime.attackedAt) {
    keys.push('under_attack')
  }

  const manifestOverlayKeys = new Set(buildingVisualState(command.building).overlays.map((overlay) => overlay.key))
  return keys.filter((key) => key !== 'working' || manifestOverlayKeys.has('working'))
}
