import { useEffect } from 'react'
import { audioManager } from './AudioManager'
import { startMusic, updateMusicVisibility } from './music'

export function AudioProvider(): null {
  useEffect(() => {
    const unlock = () => { startMusic(); void audioManager.unlock().then((ready) => { if (ready) void audioManager.preload('ui.click') }) }
    const visibility = () => { audioManager.setHidden(document.hidden); updateMusicVisibility() }
    window.addEventListener('pointerdown', unlock, { once: true, capture: true })
    window.addEventListener('keydown', unlock, { once: true, capture: true })
    document.addEventListener('visibilitychange', visibility)
    return () => {
      window.removeEventListener('pointerdown', unlock, true)
      window.removeEventListener('keydown', unlock, true)
      document.removeEventListener('visibilitychange', visibility)
    }
  }, [])
  return null
}
