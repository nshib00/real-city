const MAP_OBJECT_Z_INDEX_BASE = 100000

export function mapObjectZIndex(screenY: number) {
  return Math.round(screenY + MAP_OBJECT_Z_INDEX_BASE)
}
