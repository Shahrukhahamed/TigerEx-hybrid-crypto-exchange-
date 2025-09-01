import React, { useState } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import TradingHeader from '../../components/trading/TradingHeader';

const OptionsPage = () => {
  const [selectedUnderlying, setSelectedUnderlying] = useState('BTC');
  const [optionType, setOptionType] = useState<'call' | 'put'>('call');
  const [expiryDate, setExpiryDate] = useState('2024-03-29');

  const underlyingAssets = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'];
  const expiryDates = ['2024-03-29', '2024-04-05', '2024-04-12', '2024-04-26', '2024-05-31'];

  const optionsChain = [
    { strike: 40000, call: { price: 3250, iv: '65%', delta: '0.85' }, put: { price: 150, iv: '62%', delta: '-0.15' } },
    { strike: 42000, call: { price: 1850, iv: '58%', delta: '0.72' }, put: { price: 350, iv: '59%', delta: '-0.28' } },
    { strike: 43000, call: { price: 1250, iv: '55%', delta: '0.65' }, put: { price: 500, iv: '56%', delta: '-0.35' } },
    { strike: 44000, call: { price: 850, iv: '52%', delta: '0.58' }, put: { price: 750, iv: '53%', delta: '-0.42' } },
    { strike: 45000, call: { price: 550, iv: '50%', delta: '0.48' }, put: { price: 1050, iv: '51%', delta: '-0.52' } },
    { strike: 46000, call: { price: 350, iv: '48%', delta: '0.38' }, put: { price: 1450, iv: '49%', delta: '-0.62' } },
    { strike: 48000, call: { price: 150, iv: '45%', delta: '0.22' }, put: { price: 2250, iv: '46%', delta: '-0.78' } }
  ];

  return (
    <>
      <Head>
        <title>Options Trading - TigerEx</title>
        <meta name="description" content="Trade cryptocurrency options with European and American style contracts" />
      </Head>

      <div className="min-h-screen bg-gray-900">
        <TradingHeader />

        {/* Options Header */}
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <h1 className="text-white text-2xl font-bold">Options Trading</h1>
                <div className="flex items-center space-x-4">
                  <select
                    value={selectedUnderlying}
                    onChange={(e) => setSelectedUnderlying(e.target.value)}
                    className="bg-gray-700 text-white px-4 py-2 rounded border border-gray-600"
                  >
                    {underlyingAssets.map(asset => (
                      <option key={asset} value={asset}>{asset}</option>
                    ))}
                  </select>
                  <select
                    value={expiryDate}
                    onChange={(e) => setExpiryDate(e.target.value)}
                    className="bg-gray-700 text-white px-4 py-2 rounded border border-gray-600"
                  >
                    {expiryDates.map(date => (
                      <option key={date} value={date}>{date}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-white text-sm">
                  <span className="text-gray-400">Current Price:</span>
                  <span className="ml-2 font-bold">$43,250.00</span>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                  Options Guide
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto p-4">
          <div className="grid grid-cols-12 gap-4">
            {/* Options Chain */}
            <div className="col-span-8">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-bold text-lg">Options Chain - {selectedUnderlying}</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setOptionType('call')}
                      className={`px-4 py-2 rounded font-medium transition-colors ${
                        optionType === 'call'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Calls
                    </button>
                    <button
                      onClick={() => setOptionType('put')}
                      className={`px-4 py-2 rounded font-medium transition-colors ${
                        optionType === 'put'
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Puts
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-700">
                        <th className="text-left py-3">Strike</th>
                        <th className="text-left py-3">Last Price</th>
                        <th className="text-left py-3">Bid</th>
                        <th className="text-left py-3">Ask</th>
                        <th className="text-left py-3">IV</th>
                        <th className="text-left py-3">Delta</th>
                        <th className="text-left py-3">Volume</th>
                        <th className="text-left py-3">OI</th>
                        <th className="text-left py-3">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {optionsChain.map((option, index) => {
                        const data = optionType === 'call' ? option.call : option.put;
                        const isITM = optionType === 'call' ? option.strike < 43250 : option.strike > 43250;
                        
                        return (
                          <motion.tr
                            key={option.strike}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.05 }}
                            className={`border-b border-gray-700 hover:bg-gray-700/50 ${
                              isITM ? 'bg-yellow-500/10' : ''
                            }`}
                          >
                            <td className="py-3 text-white font-medium">${option.strike.toLocaleString()}</td>
                            <td className="py-3 text-white">${data.price}</td>
                            <td className="py-3 text-green-400">${(data.price * 0.98).toFixed(0)}</td>
                            <td className="py-3 text-red-400">${(data.price * 1.02).toFixed(0)}</td>
                            <td className="py-3 text-gray-300">{data.iv}</td>
                            <td className="py-3 text-gray-300">{data.delta}</td>
                            <td className="py-3 text-gray-400">1.2K</td>
                            <td className="py-3 text-gray-400">5.8K</td>
                            <td className="py-3">
                              <div className="flex space-x-2">
                                <button className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">
                                  Buy
                                </button>
                                <button className="bg-red-600 text-white px-3 py-1 rounded text-xs hover:bg-red-700">
                                  Sell
                                </button>
                              </div>
                            </td>
                          </motion.tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Positions */}
              <div className="bg-gray-800 rounded-lg p-4 mt-4">
                <h3 className="text-white font-bold text-lg mb-4">My Options Positions</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-700">
                        <th className="text-left py-3">Contract</th>
                        <th className="text-left py-3">Type</th>
                        <th className="text-left py-3">Size</th>
                        <th className="text-left py-3">Entry Price</th>
                        <th className="text-left py-3">Mark Price</th>
                        <th className="text-left py-3">PNL</th>
                        <th className="text-left py-3">Expiry</th>
                        <th className="text-left py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-gray-700">
                        <td className="py-3 text-white">BTC-44000-C</td>
                        <td className="py-3 text-green-400">Call</td>
                        <td className="py-3 text-white">+5</td>
                        <td className="py-3 text-white">$900</td>
                        <td className="py-3 text-white">$850</td>
                        <td className="py-3 text-red-400">-$250</td>
                        <td className="py-3 text-gray-400">2024-03-29</td>
                        <td className="py-3">
                          <button className="text-red-400 hover:text-red-300">Close</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="col-span-4 space-y-4">
              {/* Order Form */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-white font-bold mb-4">Place Options Order</h3>
                <div className="space-y-4">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setOptionType('call')}
                      className={`flex-1 py-2 rounded font-medium transition-colors ${
                        optionType === 'call'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Call
                    </button>
                    <button
                      onClick={() => setOptionType('put')}
                      className={`flex-1 py-2 rounded font-medium transition-colors ${
                        optionType === 'put'
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Put
                    </button>
                  </div>

                  <div>
                    <label className="block text-gray-400 text-sm mb-2">Strike Price</label>
                    <select className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600">
                      {optionsChain.map(option => (
                        <option key={option.strike} value={option.strike}>
                          ${option.strike.toLocaleString()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-gray-400 text-sm mb-2">Order Type</label>
                    <select className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600">
                      <option value="market">Market</option>
                      <option value="limit">Limit</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-gray-400 text-sm mb-2">Quantity</label>
                    <input
                      type="number"
                      placeholder="0"
                      className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-gray-400 text-sm mb-2">Price (USDT)</label>
                    <input
                      type="number"
                      placeholder="0.00"
                      className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                    />
                  </div>

                  <div className="flex space-x-2">
                    <button className="flex-1 bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition-colors">
                      Buy {optionType === 'call' ? 'Call' : 'Put'}
                    </button>
                    <button className="flex-1 bg-red-600 text-white py-3 rounded-lg font-medium hover:bg-red-700 transition-colors">
                      Sell {optionType === 'call' ? 'Call' : 'Put'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Greeks */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-white font-bold mb-4">Option Greeks</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Delta:</span>
                    <span className="text-white">0.65</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Gamma:</span>
                    <span className="text-white">0.0012</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Theta:</span>
                    <span className="text-red-400">-15.50</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Vega:</span>
                    <span className="text-white">8.25</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Rho:</span>
                    <span className="text-white">2.15</span>
                  </div>
                </div>
              </div>

              {/* Market Info */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-white font-bold mb-4">Market Information</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Underlying Price:</span>
                    <span className="text-white">$43,250.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Implied Volatility:</span>
                    <span className="text-white">55%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Time to Expiry:</span>
                    <span className="text-white">15 days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Risk-free Rate:</span>
                    <span className="text-white">5.25%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default OptionsPage;
