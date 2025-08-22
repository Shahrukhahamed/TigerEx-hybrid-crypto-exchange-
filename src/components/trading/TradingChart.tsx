'use client'

import { useEffect, useRef } from 'react'
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts'

interface TradingChartProps {
  symbol: string
}

export function TradingChart({ symbol }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<any>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: '#1f2937' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: '#4b5563',
      },
      timeScale: {
        borderColor: '#4b5563',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    const volumeSeries = chart.addHistogramSeries({
      color: '#6b7280',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    // Generate sample data
    const generateCandleData = () => {
      const data = []
      let time = Math.floor(Date.now() / 1000) - 86400 // 24 hours ago
      let price = 45000

      for (let i = 0; i < 288; i++) { // 5-minute intervals for 24 hours
        const open = price
        const high = open + Math.random() * 500
        const low = open - Math.random() * 500
        const close = low + Math.random() * (high - low)

        data.push({
          time,
          open,
          high,
          low,
          close,
        })

        time += 300 // 5 minutes
        price = close + (Math.random() - 0.5) * 100
      }

      return data
    }

    const generateVolumeData = () => {
      const data = []
      let time = Math.floor(Date.now() / 1000) - 86400

      for (let i = 0; i < 288; i++) {
        data.push({
          time,
          value: Math.random() * 1000 + 100,
          color: Math.random() > 0.5 ? '#22c55e' : '#ef4444',
        })
        time += 300
      }

      return data
    }

    const candleData = generateCandleData()
    const volumeData = generateVolumeData()

    candlestickSeries.setData(candleData)
    volumeSeries.setData(volumeData)

    chartRef.current = chart

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
      }
    }
  }, [symbol])

  return (
    <div className="h-full flex flex-col">
      {/* Chart Controls */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-white">{symbol}</h3>
            <div className="flex space-x-1">
              {['1m', '5m', '15m', '1h', '4h', '1d'].map((interval) => (
                <button
                  key={interval}
                  className="px-3 py-1 text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
                >
                  {interval}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors">
              📊
            </button>
            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors">
              ⚙️
            </button>
            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors">
              ⛶
            </button>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 p-4">
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>
    </div>
  )
}