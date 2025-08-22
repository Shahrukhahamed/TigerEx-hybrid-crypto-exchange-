'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

export function Statistics() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalVolume: 0,
    totalTrades: 0,
    uptime: 0
  })

  useEffect(() => {
    // Animate numbers on mount
    const targetStats = {
      totalUsers: 5000000,
      totalVolume: 250000000000,
      totalTrades: 1500000000,
      uptime: 99.99
    }

    const duration = 2000 // 2 seconds
    const steps = 60
    const stepDuration = duration / steps

    let currentStep = 0
    const interval = setInterval(() => {
      currentStep++
      const progress = currentStep / steps

      setStats({
        totalUsers: Math.floor(targetStats.totalUsers * progress),
        totalVolume: Math.floor(targetStats.totalVolume * progress),
        totalTrades: Math.floor(targetStats.totalTrades * progress),
        uptime: Math.min(targetStats.uptime * progress, targetStats.uptime)
      })

      if (currentStep >= steps) {
        clearInterval(interval)
        setStats(targetStats)
      }
    }, stepDuration)

    return () => clearInterval(interval)
  }, [])

  const formatNumber = (num: number) => {
    if (num >= 1e9) {
      return `${(num / 1e9).toFixed(1)}B`
    } else if (num >= 1e6) {
      return `${(num / 1e6).toFixed(1)}M`
    } else if (num >= 1e3) {
      return `${(num / 1e3).toFixed(1)}K`
    }
    return num.toLocaleString()
  }

  const statisticsData = [
    {
      label: 'Total Users',
      value: formatNumber(stats.totalUsers),
      description: 'Traders worldwide',
      color: 'from-blue-400 to-blue-600'
    },
    {
      label: '24h Volume',
      value: `$${formatNumber(stats.totalVolume)}`,
      description: 'Trading volume',
      color: 'from-green-400 to-green-600'
    },
    {
      label: 'Total Trades',
      value: formatNumber(stats.totalTrades),
      description: 'Executed successfully',
      color: 'from-purple-400 to-purple-600'
    },
    {
      label: 'Uptime',
      value: `${stats.uptime.toFixed(2)}%`,
      description: 'System reliability',
      color: 'from-orange-400 to-orange-600'
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
            Trusted by Millions
          </h2>
          <p className="text-gray-400 text-lg">
            Join the world's most advanced cryptocurrency trading platform
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {statisticsData.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="text-center"
            >
              <div className="card p-8 hover:bg-gray-700/50 transition-all duration-300 group">
                <div className={`w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-r ${stat.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                  <div className="w-8 h-8 bg-white/20 rounded-full" />
                </div>
                
                <div className="text-3xl sm:text-4xl font-bold text-white mb-2 group-hover:text-orange-400 transition-colors">
                  {stat.value}
                </div>
                
                <div className="text-lg font-semibold text-gray-300 mb-2">
                  {stat.label}
                </div>
                
                <div className="text-sm text-gray-500">
                  {stat.description}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Additional Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          <div className="card p-6 text-center">
            <div className="text-2xl font-bold text-white mb-2">500+</div>
            <div className="text-gray-400">Trading Pairs</div>
          </div>
          <div className="card p-6 text-center">
            <div className="text-2xl font-bold text-white mb-2">50+</div>
            <div className="text-gray-400">Supported Countries</div>
          </div>
          <div className="card p-6 text-center">
            <div className="text-2xl font-bold text-white mb-2">24/7</div>
            <div className="text-gray-400">Customer Support</div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}