// Режим выбирает игрок в левой панели и сохраняется среди настроек интерфейса.
export function mapRenderBudget(powerSave: boolean, devicePixelRatio: number) {
  const dpr = Number.isFinite(devicePixelRatio) && devicePixelRatio > 0 ? devicePixelRatio : 1
  return { maxFPS: powerSave ? 30 : 60, resolution: powerSave ? Math.min(dpr, 1) : dpr }
}

export function observePageVisibility(onChange: (visible: boolean) => void) {
  const update = () => onChange(!document.hidden)
  document.addEventListener('visibilitychange', update)
  update()
  return () => document.removeEventListener('visibilitychange', update)
}
