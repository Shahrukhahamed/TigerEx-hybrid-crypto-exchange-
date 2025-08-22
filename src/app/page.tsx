import { Suspense } from 'react'
import { Header } from '@/components/layout/Header'
import { Hero } from '@/components/home/Hero'
import { Features } from '@/components/home/Features'
import { TradingPairs } from '@/components/home/TradingPairs'
import { Statistics } from '@/components/home/Statistics'
import { Footer } from '@/components/layout/Footer'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <Header />
      <main>
        <Suspense fallback={<LoadingSpinner />}>
          <Hero />
          <TradingPairs />
          <Features />
          <Statistics />
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}