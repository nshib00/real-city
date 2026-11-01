import { useEffect, useState } from 'react'
import type { useVisibleChunks } from './useVisibleChunks'

export function MapEntryStatus({ query }: { query: ReturnType<typeof useVisibleChunks> }) {
  const [slow, setSlow] = useState(false)
  const [renderer, setRenderer] = useState<'loading' | 'ready' | 'failed'>('loading')
  useEffect(() => {
    const timer = window.setTimeout(() => setSlow(true), 8000)
    const ready = () => setRenderer('ready')
    const failed = () => setRenderer('failed')
    window.addEventListener('real-city:map-ready', ready)
    window.addEventListener('real-city:map-failed', failed)
    return () => { clearTimeout(timer); window.removeEventListener('real-city:map-ready', ready); window.removeEventListener('real-city:map-failed', failed) }
  }, [])
  if (query.data && renderer === 'ready') return null
  return <section className="map-entry-status" onPointerDown={event => event.stopPropagation()} onWheel={event => event.stopPropagation()} aria-label="Подключение карты" role={query.isError || renderer === 'failed' ? 'alert' : 'status'}>
    {renderer === 'failed' ? <><p>Не удалось запустить графику карты. Проверьте поддержку WebGL и аппаратное ускорение браузера.</p><button type="button" onClick={() => { setRenderer('loading'); window.dispatchEvent(new Event('real-city:retry-renderer')) }}>Повторить запуск карты</button></> : query.isError ? <><p>Не удалось загрузить участок мира.</p><button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>Повторить загрузку карты</button></> : <p>{!query.data ? 'Загружаем участок мира…' : 'Подготавливаем графику карты…'}{slow ? ' Соединение занимает больше времени. Можно подождать.' : ''}</p>}
  </section>
}
