import { useEffect } from 'react'

/** Экранная клавиатура может уменьшить visualViewport, не меняя CSS dvh. */
export function useAuthViewport() {
  useEffect(() => {
    const viewport = window.visualViewport
    let frame = 0
    const resize = () => {
      document.documentElement.style.setProperty('--auth-visible-height', `${viewport?.height ?? window.innerHeight}px`)
      document.documentElement.style.setProperty('--auth-visible-top', `${viewport?.offsetTop ?? 0}px`)
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const target = document.activeElement
        if (target instanceof HTMLElement && target.closest('.auth-form')) target.scrollIntoView?.({ block: 'nearest' })
      })
    }
    resize()
    window.addEventListener('resize', resize)
    viewport?.addEventListener('resize', resize)
    viewport?.addEventListener('scroll', resize)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      viewport?.removeEventListener('resize', resize)
      viewport?.removeEventListener('scroll', resize)
      document.documentElement.style.removeProperty('--auth-visible-height')
      document.documentElement.style.removeProperty('--auth-visible-top')
    }
  }, [])
}
