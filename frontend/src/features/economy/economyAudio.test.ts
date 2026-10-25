import { beforeEach, describe, expect, it, vi } from 'vitest'

import { playUiSound } from '../../audio/playUiSound'
import type { InventoryResponse } from '../../shared/api/economy'
import { fieldHarvestSound, playConfirmedCoinChange, playConfirmedRareReward, productionMaterialVariant, resourceGatherSound } from './economyAudio'

vi.mock('../../audio/playUiSound', () => ({ playUiSound: vi.fn() }))

function inventory(coins: number, rare = 0): InventoryResponse {
  return { player_id: 'p1', coin_capacity: 2000, updated_at: '', items: [
    { resource: 'coins', amount: coins }, { resource: 'super-seeds', amount: rare },
  ] }
}

describe('подтверждённые звуки экономики', () => {
  beforeEach(() => vi.clearAllMocks())

  it('не озвучивает начальную загрузку и воспроизводит один сигнал на изменение монет', () => {
    playConfirmedCoinChange(undefined, inventory(100))
    playConfirmedCoinChange(inventory(100), inventory(100))
    expect(playUiSound).not.toHaveBeenCalled()
    playConfirmedCoinChange(inventory(100), inventory(125))
    playConfirmedCoinChange(inventory(125), inventory(90))
    expect(playUiSound).toHaveBeenNthCalledWith(1, 'economy.coin.earned')
    expect(playUiSound).toHaveBeenNthCalledWith(2, 'economy.coin.spent')
  })

  it('различает редкий прирост и обычный урожай по ответу операции', () => {
    playConfirmedRareReward(inventory(100), inventory(150))
    expect(playUiSound).not.toHaveBeenCalled()
    playConfirmedRareReward(inventory(100, 0), inventory(100, 2))
    expect(playUiSound).toHaveBeenCalledWith('economy.reward.rare')
  })

  it('выбирает материал по типу поля и реальному ресурсу узла', () => {
    expect(fieldHarvestSound('mushroom_grove')).toBe('economy.harvest.mushroom')
    expect(fieldHarvestSound('sugar_bed')).toBe('economy.harvest.cane')
    expect(fieldHarvestSound('crystal_greenhouse')).toBe('economy.harvest.crystal')
    expect(fieldHarvestSound('flax_field')).toBe('economy.harvest.field')
    expect(resourceGatherSound('resin')).toBe('economy.gather.resin')
    expect(resourceGatherSound('iron_ore')).toBe('economy.gather.ore')
    expect(productionMaterialVariant('forge')).toBe(2)
    expect(productionMaterialVariant('weaving_yard')).toBe(3)
  })
})
