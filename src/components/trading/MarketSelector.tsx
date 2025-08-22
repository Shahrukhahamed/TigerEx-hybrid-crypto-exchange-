'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { MagnifyingGlassIcon, StarIcon } from '@heroicons/react/24/outline'
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid'

interface Market {
  symbol: string
  price: number
  change24h: number
  volume24h: number
}

export function MarketSelector() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [favorites, setFavorites] = useState<Set<string>>(new Set(['BTCUSDT', 'ETHUSDT']))

  const categories = ['All', 'Favorites', 'BTC', 'ETH', 'DeFi', 'Layer 1']

  const markets: Market[] = [
    { symbol: 'BTCUSDT', price: 45000, change24h: 2.5, volume24h: 1234567890 },
    { symbol: 'ETHUSDT', price: 3200, change24h: -1.2, volume24h: 987654321 },
    { symbol: 'BNBUSDT', price: 320, change24h: 3.8, volume24h: 456789123 },
    { symbol: 'ADAUSDT', price: 0.45, change24h: 5.2, volume24h: 234567890 },
    { symbol: 'SOLUSDT', price: 95, change24h: -2.1, volume24h: 345678901 },
    { symbol: 'DOTUSDT', price: 6.8, change24h: 1.9, volume24h: 123456789 },
    { symbol: 'AVAXUSDT', price: 28, change24h: 4.3, volume24h: 198765432 },
    { symbol: 'MATICUSDT', price: 0.85, change24h: -0.8, volume24h: 167890123 },
  ]

  const filteredMarkets = markets.filter(market => {
    const matchesSearch = market.symbol.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || 
      (selectedCategory === 'Favorites' && favorites.has(market.symbol)) ||
      market.symbol.includes(selectedCategory)
    return matchesSearch && matchesCategory
  })

  const toggleFavorite = (symbol: string) => {
    const newFavorites = new Set(favorites)
    if (newFavorites.has(symbol)) {
      newFavorites.delete(symbol)
    } else {
      newFavorites.add(symbol)
    }
    setFavorites(newFavorites)
  }

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
    }
    return volume.toString()
  }

  return (
    <div className="h-80 card flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-3">Markets</h3>
        
        {/* Search */}
        <div className="relative mb-3">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search markets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 transition-colors"
          />
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-1">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Markets List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="p-2">
          {filteredMarkets.map((market, index) => (
            <motion.div
              key={market.symbol}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className="flex items-center justify-between p-3 hover:bg-gray-700/50 rounded-lg cursor-pointer transition-colors group"
            >
              <div className="flex items-center space-x-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleFavorite(market.symbol)
                  }}
                  className="text-gray-400 hover:text-yellow-400 transition-colors"
                >
                  {favorites.has(market.symbol) ? (
                    <StarSolidIcon className="h-4 w-4 text-yellow-400" />
                  ) : (
                    <StarIcon className="h-4 w-4" />
                  )}
                </button>
                
                <div>
                  <div className="text-white font-medium text-sm">{market.symbol}</div>
                  <div className="text-gray-400 text-xs">Vol: {formatVolume(market.volume24h)}</div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-white font-medium text-sm">
                  ${formatPrice(market.price)}
                </div>
                <div className={`text-xs font-medium ${
                  market.change24h >= 0 ? 'text-bull' : 'text-bear'
                }`}>
                  {market.change24h >= 0 ? '+' : ''}{market.change24h.toFixed(2)}%
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}