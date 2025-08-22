'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { 
  ChartBarIcon, 
  ShieldCheckIcon, 
  GlobeAltIcon,
  BoltIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'

export function Hero() {
  const features = [
    {
      icon: BoltIcon,
      title: 'Ultra-Low Latency',
      description: 'Sub-millisecond order execution'
    },
    {
      icon: ShieldCheckIcon,
      title: 'Bank-Grade Security',
      description: '95% cold storage, multi-sig wallets'
    },
    {
      icon: GlobeAltIcon,
      title: 'Multi-Chain Support',
      description: '15+ blockchains, 25+ DEX protocols'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Shared Liquidity',
      description: 'Aggregated from top exchanges'
    }
  ]

  return (
    <section className="relative overflow-hidden py-20 sm:py-32">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-purple-500/20 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-orange-500/30 rounded-full blur-3xl animate-pulse" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold text-white mb-6">
              The Future of{' '}
              <span className="bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                Crypto Trading
              </span>
            </h1>
            
            <p className="text-xl sm:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              World's most advanced hybrid cryptocurrency exchange combining CEX and DEX functionality 
              with unlimited blockchain support and shared liquidity aggregation.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link
                href="/trade"
                className="btn btn-primary text-lg px-8 py-4 hover:scale-105 transform transition-all"
              >
                Start Trading
                <ArrowTrendingUpIcon className="ml-2 h-5 w-5" />
              </Link>
              <Link
                href="/learn"
                className="btn bg-white/10 text-white border border-white/20 hover:bg-white/20 text-lg px-8 py-4 hover:scale-105 transform transition-all"
              >
                Learn More
              </Link>
            </div>
          </motion.div>

          {/* Key Stats */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16"
          >
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-white mb-2">5M+</div>
              <div className="text-gray-400">Trades/Second</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-white mb-2">15+</div>
              <div className="text-gray-400">Blockchains</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-white mb-2">25+</div>
              <div className="text-gray-400">DEX Protocols</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-white mb-2">99.99%</div>
              <div className="text-gray-400">Uptime</div>
            </div>
          </motion.div>

          {/* Feature Cards */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 + index * 0.1 }}
                className="card p-6 hover:bg-gray-700/50 transition-colors group"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center mb-4 group-hover:bg-orange-500/30 transition-colors">
                    <feature.icon className="h-6 w-6 text-orange-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-gray-400 text-sm">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  )
}