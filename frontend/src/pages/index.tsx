import React from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { 
  TrendingUpIcon, 
  ShieldCheckIcon, 
  GlobeAltIcon, 
  CurrencyDollarIcon,
  ChartBarIcon,
  UserGroupIcon,
  LightningBoltIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';

const HomePage = () => {
  const tradingPairs = [
    { symbol: 'BTC/USDT', price: '43,250.00', change: '+2.45%', volume: '2.1B', isPositive: true },
    { symbol: 'ETH/USDT', price: '2,650.00', change: '+1.85%', volume: '1.8B', isPositive: true },
    { symbol: 'BNB/USDT', price: '315.50', change: '-0.75%', volume: '450M', isPositive: false },
    { symbol: 'ADA/USDT', price: '0.4850', change: '+3.20%', volume: '320M', isPositive: true },
    { symbol: 'SOL/USDT', price: '98.75', change: '+4.15%', volume: '280M', isPositive: true },
    { symbol: 'MATIC/USDT', price: '0.8950', change: '-1.25%', volume: '180M', isPositive: false },
  ];

  const features = [
    {
      icon: TrendingUpIcon,
      title: 'Advanced Trading',
      description: 'Spot, Margin, Futures, Options & Copy Trading with professional tools',
      color: 'from-yellow-400 to-orange-500'
    },
    {
      icon: ShieldCheckIcon,
      title: 'Bank-Level Security',
      description: 'Multi-signature wallets, cold storage, and advanced risk management',
      color: 'from-green-400 to-blue-500'
    },
    {
      icon: GlobeAltIcon,
      title: 'Global P2P Trading',
      description: '180+ countries, 12+ payment methods, instant settlements',
      color: 'from-purple-400 to-pink-500'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Low Fees',
      description: 'Industry-leading low trading fees starting from 0.1%',
      color: 'from-blue-400 to-cyan-500'
    },
    {
      icon: ChartBarIcon,
      title: 'NFT Marketplace',
      description: 'Multi-chain NFT trading with IPFS integration',
      color: 'from-red-400 to-pink-500'
    },
    {
      icon: UserGroupIcon,
      title: 'Copy Trading',
      description: 'Follow top traders with AI-powered performance analytics',
      color: 'from-indigo-400 to-purple-500'
    }
  ];

  const services = [
    { name: 'Spot Trading', description: '500+ trading pairs', icon: '📈' },
    { name: 'Margin Trading', description: 'Up to 10x leverage', icon: '⚡' },
    { name: 'Futures Trading', description: 'USD-M & COIN-M contracts', icon: '🚀' },
    { name: 'Options Trading', description: 'European & American style', icon: '🎯' },
    { name: 'Copy Trading', description: 'Social trading platform', icon: '👥' },
    { name: 'P2P Trading', description: 'Global peer-to-peer', icon: '🌍' },
    { name: 'Convert', description: 'Instant crypto conversion', icon: '🔄' },
    { name: 'Alpha Market', description: 'Early access tokens', icon: '⭐' },
    { name: 'NFT Marketplace', description: 'Multi-chain NFTs', icon: '🎨' },
    { name: 'Staking', description: 'Earn rewards', icon: '💰' },
    { name: 'DeFi', description: 'Yield farming', icon: '🌾' },
    { name: 'Institutional', description: 'Prime brokerage', icon: '🏛️' }
  ];

  return (
    <>
      <Head>
        <title>TigerEx - Advanced Crypto Trading Platform</title>
        <meta name="description" content="Trade cryptocurrencies with advanced tools, low fees, and bank-level security. Spot, Futures, Options, P2P, NFTs & more." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
        {/* Header */}
        <header className="bg-black/50 backdrop-blur-md border-b border-gray-800 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-8">
                <Link href="/" className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
                    <span className="text-black font-bold text-lg">T</span>
                  </div>
                  <span className="text-white font-bold text-xl">TigerEx</span>
                </Link>
                
                <nav className="hidden md:flex space-x-6">
                  <Link href="/trade" className="text-gray-300 hover:text-white transition-colors">Trade</Link>
                  <Link href="/futures" className="text-gray-300 hover:text-white transition-colors">Futures</Link>
                  <Link href="/options" className="text-gray-300 hover:text-white transition-colors">Options</Link>
                  <Link href="/p2p" className="text-gray-300 hover:text-white transition-colors">P2P</Link>
                  <Link href="/nft" className="text-gray-300 hover:text-white transition-colors">NFT</Link>
                  <Link href="/copy-trading" className="text-gray-300 hover:text-white transition-colors">Copy Trading</Link>
                </nav>
              </div>

              <div className="flex items-center space-x-4">
                <button className="text-gray-300 hover:text-white transition-colors">
                  <GlobeAltIcon className="w-5 h-5" />
                </button>
                <Link href="/login" className="text-gray-300 hover:text-white transition-colors">
                  Log In
                </Link>
                <Link href="/register" className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-4 py-2 rounded-lg font-medium hover:from-yellow-500 hover:to-orange-600 transition-all">
                  Register
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <motion.div
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8 }}
                className="space-y-8"
              >
                <h1 className="text-5xl lg:text-6xl font-bold text-white leading-tight">
                  Trade Crypto Like a
                  <span className="bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent"> Pro</span>
                </h1>
                <p className="text-xl text-gray-300 leading-relaxed">
                  Advanced trading platform with spot, futures, options, P2P, NFTs, and copy trading. 
                  Join millions of traders worldwide with bank-level security and industry-leading features.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link href="/register" className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-8 py-4 rounded-lg font-bold text-lg hover:from-yellow-500 hover:to-orange-600 transition-all transform hover:scale-105">
                    Start Trading Now
                  </Link>
                  <Link href="/trade" className="border border-gray-600 text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-800 transition-all">
                    Explore Markets
                  </Link>
                </div>
                <div className="flex items-center space-x-8 text-sm text-gray-400">
                  <div className="flex items-center space-x-2">
                    <LightningBoltIcon className="w-5 h-5 text-yellow-400" />
                    <span>0.1% Trading Fees</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <ShieldCheckIcon className="w-5 h-5 text-green-400" />
                    <span>Bank-Level Security</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <GlobeAltIcon className="w-5 h-5 text-blue-400" />
                    <span>180+ Countries</span>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="relative"
              >
                <div className="bg-gray-800/50 backdrop-blur-md rounded-2xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-white font-bold text-lg">Live Markets</h3>
                    <Link href="/trade" className="text-yellow-400 hover:text-yellow-300 text-sm font-medium">
                      View All →
                    </Link>
                  </div>
                  <div className="space-y-4">
                    {tradingPairs.map((pair, index) => (
                      <motion.div
                        key={pair.symbol}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                        className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer"
                      >
                        <div>
                          <div className="text-white font-medium">{pair.symbol}</div>
                          <div className="text-gray-400 text-sm">{pair.volume} 24h</div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-medium">${pair.price}</div>
                          <div className={`text-sm font-medium ${pair.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                            {pair.change}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Services Grid */}
        <section className="py-20 bg-gray-900/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl font-bold text-white mb-4">Complete Trading Ecosystem</h2>
              <p className="text-xl text-gray-300">All the tools you need to trade, invest, and earn</p>
            </motion.div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {services.map((service, index) => (
                <motion.div
                  key={service.name}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="bg-gray-800/50 backdrop-blur-md rounded-xl p-6 border border-gray-700 hover:border-yellow-400/50 transition-all cursor-pointer group"
                >
                  <div className="text-3xl mb-3">{service.icon}</div>
                  <h3 className="text-white font-bold mb-2 group-hover:text-yellow-400 transition-colors">
                    {service.name}
                  </h3>
                  <p className="text-gray-400 text-sm">{service.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl font-bold text-white mb-4">Why Choose TigerEx?</h2>
              <p className="text-xl text-gray-300">Industry-leading features and security</p>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="bg-gray-800/50 backdrop-blur-md rounded-xl p-8 border border-gray-700 hover:border-gray-600 transition-all"
                >
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} flex items-center justify-center mb-6`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-white font-bold text-xl mb-4">{feature.title}</h3>
                  <p className="text-gray-300 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-20 bg-gradient-to-r from-yellow-400/10 to-orange-500/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { label: 'Trading Volume (24h)', value: '$12.5B+', icon: '📊' },
                { label: 'Registered Users', value: '50M+', icon: '👥' },
                { label: 'Countries Supported', value: '180+', icon: '🌍' },
                { label: 'Trading Pairs', value: '500+', icon: '💱' }
              ].map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="text-center"
                >
                  <div className="text-4xl mb-2">{stat.icon}</div>
                  <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
                  <div className="text-gray-400">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="bg-gradient-to-r from-yellow-400/20 to-orange-500/20 rounded-2xl p-12 border border-yellow-400/30"
            >
              <h2 className="text-4xl font-bold text-white mb-6">
                Ready to Start Trading?
              </h2>
              <p className="text-xl text-gray-300 mb-8">
                Join millions of traders and start your crypto journey today
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/register" className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-8 py-4 rounded-lg font-bold text-lg hover:from-yellow-500 hover:to-orange-600 transition-all transform hover:scale-105">
                  Create Account
                </Link>
                <Link href="/trade" className="border border-gray-600 text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-800 transition-all">
                  Start Trading
                </Link>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-black border-t border-gray-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
                    <span className="text-black font-bold text-lg">T</span>
                  </div>
                  <span className="text-white font-bold text-xl">TigerEx</span>
                </div>
                <p className="text-gray-400">
                  The world's leading cryptocurrency exchange platform
                </p>
              </div>
              
              <div>
                <h4 className="text-white font-bold mb-4">Trading</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/trade" className="hover:text-white transition-colors">Spot Trading</Link></li>
                  <li><Link href="/futures" className="hover:text-white transition-colors">Futures</Link></li>
                  <li><Link href="/options" className="hover:text-white transition-colors">Options</Link></li>
                  <li><Link href="/margin" className="hover:text-white transition-colors">Margin</Link></li>
                </ul>
              </div>
              
              <div>
                <h4 className="text-white font-bold mb-4">Services</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/p2p" className="hover:text-white transition-colors">P2P Trading</Link></li>
                  <li><Link href="/nft" className="hover:text-white transition-colors">NFT Marketplace</Link></li>
                  <li><Link href="/copy-trading" className="hover:text-white transition-colors">Copy Trading</Link></li>
                  <li><Link href="/staking" className="hover:text-white transition-colors">Staking</Link></li>
                </ul>
              </div>
              
              <div>
                <h4 className="text-white font-bold mb-4">Support</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/help" className="hover:text-white transition-colors">Help Center</Link></li>
                  <li><Link href="/api" className="hover:text-white transition-colors">API Docs</Link></li>
                  <li><Link href="/fees" className="hover:text-white transition-colors">Fees</Link></li>
                  <li><Link href="/contact" className="hover:text-white transition-colors">Contact</Link></li>
                </ul>
              </div>
            </div>
            
            <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
              <p>&copy; 2024 TigerEx. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default HomePage;
