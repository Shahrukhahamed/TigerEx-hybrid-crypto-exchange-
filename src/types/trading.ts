export interface TradingPair {
  symbol: string
  baseAsset: string
  quoteAsset: string
  status: string
  minQuantity: number
  maxQuantity: number
  stepSize: number
  minPrice: number
  maxPrice: number
  tickSize: number
  minNotional: number
  makerFee: number
  takerFee: number
  isSpotEnabled: boolean
  isMarginEnabled: boolean
  isFuturesEnabled: boolean
}

export interface Order {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  type: 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'STOP_LIMIT' | 'TAKE_PROFIT'
  quantity: number
  price?: number
  stopPrice?: number
  timeInForce: 'GTC' | 'IOC' | 'FOK'
  status: 'NEW' | 'PARTIALLY_FILLED' | 'FILLED' | 'CANCELED' | 'REJECTED'
  filledQuantity: number
  avgFillPrice: number
  createdAt: string
  updatedAt: string
}

export interface Trade {
  id: string
  symbol: string
  orderId: string
  side: 'BUY' | 'SELL'
  quantity: number
  price: number
  commission: number
  commissionAsset: string
  timestamp: string
  isMaker: boolean
}

export interface Position {
  symbol: string
  side: 'LONG' | 'SHORT'
  size: number
  entryPrice: number
  markPrice: number
  liquidationPrice: number
  unrealizedPnl: number
  realizedPnl: number
  margin: number
  leverage: number
  marginType: 'ISOLATED' | 'CROSS'
}

export interface Balance {
  asset: string
  available: number
  locked: number
  borrowed: number
  interest: number
  netAsset: number
}

export interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

export interface OrderBookData {
  symbol: string
  bids: OrderBookEntry[]
  asks: OrderBookEntry[]
  lastUpdateId: number
}

export interface MarketData {
  symbol: string
  price: number
  priceChange: number
  priceChangePercent: number
  highPrice: number
  lowPrice: number
  volume: number
  quoteVolume: number
  openPrice: number
  prevClosePrice: number
  weightedAvgPrice: number
  count: number
  timestamp: number
}

export interface Kline {
  openTime: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  closeTime: number
  quoteAssetVolume: number
  numberOfTrades: number
  takerBuyBaseAssetVolume: number
  takerBuyQuoteAssetVolume: number
}