import { useEffect } from 'react'

const regions = ['game-map', 'game-tools', 'game-build-menu', 'game-inspector', 'game-events']

export function InterfaceNavigation() {
  useEffect(() => {
    const navigate = (event: KeyboardEvent) => {
      if (event.key !== 'F6' || event.ctrlKey || event.altKey || event.metaKey || document.querySelector('[aria-modal="true"]')) return
      const nodes = regions.map((id) => document.getElementById(id)).filter((node): node is HTMLElement => Boolean(node && !node.closest('[inert], [hidden]')))
      const current = nodes.findIndex((node) => node === document.activeElement || node.contains(document.activeElement))
      const next = current < 0 ? 0 : (current + (event.shiftKey ? -1 : 1) + nodes.length) % nodes.length
      event.preventDefault()
      nodes[next]?.focus()
    }
    const viewport = window.visualViewport
    const resize = () => {
      document.documentElement.style.setProperty('--visible-height', `${viewport?.height ?? window.innerHeight}px`)
      document.documentElement.style.setProperty('--visible-top', `${viewport?.offsetTop ?? 0}px`)
    }
    resize()
    window.addEventListener('keydown', navigate)
    window.addEventListener('resize', resize)
    viewport?.addEventListener('resize', resize)
    viewport?.addEventListener('scroll', resize)
    return () => {
      window.removeEventListener('keydown', navigate)
      window.removeEventListener('resize', resize)
      viewport?.removeEventListener('resize', resize)
      viewport?.removeEventListener('scroll', resize)
      document.documentElement.style.removeProperty('--visible-height')
      document.documentElement.style.removeProperty('--visible-top')
    }
  }, [])
  return <nav className="interface-links" aria-label="Переходы по интерфейсу">
    {regions.filter((id) => id !== 'game-build-menu').map((id, index) => <a key={id} href={`#${id}`}>{['К карте', 'К инструментам', 'К инспектору', 'К событиям'][index]}</a>)}
  </nav>
}
