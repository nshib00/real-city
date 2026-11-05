import { useState, type FormEvent } from 'react'
import './AccessibleMapSelection.css'
import { useGameStore } from './state/useGameStore'
import { WORLD_WRAP_TILES, wrapGridCoord } from './coordinates/iso'

// Только осмотр: выбор здесь никогда не вызывает рубку, атаку или размещение.
export function AccessibleMapSelection() {
  const [x, setX] = useState('0')
  const [y, setY] = useState('0')
  const [message, setMessage] = useState('')
  const buildings = useGameStore((state) => state.buildings)
  const monsters = useGameStore((state) => state.monsters)
  function inspect(event: FormEvent) {
    event.preventDefault()
    const tile = { x: Number(x), y: Number(y) }
    if (x.trim() === '' || y.trim() === '' || !Number.isInteger(tile.x) || !Number.isInteger(tile.y) || tile.x < 0 || tile.y < 0 || tile.x >= WORLD_WRAP_TILES || tile.y >= WORLD_WRAP_TILES) {
      setMessage(`Координаты должны быть целыми числами от 0 до ${WORLD_WRAP_TILES - 1}.`)
      return
    }
    const state = useGameStore.getState()
    state.setRelocatingBuildingId(null)
    state.setPlacementPreviewKind(null)
    state.setTool('select')
    state.selectTile(tile)
    const building = buildings.find((building) => {
      const delta = wrapGridCoord({ x: tile.x - building.tile.x, y: tile.y - building.tile.y })
      return delta.x < (building.footprintW ?? 1) && delta.y < (building.footprintH ?? 1)
    })
    const monster = monsters.find((monster) => monster.tile.x === tile.x && monster.tile.y === tile.y && monster.state !== 'dead')
    state.focusTile({ tile, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight })
    if (building) state.selectBuilding(building.id)
    else if (monster) state.selectMonster(monster.id)
    setMessage(`Выбрана клетка ${tile.x}, ${tile.y}. Сведения и действия — в инспекторе.`)
    document.getElementById('game-inspector')?.focus()
  }
  return <details className="map-coordinate-selection" onPointerDown={(event) => event.stopPropagation()} onWheel={(event) => event.stopPropagation()}>
    <summary>Выбрать клетку по координатам</summary>
    <form onSubmit={inspect} noValidate>
      <label>X<input type="number" step="1" min="0" max={WORLD_WRAP_TILES - 1} value={x} onChange={(event) => setX(event.target.value)} /></label>
      <label>Y<input type="number" step="1" min="0" max={WORLD_WRAP_TILES - 1} value={y} onChange={(event) => setY(event.target.value)} /></label>
      <button type="submit">Осмотреть клетку</button>
    </form>
    <p role="status">{message}</p>
  </details>
}
