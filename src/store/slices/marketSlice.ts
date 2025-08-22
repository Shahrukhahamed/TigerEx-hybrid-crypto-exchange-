import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface MarketData {
  symbol: string
  price: number
  change24h: number
  volume24h: number
  high24h: number
  low24h: number
}

interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

interface OrderBook {
  symbol: string
  bids: OrderBookEntry[]
  asks: OrderBookEntry[]
  lastUpdateId: number
}

interface Trade {
  id: string
  symbol: string
  price: number
  quantity: number
  side: 'BUY' | 'SELL'
  timestamp: number
}

interface MarketState {
  markets: MarketData[]
  orderBooks: Record<string, OrderBook>
  recentTrades: Record<string, Trade[]>
  selectedMarket: string
  loading: boolean
  error: string | null
}

const initialState: MarketState = {
  markets: [],
  orderBooks: {},
  recentTrades: {},
  selectedMarket: 'BTCUSDT',
  loading: false,
  error: null,
}

export const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setMarkets: (state, action: PayloadAction<MarketData[]>) => {
      state.markets = action.payload
    },
    updateMarket: (state, action: PayloadAction<MarketData>) => {
      const index = state.markets.findIndex(market => market.symbol === action.payload.symbol)
      if (index !== -1) {
        state.markets[index] = action.payload
      } else {
        state.markets.push(action.payload)
      }
    },
    setOrderBook: (state, action: PayloadAction<OrderBook>) => {
      state.orderBooks[action.payload.symbol] = action.payload
    },
    updateOrderBook: (state, action: PayloadAction<{ symbol: string; bids: OrderBookEntry[]; asks: OrderBookEntry[] }>) => {
      const { symbol, bids, asks } = action.payload
      if (state.orderBooks[symbol]) {
        state.orderBooks[symbol].bids = bids
        state.orderBooks[symbol].asks = asks
        state.orderBooks[symbol].lastUpdateId += 1
      }
    },
    addTrade: (state, action: PayloadAction<Trade>) => {
      const { symbol } = action.payload
      if (!state.recentTrades[symbol]) {
        state.recentTrades[symbol] = []
      }
      state.recentTrades[symbol].unshift(action.payload)
      // Keep only last 100 trades
      if (state.recentTrades[symbol].length > 100) {
        state.recentTrades[symbol] = state.recentTrades[symbol].slice(0, 100)
      }
    },
    setSelectedMarket: (state, action: PayloadAction<string>) => {
      state.selectedMarket = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
  },
})

export const {
  setMarkets,
  updateMarket,
  setOrderBook,
  updateOrderBook,
  addTrade,
  setSelectedMarket,
  setLoading,
  setError,
} = marketSlice.actions