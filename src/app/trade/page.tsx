'use client'

import { Suspense } from 'react'
import { TradingInterface } from '@/components/trading/TradingInterface'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export default function TradePage() {
  return (
    <div className="min-h-screen bg-gray-900">
      <Suspense fallback={<LoadingSpinner />}>
        <TradingInterface />
      </Suspense>
    </div>
  )
}