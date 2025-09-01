import React, { useState } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import TradingChart from '../../components/trading/TradingChart';
import OrderBook from '../../components/trading/OrderBook';
import OrderForm from '../../components/trading/OrderForm';
import TradingHeader from '../../components/trading/TradingHeader';

const FuturesPage = () => {
  const [selectedContract, setSelectedContract] = useState('BTCUSDT');
  const [contractType, setContractType] = useState<'usd-m' | 'coin-m'>('usd-m');
  const [leverage, setLeverage] = useState(10);

  const contracts = {
    'usd-m': [
      { symbol: 'BTCUSDT', price: '43,250.00', change: '+2.45%', volume: '2.1B', funding: '0.0100%' },
      { symbol: 'ETHUSDT', price: '2,650.00', change: '+1.85%', volume: '1.8B', funding: '0.0075%' },
      { symbol: 'BNBUSDT', price: '315.50', change: '-0.75%', volume: '450M', funding: '-0.0050%' },
      { symbol: 'ADAUSDT', price: '0.4850', change: '+3.20%', volume: '320M', funding: '0.0125%' },
      { symbol: 'SOLUSDT', price: '98.75', change: '+4.15%', volume: '280M', funding: '0.0200%' }
    ],
    'coin-m': [
      { symbol: 'BTCUSD', price: '43,250.00', change: '+2.45%', volume: '1.2B', funding: '0.0100%' },
      { symbol: 'ETHUSD', price: '2,650.00', change: '+1.85%', volume: '800M', funding: '0.0075%' },
      { symbol: 'ADAUSD', price: '0.4850', change: '+3.20%', volume: '150M', funding: '0.0125%' }
    ]
  };

  const leverageOptions = [1, 2, 3, 5, 10, 20, 25, 50, 75, 100, 125];

  return (
    <>
      <Head>
        <title>Futures Trading - TigerEx</title>
        <meta name="description" content="Trade cryptocurrency futures with up to 125x leverage. USD-M and COIN-M perpetual contracts." />
      </Head>

      <div className="min-h-screen bg-gray-900">
        <TradingHeader />

        {/* Futures Header */}
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <h1 className="text-white text-2xl font-bold">Futures Trading</h1>
                <div className="flex space-x-4">
                  <button
                    onClick={() => setContractType('usd-m')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      contractType === 'usd-m'
                        ? 'bg-yellow-500 text-black'
                        : 'bg-gray-700 text-white hover:bg-gray-600'
                    }`}
                  >
                    USD-M Futures
                  </button>
                  <button
                    onClick={() => setContractType('coin-m')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      contractType === 'coin-m'
                        ? 'bg-yellow-500 text-black'
                        : 'bg-gray-700 text-white hover:bg-gray-600'
                    }`}
                  >
                    COIN-M Futures
                  </button>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-white">
                  <span className="text-gray-400">Leverage:</span>
                  <select
                    value={leverage}
                    onChange={(e) => setLeverage(Number(e.target.value))}
                    className="ml-2 bg-gray-700 text-white px-3 py-1 rounded border border-gray-600"
                  >
                    {leverageOptions.map(lev => (
                      <option key={lev} value={lev}>{lev}x</option>
                    ))}
                  </select>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                  Tutorial
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto p-4">
          <div className="grid grid-cols-12 gap-4">
            {/* Left Sidebar - Contract List */}
            <div className="col-span-3 bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-medium">
                  {contractType === 'usd-m' ? 'USD-M Perpetual' : 'COIN-M Perpetual'}
                </h3>
                <button className="text-gray-400 hover:text-white">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-1">
                {contracts[contractType].map((contract) => (
                  <motion.div
                    key={contract.symbol}
                    whileHover={{ backgroundColor: 'rgba(75, 85, 99, 0.5)' }}
                    onClick={() => setSelectedContract(contract.symbol)}
                    className={`p-3 rounded cursor-pointer transition-colors ${
                      selectedContract === contract.symbol ? 'bg-gray-700' : 'hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="text-white font-medium">{contract.symbol}</div>
                        <div className="text-gray-400 text-sm">Perpetual</div>
                      </div>
                      <div className="text-right">
                        <div className="text-white">${contract.price}</div>
                        <div className={`text-sm ${contract.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                          {contract.change}
                        </div>
                      </div>
                    </div>
                    <div className="flex justify-between mt-2 text-xs">
                      <span className="text-gray-400">Vol: {contract.volume}</span>
                      <span className={`${contract.funding.startsWith('-') ? 'text-red-400' : 'text-green-400'}`}>
                        {contract.funding}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Funding Rate Info */}
              <div className="mt-6 p-3 bg-gray-700/50 rounded-lg">
                <h4 className="text-white font-medium mb-2">Funding Rate</h4>
                <div className="text-sm text-gray-300">
                  <div className="flex justify-between">
                    <span>Current:</span>
                    <span className="text-green-400">0.0100%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Next funding:</span>
                    <span>in 2h 34m</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Trading Area */}
            <div className="col-span-6 space-y-4">
              {/* Contract Info */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-6">
                    <div>
                      <div className="text-white font-bold text-xl">{selectedContract}</div>
                      <div className="text-gray-400 text-sm">Perpetual Contract</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-400">$43,250.00</div>
                      <div className="text-sm text-green-400">+2.45% (+$1,035.50)</div>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400">Mark Price</div>
                        <div className="text-white">$43,248.50</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Index Price</div>
                        <div className="text-white">$43,247.25</div>
                      </div>
                      <div>
                        <div className="text-gray-400">24h Volume</div>
                        <div className="text-white">2.1B USDT</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Open Interest</div>
                        <div className="text-white">1.2B USDT</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Trading Chart */}
              <div className="bg-gray-800 rounded-lg h-96">
                <TradingChart pair={selectedContract} />
              </div>

              {/* Position and Orders */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex space-x-6 border-b border-gray-700 mb-4">
                  {['Positions', 'Open Orders', 'Order History', 'Trade History'].map((tab) => (
                    <button key={tab} className="py-2 text-gray-400 hover:text-white border-b-2 border-transparent hover:border-yellow-400 transition-colors">
                      {tab}
                    </button>
                  ))}
                </div>
                
                {/* Positions Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-700">
                        <th className="text-left py-2">Symbol</th>
                        <th className="text-left py-2">Size</th>
                        <th className="text-left py-2">Entry Price</th>
                        <th className="text-left py-2">Mark Price</th>
                        <th className="text-left py-2">PNL</th>
                        <th className="text-left py-2">ROE</th>
                        <th className="text-left py-2">Margin</th>
                        <th className="text-left py-2">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-gray-700">
                        <td className="py-3 text-white">BTCUSDT</td>
                        <td className="py-3 text-green-400">+0.5 BTC</td>
                        <td className="py-3 text-white">$42,800.00</td>
                        <td className="py-3 text-white">$43,250.00</td>
                        <td className="py-3 text-green-400">+$225.00</td>
                        <td className="py-3 text-green-400">+5.25%</td>
                        <td className="py-3 text-white">$4,280.00</td>
                        <td className="py-3">
                          <button className="text-red-400 hover:text-red-300 mr-2">Close</button>
                          <button className="text-blue-400 hover:text-blue-300">Edit</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="col-span-3 space-y-4">
              {/* Order Book */}
              <div className="bg-gray-800 rounded-lg h-80">
                <OrderBook pair={selectedContract} />
              </div>

              {/* Order Form */}
              <div className="bg-gray-800 rounded-lg">
                <OrderForm 
                  pair={selectedContract}
                  orderType="buy"
                  onOrderTypeChange={() => {}}
                  tradingMode="futures"
                  leverage={leverage}
                />
              </div>

              {/* Risk Management */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-white font-medium mb-4">Risk Management</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Account Balance:</span>
                    <span className="text-white">10,000.00 USDT</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Available Balance:</span>
                    <span className="text-white">5,720.00 USDT</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Position Margin:</span>
                    <span className="text-white">4,280.00 USDT</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Margin Ratio:</span>
                    <span className="text-yellow-400">42.8%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Maintenance Margin:</span>
                    <span className="text-white">214.00 USDT</span>
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

export default FuturesPage;
