import { WORLD_WRAP_TILES } from '../../game/coordinates/iso'
import type { TerritoryCell } from '../../game/territory'
import { ownershipLabels } from '../../shared/ui/ownership'

export function TerritoryLayer({ cells }: { cells: TerritoryCell[] }) {
  return <svg className="world-territory-layer" viewBox={`0 0 ${WORLD_WRAP_TILES} ${WORLD_WRAP_TILES}`} role="img" aria-label="Занятые клетки известных построек">
    {cells.map(cell => <rect key={`${cell.x}:${cell.y}`} x={cell.x} y={cell.y} width="1" height="1" data-ownership={cell.ownership}><title>{ownershipLabels[cell.ownership]}: {cell.x}, {cell.y}</title></rect>)}
  </svg>
}
