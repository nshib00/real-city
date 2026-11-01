import { useEffect, useState } from 'react'
import { mapTextureReadiness } from '../../game/renderer/PixiStage'

export function MapAssetStatus() {
  const [counts, setCounts] = useState(() => mapTextureReadiness.diagnostics())
  useEffect(() => {
    const timer = window.setInterval(() => {
      const next = mapTextureReadiness.diagnostics()
      setCounts((previous) => previous.loading === next.loading && previous.failed === next.failed ? previous : next)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [])
  if (!counts.loading && !counts.failed) return null
  return <section className="map-asset-status" aria-label="Графика карты">
    {counts.loading ? <span>Загрузка графики: {counts.loading}</span> : null}
    {counts.failed ? <><span role="status">Не удалось загрузить часть графики. Карта использует упрощённые объекты.</span><button type="button" onClick={() => window.dispatchEvent(new Event('real-city:retry-map-assets'))}>Повторить загрузку графики</button></> : null}
  </section>
}
