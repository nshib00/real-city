// Политика только визуального движения. Серверные таймеры и новые координаты не меняются.
export function worldMotionEnabled() {
  return document.documentElement.dataset.uiEffects !== 'off'
    && !(typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches)
}

export function observeWorldMotion(changed: () => void) {
  const media = typeof matchMedia === 'function' ? matchMedia('(prefers-reduced-motion: reduce)') : null
  const observer = new MutationObserver(changed)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-ui-effects'] })
  media?.addEventListener('change', changed)
  return () => { observer.disconnect(); media?.removeEventListener('change', changed) }
}
