import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import TradingChart from '../../components/trading/TradingChart';
import OrderBook from '../../components/trading/OrderBook';
import OrderForm from '../../components/trading/OrderForm';
import PositionsPanel from '../../components/trading/PositionsPanel';
import MarketSelector from '../../components/trading/MarketSelector';
import TradingHeader from '../../components/trading/TradingHeader';

const TradePage = () => {
  const [selectedPair, setSelectedPair] = useState('BTC/USDT');
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [activeTab, setActiveTab] = useState('spot');

  const tradingTabs = [
    { id: 'spot', name: 'Spot', description: 'Buy and sell crypto instantly' },
    { id: 'margin', name: 'Margin', description: 'Trade with leverage up to 10x' },
    { id: 'futures', name: 'Futures', description: 'Perpetual and quarterly contracts' },
    { id: 'options', name: 'Options', description: 'European and American style options' }
  ];

  const marketData = {
    'BTC/USDT': {
      price: '43,250.00',
      change: '+2.45%',
      high24h: '44,100.00',
      low24h: '42,800.00',
      volume: '2.1B',
      isPositive: true
    },
    'ETH/USDT': {
      price: '2,650.00',
      change: '+1.85%',
      high24h: '2,720.00',
      low24h: '2,580.00',
      volume: '1.8B',
      isPositive: true
    }
  };

  const currentMarket = marketData[selectedPair] || marketData['BTC/USDT'];

  return (
    <>
      <Head>
        <title>Trade - TigerEx</title>
        <meta name="description" content="Advanced cryptocurrency trading with spot, margin, futures, and options" />
      </Head>

      <div className="min-h-screen bg-gray-900">
        {/* Trading Header */}
        <TradingHeader />

        {/* Trading Tabs */}
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex space-x-8">
              {tradingTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-2 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-yellow-400 text-yellow-400'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  <div className="text-sm font-medium">{tab.name}</div>
                  <div className="text-xs text-gray-500">{tab.description}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Trading Interface */}
        <div className="max-w-7xl mx-auto p-4">
          <div className="grid grid-cols-12 gap-4 h-screen">
            {/* Left Sidebar - Market Selector */}
            <div className="col-span-2">
              <MarketSelector 
                selectedPair={selectedPair}
                onPairSelect={setSelectedPair}
              />
            </div>

            {/* Main Trading Area */}
            <div className="col-span-7 space-y-4">
              {/* Market Info Bar */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-6">
                    <div>
                      <div className="text-white font-bold text-xl">{selectedPair}</div>
                      <div className="text-gray-400 text-sm">Perpetual</div>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${currentMarket.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        ${currentMarket.price}
                      </div>
                      <div className={`text-sm ${currentMarket.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        {currentMarket.change}
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400">24h High</div>
                        <div className="text-white">${currentMarket.high24h}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">24h Low</div>
                        <div className="text-white">${currentMarket.low24h}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">24h Volume</div>
                        <div className="text-white">{currentMarket.volume}</div>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button className="bg-yellow-500 text-black px-4 py-2 rounded font-medium hover:bg-yellow-600 transition-colors">
                      Add to Favorites
                    </button>
                    <button className="bg-gray-700 text-white px-4 py-2 rounded font-medium hover:bg-gray-600 transition-colors">
                      Share
                    </button>
                  </div>
                </div>
              </div>

              {/* Trading Chart */}
              <div className="bg-gray-800 rounded-lg h-96">
                <TradingChart pair={selectedPair} />
              </div>

              {/* Positions and Orders */}
              <div className="bg-gray-800 rounded-lg">
                <PositionsPanel activeTab={activeTab} />
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="col-span-3 space-y-4">
              {/* Order Book */}
              <div className="bg-gray-800 rounded-lg h-80">
                <OrderBook pair={selectedPair} />
              </div>

              {/* Order Form */}
              <div className="bg-gray-800 rounded-lg">
                <OrderForm 
                  pair={selectedPair}
                  orderType={orderType}
                  onOrderTypeChange={setOrderType}
                  tradingMode={activeTab}
                />
              </div>

              {/* Recent Trades */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-white font-medium mb-4">Recent Trades</h3>
                <div className="space-y-2">
                  {[
                    { price: '43,250.00', amount: '0.0234', time: '14:23:45', type: 'buy' },
                    { price: '43,248.50', amount: '0.1567', time: '14:23:44', type: 'sell' },
                    { price: '43,251.00', amount: '0.0891', time: '14:23:43', type: 'buy' },
                    { price: '43,249.75', amount: '0.2134', time: '14:23:42', type: 'sell' },
                    { price: '43,252.25', amount: '0.0456', time: '14:23:41', type: 'buy' }
                  ].map((trade, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <div className={`${trade.type === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.price}
                      </div>
                      <div className="text-gray-400">{trade.amount}</div>
                      <div className="text-gray-500">{trade.time}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TradePage;
