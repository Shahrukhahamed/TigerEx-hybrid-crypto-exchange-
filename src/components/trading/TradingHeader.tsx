'use client'

import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline'

export function TradingHeader() {
  // Mock data - in real app, this would come from Redux store
  const marketData = {
    symbol: 'BTCUSDT',
    price: 45000,
    change24h: 2.5,
    volume24h: 1234567890,
    high24h: 46000,
    low24h: 44000
  }

  const formatNumber = (num: number) => {
    if (num >= 1e9) {
      return `${(num / 1e9).toFixed(1)}B`
    } else if (num >= 1e6) {
      return `${(num / 1e6).toFixed(1)}M`
    }
    return num.toLocaleString()
  }

  return (
    <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-white">{marketData.symbol}</h1>
            <div className="text-2xl font-bold text-white">
              ${marketData.price.toLocaleString()}
            </div>
            <div className={`flex items-center space-x-1 ${
              marketData.change24h >= 0 ? 'text-bull' : 'text-bear'
            }`}>
              {marketData.change24h >= 0 ? (
                <ArrowUpIcon className="h-4 w-4" />
              ) : (
                <ArrowDownIcon className="h-4 w-4" />
              )}
              <span className="font-medium">
                {marketData.change24h >= 0 ? '+' : ''}{marketData.change24h.toFixed(2)}%
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-6 text-sm">
            <div>
              <span className="text-gray-400">24h High: </span>
              <span className="text-white font-medium">${marketData.high24h.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-400">24h Low: </span>
              <span className="text-white font-medium">${marketData.low24h.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-400">24h Volume: </span>
              <span className="text-white font-medium">${formatNumber(marketData.volume24h)}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Total Balance</div>
            <div className="text-lg font-semibold text-white">$125,430.50</div>
          </div>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
      </div>
    </div>
  )
}