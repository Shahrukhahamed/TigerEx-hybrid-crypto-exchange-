'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '@/store'
import { setOrderType, setOrderSide } from '@/store/slices/tradingSlice'

export function OrderForm() {
  const dispatch = useDispatch()
  const { orderType, orderSide } = useSelector((state: RootState) => state.trading)
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [stopPrice, setStopPrice] = useState('')
  const [leverage, setLeverage] = useState(1)

  const orderTypes = ['LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LIMIT', 'TAKE_PROFIT']
  const percentages = [25, 50, 75, 100]

  const handlePlaceOrder = () => {
    // Order placement logic
    console.log('Placing order:', {
      type: orderType,
      side: orderSide,
      quantity,
      price,
      stopPrice,
      leverage
    })
  }

  const setPercentage = (percentage: number) => {
    // Calculate quantity based on percentage of available balance
    const mockBalance = 10000 // Mock available balance
    const currentPrice = 45000 // Mock current price
    
    if (orderSide === 'BUY') {
      const totalValue = (mockBalance * percentage) / 100
      const calculatedQuantity = totalValue / currentPrice
      setQuantity(calculatedQuantity.toFixed(6))
    } else {
      const mockBtcBalance = 0.5 // Mock BTC balance
      const calculatedQuantity = (mockBtcBalance * percentage) / 100
      setQuantity(calculatedQuantity.toFixed(6))
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Place Order</h3>
      </div>

      <div className="flex-1 p-4 space-y-4">
        {/* Order Type Tabs */}
        <div className="flex space-x-1 bg-gray-700 rounded-lg p-1">
          {orderTypes.map((type) => (
            <button
              key={type}
              onClick={() => dispatch(setOrderType(type))}
              className={`flex-1 py-2 px-3 rounded text-sm font-medium transition-colors ${
                orderType === type
                  ? 'bg-orange-500 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Buy/Sell Toggle */}
        <div className="flex space-x-1 bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => dispatch(setOrderSide('BUY'))}
            className={`flex-1 py-3 px-4 rounded font-medium transition-colors ${
              orderSide === 'BUY'
                ? 'bg-green-500 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Buy
          </button>
          <button
            onClick={() => dispatch(setOrderSide('SELL'))}
            className={`flex-1 py-3 px-4 rounded font-medium transition-colors ${
              orderSide === 'SELL'
                ? 'bg-red-500 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Sell
          </button>
        </div>

        {/* Leverage Slider (for futures) */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="text-gray-400 text-sm">Leverage</label>
            <span className="text-white font-medium">{leverage}x</span>
          </div>
          <input
            type="range"
            min="1"
            max="125"
            value={leverage}
            onChange={(e) => setLeverage(Number(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>1x</span>
            <span>25x</span>
            <span>50x</span>
            <span>100x</span>
            <span>125x</span>
          </div>
        </div>

        {/* Price Input */}
        {orderType !== 'MARKET' && (
          <div className="space-y-2">
            <label className="block text-gray-400 text-sm">Price</label>
            <div className="relative">
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 transition-colors"
              />
              <span className="absolute right-3 top-3 text-gray-400 text-sm">USDT</span>
            </div>
          </div>
        )}

        {/* Stop Price Input */}
        {(orderType === 'STOP_LOSS' || orderType === 'STOP_LIMIT') && (
          <div className="space-y-2">
            <label className="block text-gray-400 text-sm">Stop Price</label>
            <div className="relative">
              <input
                type="number"
                value={stopPrice}
                onChange={(e) => setStopPrice(e.target.value)}
                placeholder="0.00"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 transition-colors"
              />
              <span className="absolute right-3 top-3 text-gray-400 text-sm">USDT</span>
            </div>
          </div>
        )}

        {/* Quantity Input */}
        <div className="space-y-2">
          <label className="block text-gray-400 text-sm">Quantity</label>
          <div className="relative">
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="0.000000"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 transition-colors"
            />
            <span className="absolute right-3 top-3 text-gray-400 text-sm">BTC</span>
          </div>
        </div>

        {/* Percentage Buttons */}
        <div className="grid grid-cols-4 gap-2">
          {percentages.map((percentage) => (
            <button
              key={percentage}
              onClick={() => setPercentage(percentage)}
              className="py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white rounded text-sm font-medium transition-colors"
            >
              {percentage}%
            </button>
          ))}
        </div>

        {/* Total */}
        <div className="space-y-2">
          <label className="block text-gray-400 text-sm">Total</label>
          <div className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-3">
            <span className="text-white">
              {(parseFloat(quantity || '0') * parseFloat(price || '0')).toFixed(2)} USDT
            </span>
          </div>
        </div>

        {/* Available Balance */}
        <div className="text-sm text-gray-400">
          Available: {orderSide === 'BUY' ? '10,000.00 USDT' : '0.5000 BTC'}
        </div>

        {/* Submit Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handlePlaceOrder}
          disabled={!quantity || (orderType !== 'MARKET' && !price)}
          className={`w-full py-4 rounded-lg font-semibold text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
            orderSide === 'BUY'
              ? 'bg-green-500 hover:bg-green-600'
              : 'bg-red-500 hover:bg-red-600'
          }`}
        >
          {orderSide === 'BUY' ? 'Buy' : 'Sell'} BTC
        </motion.button>
      </div>
    </div>
  )
}