'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline'

interface TradingPair {
  symbol: string
  price: number
  change24h: number
  volume24h: number
  high24h: number
  low24h: number
}

export function TradingPairs() {
  const [pairs, setPairs] = useState<TradingPair[]>([])
  const [selectedCategory, setSelectedCategory] = useState('All')

  const categories = ['All', 'Favorites', 'BTC', 'ETH', 'DeFi', 'Layer 1', 'Meme']

  useEffect(() => {
    // Mock data - in real app, this would come from API
    const mockPairs: TradingPair[] = [
      { symbol: 'BTCUSDT', price: 45000, change24h: 2.5, volume24h: 1234567890, high24h: 46000, low24h: 44000 },
      { symbol: 'ETHUSDT', price: 3200, change24h: -1.2, volume24h: 987654321, high24h: 3300, low24h: 3100 },
      { symbol: 'BNBUSDT', price: 320, change24h: 3.8, volume24h: 456789123, high24h: 335, low24h: 310 },
      { symbol: 'ADAUSDT', price: 0.45, change24h: 5.2, volume24h: 234567890, high24h: 0.48, low24h: 0.42 },
      { symbol: 'SOLUSDT', price: 95, change24h: -2.1, volume24h: 345678901, high24h: 98, low24h: 92 },
      { symbol: 'DOTUSDT', price: 6.8, change24h: 1.9, volume24h: 123456789, high24h: 7.1, low24h: 6.5 },
      { symbol: 'AVAXUSDT', price: 28, change24h: 4.3, volume24h: 198765432, high24h: 29.5, low24h: 26.8 },
      { symbol: 'MATICUSDT', price: 0.85, change24h: -0.8, volume24h: 167890123, high24h: 0.88, low24h: 0.82 },
    ]
    setPairs(mockPairs)
  }, [])

  const formatPrice = (price: number) => {
    if (price < 1) {
      return price.toFixed(4)
    } else if (price < 100) {
      return price.toFixed(2)
    } else {
      return price.toLocaleString()
    }
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) {
      return `${(volume / 1e9).toFixed(1)}B`
    } else if (volume >= 1e6) {
      return `${(volume / 1e6).toFixed(1)}M`
    } else if (volume >= 1e3) {
      return `${(volume / 1e3).toFixed(1)}K`
    }
    return volume.toString()
  }

  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Live Market Data
          </h2>
          <p className="text-gray-400 text-lg">
            Real-time prices from multiple exchanges and DEX protocols
          </p>
        </motion.div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* Trading Pairs Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="card overflow-hidden"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Pair
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    24h Change
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    24h Volume
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    24h High
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    24h Low
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {pairs.map((pair, index) => (
                  <motion.tr
                    key={pair.symbol}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className="hover:bg-gray-700/30 transition-colors cursor-pointer"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-8 w-8">
                          <div className="h-8 w-8 rounded-full bg-orange-500/20 flex items-center justify-center">
                            <span className="text-orange-400 font-medium text-sm">
                              {pair.symbol.substring(0, 2)}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-white">{pair.symbol}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-sm font-medium text-white">
                        ${formatPrice(pair.price)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`flex items-center justify-end text-sm font-medium ${
                        pair.change24h >= 0 ? 'text-bull' : 'text-bear'
                      }`}>
                        {pair.change24h >= 0 ? (
                          <ArrowUpIcon className="h-4 w-4 mr-1" />
                        ) : (
                          <ArrowDownIcon className="h-4 w-4 mr-1" />
                        )}
                        {pair.change24h >= 0 ? '+' : ''}{pair.change24h.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-sm text-gray-300">
                        ${formatVolume(pair.volume24h)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-sm text-gray-300">
                        ${formatPrice(pair.high24h)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-sm text-gray-300">
                        ${formatPrice(pair.low24h)}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        <div className="text-center mt-8">
          <Link
            href="/markets"
            className="btn btn-primary hover:scale-105 transform transition-all"
          >
            View All Markets
          </Link>
        </div>
      </div>
    </section>
  )
}