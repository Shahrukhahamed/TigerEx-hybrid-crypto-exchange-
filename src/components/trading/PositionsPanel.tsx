'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'

export function PositionsPanel() {
  const [activeTab, setActiveTab] = useState('positions')

  const tabs = [
    { id: 'positions', label: 'Positions' },
    { id: 'orders', label: 'Open Orders' },
    { id: 'history', label: 'Order History' },
    { id: 'trades', label: 'Trade History' },
  ]

  const mockPositions = [
    {
      symbol: 'BTCUSDT',
      side: 'LONG',
      size: '0.5',
      entryPrice: '44,500',
      markPrice: '45,000',
      pnl: '+250.00',
      margin: '2,000',
      leverage: '10x'
    }
  ]

  const mockOrders = [
    {
      id: '1',
      symbol: 'BTCUSDT',
      type: 'LIMIT',
      side: 'BUY',
      quantity: '0.1',
      price: '44,000',
      filled: '0%',
      status: 'NEW',
      time: '14:30:25'
    },
    {
      id: '2',
      symbol: 'ETHUSDT',
      type: 'LIMIT',
      side: 'SELL',
      quantity: '2.5',
      price: '3,100',
      filled: '30%',
      status: 'PARTIALLY_FILLED',
      time: '14:25:10'
    }
  ]

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex space-x-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-orange-400 border-orange-400'
                  : 'text-gray-400 border-transparent hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'positions' && (
          <div className="h-full overflow-y-auto">
            {mockPositions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Symbol</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Side</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Size</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Entry Price</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Mark Price</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">PnL</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Margin</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {mockPositions.map((position, index) => (
                      <motion.tr
                        key={position.symbol}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className="hover:bg-gray-700/30 transition-colors"
                      >
                        <td className="px-4 py-3 text-white font-medium">{position.symbol}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            position.side === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {position.side}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-white">{position.size}</td>
                        <td className="px-4 py-3 text-right text-gray-300">${position.entryPrice}</td>
                        <td className="px-4 py-3 text-right text-gray-300">${position.markPrice}</td>
                        <td className="px-4 py-3 text-right">
                          <span className={position.pnl.startsWith('+') ? 'text-green-400' : 'text-red-400'}>
                            ${position.pnl}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-gray-300">${position.margin}</td>
                        <td className="px-4 py-3 text-center">
                          <button className="text-orange-400 hover:text-orange-300 text-sm font-medium transition-colors">
                            Close
                          </button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-gray-400 mb-2">No open positions</div>
                  <div className="text-gray-500 text-sm">Your positions will appear here</div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="h-full overflow-y-auto">
            {mockOrders.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Symbol</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Side</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Quantity</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Price</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Filled</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Time</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {mockOrders.map((order, index) => (
                      <motion.tr
                        key={order.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className="hover:bg-gray-700/30 transition-colors"
                      >
                        <td className="px-4 py-3 text-white font-medium">{order.symbol}</td>
                        <td className="px-4 py-3 text-gray-300">{order.type}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            order.side === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {order.side}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-white">{order.quantity}</td>
                        <td className="px-4 py-3 text-right text-gray-300">${order.price}</td>
                        <td className="px-4 py-3 text-right text-gray-300">{order.filled}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            order.status === 'NEW' ? 'bg-blue-500/20 text-blue-400' : 'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-sm">{order.time}</td>
                        <td className="px-4 py-3 text-center">
                          <button className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors">
                            Cancel
                          </button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-gray-400 mb-2">No open orders</div>
                  <div className="text-gray-500 text-sm">Your orders will appear here</div>
                </div>
              </div>
            )}
          </div>
        )}

        {(activeTab === 'history' || activeTab === 'trades') && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-gray-400 mb-2">No {activeTab === 'history' ? 'order' : 'trade'} history</div>
              <div className="text-gray-500 text-sm">Your {activeTab === 'history' ? 'order' : 'trade'} history will appear here</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}