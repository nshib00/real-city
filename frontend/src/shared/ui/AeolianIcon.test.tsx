// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { AeolianIcon } from './AeolianIcon'
import { iconPaths } from './iconPaths'
import { iconPaths16 } from './iconPaths16'
afterEach(cleanup)
it('has a separately drawn small variant for every functional icon', () => {
  expect(Object.keys(iconPaths16).sort()).toEqual(Object.keys(iconPaths).sort())
  const { container, rerender } = render(<AeolianIcon name="repair" size={16} />)
  expect(container.querySelector('svg')?.getAttribute('viewBox')).toBe('0 0 16 16')
  expect(container.querySelector('path')?.getAttribute('d')).toBe(iconPaths16.repair)
  rerender(<AeolianIcon name="repair" size={24} />)
  expect(container.querySelector('path')?.getAttribute('d')).toBe(iconPaths.repair)
})

it('keeps decorative icons silent and labels meaningful icons', () => {
  const { container, rerender } = render(<AeolianIcon name="repair" size={16} />)
  expect(container.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')
  expect(container.querySelector('svg')?.getAttribute('width')).toBe('16')
  rerender(<AeolianIcon name="repair" label="Ремонт" />)
  expect(screen.getByRole('img', { name: 'Ремонт' }).getAttribute('aria-hidden')).toBeNull()
})

it('falls back without leaking an unknown key into markup', () => {
  const { container, rerender } = render(<AeolianIcon name={'<script>unknown</script>'} label="Предмет" />)
  expect(container.querySelector('path')?.getAttribute('d')).toBe(iconPaths.shortage)
  expect(container.querySelector('script')).toBeNull()
  rerender(<AeolianIcon name="toString" label="Предмет" />)
  expect(container.querySelector('path')?.getAttribute('d')).toBe(iconPaths.shortage)
})
