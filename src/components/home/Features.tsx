'use client'

import { motion } from 'framer-motion'
import {
  BoltIcon,
  ShieldCheckIcon,
  GlobeAltIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  CogIcon,
  UserGroupIcon,
  AcademicCapIcon,
  DevicePhoneMobileIcon,
  CloudIcon,
  LockClosedIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline'

export function Features() {
  const features = [
    {
      icon: BoltIcon,
      title: 'Ultra-Low Latency Trading',
      description: 'Sub-millisecond order execution with our C++ matching engine processing 5M+ trades per second.',
      color: 'from-yellow-400 to-orange-500'
    },
    {
      icon: GlobeAltIcon,
      title: 'Multi-Chain DEX Integration',
      description: 'Trade across 15+ blockchains and 25+ DEX protocols with unified liquidity aggregation.',
      color: 'from-blue-400 to-purple-500'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Shared Liquidity Pools',
      description: 'Access combined liquidity from Binance, Bybit, OKX, and major DEX protocols.',
      color: 'from-green-400 to-emerald-500'
    },
    {
      icon: ShieldCheckIcon,
      title: 'Bank-Grade Security',
      description: '95% cold storage, multi-signature wallets, and comprehensive insurance coverage.',
      color: 'from-red-400 to-pink-500'
    },
    {
      icon: ChartBarIcon,
      title: 'Advanced Trading Tools',
      description: '30+ order types, algorithmic trading, copy trading, and professional analytics.',
      color: 'from-indigo-400 to-blue-500'
    },
    {
      icon: CogIcon,
      title: 'Custom Blockchain Support',
      description: 'Deploy and integrate custom EVM and Web3 blockchains with full trading support.',
      color: 'from-purple-400 to-indigo-500'
    },
    {
      icon: UserGroupIcon,
      title: 'Institutional Services',
      description: 'Prime brokerage, OTC trading, custody services, and white-label solutions.',
      color: 'from-teal-400 to-cyan-500'
    },
    {
      icon: DevicePhoneMobileIcon,
      title: 'Mobile-First Design',
      description: 'Native iOS and Android apps with biometric authentication and offline capabilities.',
      color: 'from-orange-400 to-red-500'
    },
    {
      icon: AcademicCapIcon,
      title: 'Educational Platform',
      description: 'Comprehensive trading academy, certifications, and paper trading for learning.',
      color: 'from-emerald-400 to-teal-500'
    },
    {
      icon: CloudIcon,
      title: 'Global Infrastructure',
      description: 'Multi-cloud deployment across AWS, Google Cloud, and edge locations worldwide.',
      color: 'from-sky-400 to-blue-500'
    },
    {
      icon: LockClosedIcon,
      title: 'Regulatory Compliance',
      description: 'Licensed in 50+ jurisdictions with full KYC/AML and regulatory reporting.',
      color: 'from-violet-400 to-purple-500'
    },
    {
      icon: RocketLaunchIcon,
      title: 'Token Launchpad',
      description: 'Comprehensive token listing platform for both CEX and DEX with automated compliance.',
      color: 'from-pink-400 to-rose-500'
    }
  ]

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Everything You Need to Trade
          </h2>
          <p className="text-gray-400 text-lg max-w-3xl mx-auto">
            TigerEx combines the best features from Binance, Bybit, OKX, and other major exchanges 
            into one revolutionary platform with unlimited blockchain support.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group"
            >
              <div className="card p-8 h-full hover:bg-gray-700/50 transition-all duration-300 group-hover:scale-105">
                <div className="flex flex-col h-full">
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} p-3 mb-6 group-hover:scale-110 transition-transform`}>
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  
                  <h3 className="text-xl font-semibold text-white mb-4 group-hover:text-orange-400 transition-colors">
                    {feature.title}
                  </h3>
                  
                  <p className="text-gray-400 leading-relaxed flex-grow">
                    {feature.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Call to Action */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="text-center mt-16"
        >
          <div className="card p-8 bg-gradient-to-r from-orange-500/20 to-red-500/20 border-orange-500/30">
            <h3 className="text-2xl font-bold text-white mb-4">
              Ready to Experience the Future of Trading?
            </h3>
            <p className="text-gray-300 mb-6">
              Join millions of traders on the world's most advanced cryptocurrency exchange
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="btn btn-primary text-lg px-8 py-3 hover:scale-105 transform transition-all">
                Start Trading Now
              </button>
              <button className="btn bg-white/10 text-white border border-white/20 hover:bg-white/20 text-lg px-8 py-3 hover:scale-105 transform transition-all">
                View Documentation
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}