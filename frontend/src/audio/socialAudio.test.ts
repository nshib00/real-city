import { describe, expect, it } from 'vitest'
import { isMention } from './socialAudio'

describe('упоминание в чате', () => {
  it('узнаёт отдельное имя без ложного совпадения с длинным словом', () => {
    expect(isMention('Привет, @Алиса!', ['Алиса'])).toBe(true)
    expect(isMention('Привет, @Алиса123', ['Алиса'])).toBe(false)
    expect(isMention('@Игрок [1], заходи', ['Игрок [1]'])).toBe(true)
  })
})
