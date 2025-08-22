'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '@/store'
import { setSelectedPair, setOrderType, setOrderSide } from '@/store/slices/tradingSlice'
import { OrderBook } from './OrderBook'
import { TradingChart } from './TradingChart'
import { OrderForm } from './OrderForm'
import { PositionsPanel } from './PositionsPanel'
import { MarketSelector } from './MarketSelector'
import { TradingHeader } from './TradingHeader'

export function TradingInterface() {
  const dispatch = useDispatch()
  const { selectedPair } = useSelector((state: RootState) => state.trading)
  const [activeTab, setActiveTab] = useState('orderbook')

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Trading Header */}
      <TradingHeader />

      {/* Main Trading Interface */}
      <div className="flex-1 grid grid-cols-12 gap-1 p-1 overflow-hidden">
        {/* Left Panel - Market Selector & Order Book */}
        <div className="col-span-3 flex flex-col space-y-1">
          <MarketSelector />
          <div className="flex-1 card">
            <div className="p-4 border-b border-gray-700">
              <div className="flex space-x-4">
                <button
                  onClick={() => setActiveTab('orderbook')}
                  className={`pb-2 border-b-2 transition-colors ${
                    activeTab === 'orderbook'
                      ? 'text-orange-400 border-orange-400'
                      : 'text-gray-400 border-transparent hover:text-white'
                  }`}
                >
                  Order Book
                </button>
                <button
                  onClick={() => setActiveTab('trades')}
                  className={`pb-2 border-b-2 transition-colors ${
                    activeTab === 'trades'
                      ? 'text-orange-400 border-orange-400'
                      : 'text-gray-400 border-transparent hover:text-white'
                  }`}
                >
                  Recent Trades
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              {activeTab === 'orderbook' && <OrderBook symbol={selectedPair} />}
              {activeTab === 'trades' && <div className="p-4 text-gray-400">Recent trades will be displayed here</div>}
            </div>
          </div>
        </div>

        {/* Center Panel - Chart */}
        <div className="col-span-6 card">
          <TradingChart symbol={selectedPair} />
        </div>

        {/* Right Panel - Order Form */}
        <div className="col-span-3 card">
          <OrderForm />
        </div>
      </div>

      {/* Bottom Panel - Positions & Orders */}
      <div className="h-64 card m-1">
        <PositionsPanel />
      </div>
    </div>
  )
}