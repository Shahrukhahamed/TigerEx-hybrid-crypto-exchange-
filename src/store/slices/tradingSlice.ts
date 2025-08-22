import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Order {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  type: string
  quantity: number
  price: number
  status: string
  createdAt: string
}

interface Position {
  symbol: string
  side: 'LONG' | 'SHORT'
  size: number
  entryPrice: number
  markPrice: number
  unrealizedPnl: number
  leverage: number
}

interface Balance {
  asset: string
  available: number
  locked: number
  total: number
}

interface TradingState {
  selectedPair: string
  orderType: string
  orderSide: 'BUY' | 'SELL'
  orders: Order[]
  positions: Position[]
  balances: Balance[]
  loading: boolean
  error: string | null
}

const initialState: TradingState = {
  selectedPair: 'BTCUSDT',
  orderType: 'LIMIT',
  orderSide: 'BUY',
  orders: [],
  positions: [],
  balances: [],
  loading: false,
  error: null,
}

export const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    setSelectedPair: (state, action: PayloadAction<string>) => {
      state.selectedPair = action.payload
    },
    setOrderType: (state, action: PayloadAction<string>) => {
      state.orderType = action.payload
    },
    setOrderSide: (state, action: PayloadAction<'BUY' | 'SELL'>) => {
      state.orderSide = action.payload
    },
    setOrders: (state, action: PayloadAction<Order[]>) => {
      state.orders = action.payload
    },
    addOrder: (state, action: PayloadAction<Order>) => {
      state.orders.unshift(action.payload)
    },
    updateOrder: (state, action: PayloadAction<Order>) => {
      const index = state.orders.findIndex(order => order.id === action.payload.id)
      if (index !== -1) {
        state.orders[index] = action.payload
      }
    },
    removeOrder: (state, action: PayloadAction<string>) => {
      state.orders = state.orders.filter(order => order.id !== action.payload)
    },
    setPositions: (state, action: PayloadAction<Position[]>) => {
      state.positions = action.payload
    },
    setBalances: (state, action: PayloadAction<Balance[]>) => {
      state.balances = action.payload
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
  setSelectedPair,
  setOrderType,
  setOrderSide,
  setOrders,
  addOrder,
  updateOrder,
  removeOrder,
  setPositions,
  setBalances,
  setLoading,
  setError,
} = tradingSlice.actions