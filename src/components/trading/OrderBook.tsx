'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

interface OrderBookProps {
  symbol: string
}

export function OrderBook({ symbol }: OrderBookProps) {
  const [orderBook, setOrderBook] = useState<{
    bids: OrderBookEntry[]
    asks: OrderBookEntry[]
  }>({
    bids: [],
    asks: []
  })

  useEffect(() => {
    // Generate mock order book data
    const generateOrderBook = () => {
      const basePrice = 45000
      const bids: OrderBookEntry[] = []
      const asks: OrderBookEntry[] = []
      
      let bidTotal = 0
      let askTotal = 0

      // Generate bids (below current price)
      for (let i = 0; i < 20; i++) {
        const price = basePrice - (i + 1) * 10
        const quantity = Math.random() * 10 + 0.1
        bidTotal += quantity
        bids.push({ price, quantity, total: bidTotal })
      }

      // Generate asks (above current price)
      for (let i = 0; i < 20; i++) {
        const price = basePrice + (i + 1) * 10
        const quantity = Math.random() * 10 + 0.1
        askTotal += quantity
        asks.push({ price, quantity, total: askTotal })
      }

      setOrderBook({ bids, asks })
    }

    generateOrderBook()
    
    // Update order book every 2 seconds
    const interval = setInterval(generateOrderBook, 2000)
    return () => clearInterval(interval)
  }, [symbol])

  const formatPrice = (price: number) => price.toFixed(2)
  const formatQuantity = (quantity: number) => quantity.toFixed(4)

  const maxBidTotal = Math.max(...orderBook.bids.map(b => b.total))
  const maxAskTotal = Math.max(...orderBook.asks.map(a => a.total))

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex justify-between text-xs text-gray-400 font-medium">
          <span>Price (USDT)</span>
          <span>Amount (BTC)</span>
          <span>Total</span>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {/* Asks (Sell Orders) */}
        <div className="h-1/2 overflow-y-auto scrollbar-thin">
          <div className="space-y-px">
            {orderBook.asks.slice().reverse().map((ask, index) => (
              <motion.div
                key={`ask-${ask.price}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: index * 0.01 }}
                className="relative flex justify-between items-center px-4 py-1 hover:bg-red-500/10 transition-colors cursor-pointer group"
              >
                {/* Background bar */}
                <div
                  className="absolute inset-0 bg-red-500/10"
                  style={{
                    width: `${(ask.total / maxAskTotal) * 100}%`,
                    right: 0,
                  }}
                />
                
                <div className="relative z-10 flex justify-between w-full text-xs">
                  <span className="text-red-400 font-mono">{formatPrice(ask.price)}</span>
                  <span className="text-gray-300 font-mono">{formatQuantity(ask.quantity)}</span>
                  <span className="text-gray-400 font-mono">{formatQuantity(ask.total)}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Spread */}
        <div className="flex items-center justify-center py-2 bg-gray-700/50 border-y border-gray-600">
          <div className="text-center">
            <div className="text-white font-bold text-lg">
              ${orderBook.bids[0] ? formatPrice(orderBook.bids[0].price) : '0.00'}
            </div>
            <div className="text-gray-400 text-xs">
              Spread: ${orderBook.asks[0] && orderBook.bids[0] 
                ? (orderBook.asks[0].price - orderBook.bids[0].price).toFixed(2) 
                : '0.00'}
            </div>
          </div>
        </div>

        {/* Bids (Buy Orders) */}
        <div className="h-1/2 overflow-y-auto scrollbar-thin">
          <div className="space-y-px">
            {orderBook.bids.map((bid, index) => (
              <motion.div
                key={`bid-${bid.price}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: index * 0.01 }}
                className="relative flex justify-between items-center px-4 py-1 hover:bg-green-500/10 transition-colors cursor-pointer group"
              >
                {/* Background bar */}
                <div
                  className="absolute inset-0 bg-green-500/10"
                  style={{
                    width: `${(bid.total / maxBidTotal) * 100}%`,
                    right: 0,
                  }}
                />
                
                <div className="relative z-10 flex justify-between w-full text-xs">
                  <span className="text-green-400 font-mono">{formatPrice(bid.price)}</span>
                  <span className="text-gray-300 font-mono">{formatQuantity(bid.quantity)}</span>
                  <span className="text-gray-400 font-mono">{formatQuantity(bid.total)}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}