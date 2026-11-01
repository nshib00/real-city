import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { ObjectMarks } from './ObjectMarks'
import { ownershipOf } from './ownership'

afterEach(cleanup)
it('определяет союз только по переданному подтверждённому составу', () => {
  const allies = new Set(['me', 'ally'])
  expect(ownershipOf('me', 'me', allies)).toBe('own')
  expect(ownershipOf('ally', 'me', allies)).toBe('ally')
  expect(ownershipOf('other', 'me', allies)).toBe('foreign')
  expect(ownershipOf(null, 'me', allies)).toBe('neutral')
})
it('сохраняет отдельные подписи владения, угрозы и выбора в одной комбинации', () => {
  render(<ObjectMarks ownership="ally" threat selected rare status="depleted" category="industry" />)
  expect(screen.getByText('Союзный объект')).toBeTruthy()
  expect(screen.getByText('Угроза')).toBeTruthy()
  expect(screen.getByText('Выбрано')).toBeTruthy()
  expect(screen.getByText('Редкий ресурс')).toBeTruthy()
  expect(screen.getByText('Истощено')).toBeTruthy()
  expect(screen.getByText('Производство')).toBeTruthy()
})
