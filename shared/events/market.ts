export type MarketEventType = 'market.order.created' | 'market.order.filled' | 'market.order.cancelled'

export type MarketOrderPayload = {
  id: string
  player_id: string
  side: 'buy' | 'sell'
  resource: string
  amount: number
  price: number
  fee: number
  status: 'open' | 'filled' | 'cancelled'
  created_at: string
  updated_at: string
}
