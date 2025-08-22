import { configureStore } from '@reduxjs/toolkit'
import { authSlice } from './slices/authSlice'
import { tradingSlice } from './slices/tradingSlice'
import { marketSlice } from './slices/marketSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    trading: tradingSlice.reducer,
    market: marketSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch