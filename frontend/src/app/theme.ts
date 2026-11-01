import { useEffect, useSyncExternalStore } from 'react'

// Карта сохраняет светящиеся контуры; цвета DOM определяет палитра поверхности.
export const interfaceColors = { selected: '#69c7d9', focus: '#f2bf55', danger: '#ff9393', success: '#78d088' } as const
export const overlayColors = Object.fromEntries(Object.entries(interfaceColors).map(([key, value]) => [key, Number.parseInt(value.slice(1), 16)])) as Record<keyof typeof interfaceColors, number>
export type InterfaceTheme = 'classic' | 'aeolian'
const key = 'real-city.interface-theme'
const listeners = new Set<() => void>()
function readTheme(): InterfaceTheme {
  try { return localStorage.getItem(key) === 'aeolian' ? 'aeolian' : 'classic' } catch { return 'classic' }
}
let theme = readTheme()
export function setInterfaceTheme(value: InterfaceTheme) {
  theme = value
  try { localStorage.setItem(key, value) } catch { /* Переключение доступно без хранилища. */ }
  listeners.forEach((listener) => listener())
}
function subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener) } }
export function useInterfaceTheme() {
  return useSyncExternalStore(subscribe, () => theme)
}
export function useApplyInterfaceTheme() {
  const value = useInterfaceTheme()
  useEffect(() => {
    document.documentElement.dataset.interfaceTheme = value
    for (const [name, color] of Object.entries(interfaceColors)) document.documentElement.style.setProperty(`--map-${name}`, color)
    return () => {
      delete document.documentElement.dataset.interfaceTheme
      for (const name of Object.keys(interfaceColors)) document.documentElement.style.removeProperty(`--map-${name}`)
    }
  }, [value])
}
