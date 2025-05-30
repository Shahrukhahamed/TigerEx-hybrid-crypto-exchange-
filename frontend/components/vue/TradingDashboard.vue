<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
    <!-- Navigation Header -->
    <nav class="bg-black/20 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo -->
          <div class="flex items-center space-x-4">
            <div class="flex-shrink-0">
              <img class="h-8 w-auto" src="/logo-white.svg" alt="TigerEx" />
            </div>
            <div class="hidden md:block">
              <div class="ml-10 flex items-baseline space-x-4">
                <a href="#" class="text-white hover:text-orange-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Spot
                </a>
                <a href="#" class="text-gray-300 hover:text-orange-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Futures
                </a>
                <a href="#" class="text-gray-300 hover:text-orange-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Options
                </a>
                <a href="#" class="text-gray-300 hover:text-orange-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Copy Trading
                </a>
                <a href="#" class="text-gray-300 hover:text-orange-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  NFT
                </a>
                <a href="#" class="text-gray-300 hover:text-orange-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Earn
                </a>
              </div>
            </div>
          </div>

          <!-- User Menu -->
          <div class="flex items-center space-x-4">
            <div class="text-white text-sm">
              <span class="text-gray-400">Balance:</span>
              <span class="font-semibold ml-1">${{ totalBalance.toLocaleString() }}</span>
            </div>
            <button class="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              Deposit
            </button>
            <div class="relative">
              <button @click="showUserMenu = !showUserMenu" class="flex items-center space-x-2 text-white hover:text-orange-400 transition-colors">
                <img class="h-8 w-8 rounded-full" src="/avatar-placeholder.jpg" alt="User" />
                <ChevronDownIcon class="h-4 w-4" />
              </button>
              <!-- User dropdown menu would go here -->
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <!-- Market Overview -->
      <div class="mb-6">
        <div class="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 p-6">
          <h2 class="text-xl font-semibold text-white mb-4">Market Overview</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div v-for="market in topMarkets" :key="market.symbol" 
                 class="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-colors cursor-pointer"
                 @click="selectMarket(market.symbol)">
              <div class="flex items-center justify-between mb-2">
                <span class="text-white font-medium">{{ market.symbol }}</span>
                <span :class="market.change24h >= 0 ? 'text-green-400' : 'text-red-400'" class="text-sm">
                  {{ market.change24h >= 0 ? '+' : '' }}{{ market.change24h.toFixed(2) }}%
                </span>
              </div>
              <div class="text-white text-lg font-semibold">
                ${{ market.price.toLocaleString() }}
              </div>
              <div class="text-gray-400 text-sm">
                Vol: ${{ (market.volume24h / 1000000).toFixed(1) }}M
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Trading Interface -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <!-- Order Book & Recent Trades -->
        <div class="lg:col-span-1">
          <div class="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 h-[600px]">
            <div class="p-4 border-b border-white/10">
              <div class="flex space-x-4">
                <button @click="activeOrderBookTab = 'orderbook'" 
                        :class="activeOrderBookTab === 'orderbook' ? 'text-orange-400 border-orange-400' : 'text-gray-400 border-transparent'"
                        class="pb-2 border-b-2 transition-colors">
                  Order Book
                </button>
                <button @click="activeOrderBookTab = 'trades'" 
                        :class="activeOrderBookTab === 'trades' ? 'text-orange-400 border-orange-400' : 'text-gray-400 border-transparent'"
                        class="pb-2 border-b-2 transition-colors">
                  Recent Trades
                </button>
              </div>
            </div>
            
            <!-- Order Book -->
            <div v-if="activeOrderBookTab === 'orderbook'" class="p-4">
              <div class="space-y-1">
                <!-- Asks -->
                <div v-for="ask in orderBook.asks.slice(0, 10)" :key="ask.price" 
                     class="flex justify-between items-center py-1 hover:bg-red-500/10 transition-colors">
                  <span class="text-red-400 text-sm">${{ ask.price.toFixed(2) }}</span>
                  <span class="text-gray-300 text-sm">{{ ask.quantity.toFixed(4) }}</span>
                </div>
                
                <!-- Spread -->
                <div class="flex justify-center py-2 border-y border-white/10">
                  <span class="text-white font-semibold">${{ currentPrice.toFixed(2) }}</span>
                </div>
                
                <!-- Bids -->
                <div v-for="bid in orderBook.bids.slice(0, 10)" :key="bid.price" 
                     class="flex justify-between items-center py-1 hover:bg-green-500/10 transition-colors">
                  <span class="text-green-400 text-sm">${{ bid.price.toFixed(2) }}</span>
                  <span class="text-gray-300 text-sm">{{ bid.quantity.toFixed(4) }}</span>
                </div>
              </div>
            </div>

            <!-- Recent Trades -->
            <div v-if="activeOrderBookTab === 'trades'" class="p-4">
              <div class="space-y-1">
                <div v-for="trade in recentTrades" :key="trade.id" 
                     class="flex justify-between items-center py-1">
                  <span :class="trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'" class="text-sm">
                    ${{ trade.price.toFixed(2) }}
                  </span>
                  <span class="text-gray-300 text-sm">{{ trade.quantity.toFixed(4) }}</span>
                  <span class="text-gray-500 text-xs">{{ formatTime(trade.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chart -->
        <div class="lg:col-span-2">
          <div class="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 h-[600px]">
            <div class="p-4 border-b border-white/10">
              <div class="flex justify-between items-center">
                <div class="flex items-center space-x-4">
                  <h3 class="text-white font-semibold text-lg">{{ selectedSymbol }}</h3>
                  <div class="flex items-center space-x-2">
                    <span class="text-white text-xl font-bold">${{ currentPrice.toFixed(2) }}</span>
                    <span :class="priceChange24h >= 0 ? 'text-green-400' : 'text-red-400'" class="text-sm">
                      {{ priceChange24h >= 0 ? '+' : '' }}{{ priceChange24h.toFixed(2) }}%
                    </span>
                  </div>
                </div>
                <div class="flex space-x-2">
                  <button v-for="timeframe in timeframes" :key="timeframe"
                          @click="selectedTimeframe = timeframe"
                          :class="selectedTimeframe === timeframe ? 'bg-orange-500 text-white' : 'bg-white/10 text-gray-300 hover:bg-white/20'"
                          class="px-3 py-1 rounded text-sm transition-colors">
                    {{ timeframe }}
                  </button>
                </div>
              </div>
            </div>
            <div class="p-4 h-[500px]">
              <!-- TradingView Chart Component -->
              <div id="tradingview-chart" class="w-full h-full bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-400">TradingView Chart</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Trading Panel -->
        <div class="lg:col-span-1">
          <div class="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 h-[600px]">
            <div class="p-4 border-b border-white/10">
              <div class="flex space-x-1 bg-white/10 rounded-lg p-1">
                <button v-for="orderType in orderTypes" :key="orderType"
                        @click="selectedOrderType = orderType"
                        :class="selectedOrderType === orderType ? 'bg-orange-500 text-white' : 'text-gray-300 hover:text-white'"
                        class="flex-1 py-2 px-3 rounded text-sm font-medium transition-colors">
                  {{ orderType }}
                </button>
              </div>
            </div>

            <div class="p-4 space-y-4">
              <!-- Buy/Sell Toggle -->
              <div class="flex space-x-1 bg-white/10 rounded-lg p-1">
                <button @click="orderSide = 'BUY'"
                        :class="orderSide === 'BUY' ? 'bg-green-500 text-white' : 'text-gray-300 hover:text-white'"
                        class="flex-1 py-2 px-3 rounded text-sm font-medium transition-colors">
                  Buy
                </button>
                <button @click="orderSide = 'SELL'"
                        :class="orderSide === 'SELL' ? 'bg-red-500 text-white' : 'text-gray-300 hover:text-white'"
                        class="flex-1 py-2 px-3 rounded text-sm font-medium transition-colors">
                  Sell
                </button>
              </div>

              <!-- Order Form -->
              <div class="space-y-3">
                <!-- Price Input -->
                <div v-if="selectedOrderType !== 'Market'">
                  <label class="block text-gray-400 text-sm mb-1">Price</label>
                  <div class="relative">
                    <input v-model="orderPrice" type="number" step="0.01"
                           class="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 transition-colors"
                           placeholder="0.00" />
                    <span class="absolute right-3 top-2 text-gray-400 text-sm">USDT</span>
                  </div>
                </div>

                <!-- Quantity Input -->
                <div>
                  <label class="block text-gray-400 text-sm mb-1">Quantity</label>
                  <div class="relative">
                    <input v-model="orderQuantity" type="number" step="0.0001"
                           class="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 transition-colors"
                           placeholder="0.0000" />
                    <span class="absolute right-3 top-2 text-gray-400 text-sm">{{ baseAsset }}</span>
                  </div>
                </div>

                <!-- Percentage Buttons -->
                <div class="grid grid-cols-4 gap-2">
                  <button v-for="percentage in [25, 50, 75, 100]" :key="percentage"
                          @click="setPercentage(percentage)"
                          class="bg-white/10 hover:bg-white/20 text-gray-300 py-1 rounded text-sm transition-colors">
                    {{ percentage }}%
                  </button>
                </div>

                <!-- Total -->
                <div>
                  <label class="block text-gray-400 text-sm mb-1">Total</label>
                  <div class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                    <span class="text-white">{{ orderTotal.toFixed(2) }} USDT</span>
                  </div>
                </div>

                <!-- Available Balance -->
                <div class="text-sm text-gray-400">
                  Available: {{ availableBalance.toFixed(4) }} {{ orderSide === 'BUY' ? 'USDT' : baseAsset }}
                </div>

                <!-- Submit Button -->
                <button @click="placeOrder"
                        :disabled="!canPlaceOrder"
                        :class="orderSide === 'BUY' ? 'bg-green-500 hover:bg-green-600 disabled:bg-green-500/50' : 'bg-red-500 hover:bg-red-600 disabled:bg-red-500/50'"
                        class="w-full py-3 rounded-lg text-white font-medium transition-colors disabled:cursor-not-allowed">
                  {{ orderSide === 'BUY' ? 'Buy' : 'Sell' }} {{ baseAsset }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Open Orders & Trade History -->
      <div class="mt-6">
        <div class="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10">
          <div class="p-4 border-b border-white/10">
            <div class="flex space-x-6">
              <button v-for="tab in bottomTabs" :key="tab"
                      @click="activeBottomTab = tab"
                      :class="activeBottomTab === tab ? 'text-orange-400 border-orange-400' : 'text-gray-400 border-transparent'"
                      class="pb-2 border-b-2 transition-colors">
                {{ tab }}
              </button>
            </div>
          </div>

          <div class="p-4">
            <!-- Open Orders -->
            <div v-if="activeBottomTab === 'Open Orders'" class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="text-gray-400 text-sm">
                    <th class="text-left py-2">Symbol</th>
                    <th class="text-left py-2">Type</th>
                    <th class="text-left py-2">Side</th>
                    <th class="text-left py-2">Quantity</th>
                    <th class="text-left py-2">Price</th>
                    <th class="text-left py-2">Filled</th>
                    <th class="text-left py-2">Status</th>
                    <th class="text-left py-2">Time</th>
                    <th class="text-left py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="order in openOrders" :key="order.id" class="border-t border-white/10">
                    <td class="py-3 text-white">{{ order.symbol }}</td>
                    <td class="py-3 text-gray-300">{{ order.type }}</td>
                    <td class="py-3">
                      <span :class="order.side === 'BUY' ? 'text-green-400' : 'text-red-400'">
                        {{ order.side }}
                      </span>
                    </td>
                    <td class="py-3 text-gray-300">{{ order.quantity }}</td>
                    <td class="py-3 text-gray-300">${{ order.price }}</td>
                    <td class="py-3 text-gray-300">{{ (order.filledPercentage * 100).toFixed(1) }}%</td>
                    <td class="py-3">
                      <span class="px-2 py-1 rounded text-xs bg-yellow-500/20 text-yellow-400">
                        {{ order.status }}
                      </span>
                    </td>
                    <td class="py-3 text-gray-400 text-sm">{{ formatTime(order.createdAt) }}</td>
                    <td class="py-3">
                      <button @click="cancelOrder(order.id)"
                              class="text-red-400 hover:text-red-300 text-sm transition-colors">
                        Cancel
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Trade History -->
            <div v-if="activeBottomTab === 'Trade History'" class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="text-gray-400 text-sm">
                    <th class="text-left py-2">Symbol</th>
                    <th class="text-left py-2">Side</th>
                    <th class="text-left py-2">Quantity</th>
                    <th class="text-left py-2">Price</th>
                    <th class="text-left py-2">Total</th>
                    <th class="text-left py-2">Fee</th>
                    <th class="text-left py-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="trade in tradeHistory" :key="trade.id" class="border-t border-white/10">
                    <td class="py-3 text-white">{{ trade.symbol }}</td>
                    <td class="py-3">
                      <span :class="trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'">
                        {{ trade.side }}
                      </span>
                    </td>
                    <td class="py-3 text-gray-300">{{ trade.quantity }}</td>
                    <td class="py-3 text-gray-300">${{ trade.price }}</td>
                    <td class="py-3 text-gray-300">${{ trade.total }}</td>
                    <td class="py-3 text-gray-300">${{ trade.fee }}</td>
                    <td class="py-3 text-gray-400 text-sm">{{ formatTime(trade.timestamp) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Positions -->
            <div v-if="activeBottomTab === 'Positions'" class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="text-gray-400 text-sm">
                    <th class="text-left py-2">Symbol</th>
                    <th class="text-left py-2">Side</th>
                    <th class="text-left py-2">Size</th>
                    <th class="text-left py-2">Entry Price</th>
                    <th class="text-left py-2">Mark Price</th>
                    <th class="text-left py-2">PnL</th>
                    <th class="text-left py-2">Margin</th>
                    <th class="text-left py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="position in positions" :key="position.id" class="border-t border-white/10">
                    <td class="py-3 text-white">{{ position.symbol }}</td>
                    <td class="py-3">
                      <span :class="position.side === 'LONG' ? 'text-green-400' : 'text-red-400'">
                        {{ position.side }}
                      </span>
                    </td>
                    <td class="py-3 text-gray-300">{{ position.size }}</td>
                    <td class="py-3 text-gray-300">${{ position.entryPrice }}</td>
                    <td class="py-3 text-gray-300">${{ position.markPrice }}</td>
                    <td class="py-3">
                      <span :class="position.pnl >= 0 ? 'text-green-400' : 'text-red-400'">
                        ${{ position.pnl.toFixed(2) }}
                      </span>
                    </td>
                    <td class="py-3 text-gray-300">${{ position.margin }}</td>
                    <td class="py-3">
                      <button @click="closePosition(position.id)"
                              class="text-orange-400 hover:text-orange-300 text-sm transition-colors">
                        Close
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notifications -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <div v-for="notification in notifications" :key="notification.id"
           :class="notification.type === 'success' ? 'bg-green-500' : notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'"
           class="px-4 py-3 rounded-lg text-white shadow-lg transform transition-all duration-300">
        {{ notification.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

// Reactive data
const showUserMenu = ref(false)
const activeOrderBookTab = ref('orderbook')
const activeBottomTab = ref('Open Orders')
const selectedSymbol = ref('BTCUSDT')
const selectedTimeframe = ref('1H')
const selectedOrderType = ref('Limit')
const orderSide = ref('BUY')
const orderPrice = ref('')
const orderQuantity = ref('')
const currentPrice = ref(50000)
const priceChange24h = ref(2.5)
const totalBalance = ref(125000)
const availableBalance = ref(10000)

// Constants
const timeframes = ['1M', '5M', '15M', '1H', '4H', '1D', '1W']
const orderTypes = ['Limit', 'Market', 'Stop']
const bottomTabs = ['Open Orders', 'Trade History', 'Positions', 'Assets']

// Mock data
const topMarkets = ref([
  { symbol: 'BTCUSDT', price: 50000, change24h: 2.5, volume24h: 1200000000 },
  { symbol: 'ETHUSDT', price: 3000, change24h: -1.2, volume24h: 800000000 },
  { symbol: 'BNBUSDT', price: 300, change24h: 3.8, volume24h: 400000000 },
  { symbol: 'ADAUSDT', price: 0.5, change24h: 5.2, volume24h: 200000000 },
  { symbol: 'DOTUSDT', price: 8.5, change24h: -2.1, volume24h: 150000000 },
  { symbol: 'XRPUSDT', price: 0.6, change24h: 1.8, volume24h: 300000000 }
])

const orderBook = ref({
  asks: Array.from({ length: 20 }, (_, i) => ({
    price: 50000 + (i + 1) * 10,
    quantity: Math.random() * 10
  })),
  bids: Array.from({ length: 20 }, (_, i) => ({
    price: 50000 - (i + 1) * 10,
    quantity: Math.random() * 10
  }))
})

const recentTrades = ref(
  Array.from({ length: 50 }, (_, i) => ({
    id: i,
    price: 50000 + (Math.random() - 0.5) * 1000,
    quantity: Math.random() * 5,
    side: Math.random() > 0.5 ? 'BUY' : 'SELL',
    timestamp: Date.now() - i * 60000
  }))
)

const openOrders = ref([
  {
    id: 1,
    symbol: 'BTCUSDT',
    type: 'LIMIT',
    side: 'BUY',
    quantity: '0.1',
    price: '49500',
    filledPercentage: 0.3,
    status: 'PARTIALLY_FILLED',
    createdAt: Date.now() - 3600000
  },
  {
    id: 2,
    symbol: 'ETHUSDT',
    type: 'LIMIT',
    side: 'SELL',
    quantity: '2.5',
    price: '3100',
    filledPercentage: 0,
    status: 'NEW',
    createdAt: Date.now() - 1800000
  }
])

const tradeHistory = ref([
  {
    id: 1,
    symbol: 'BTCUSDT',
    side: 'BUY',
    quantity: '0.05',
    price: '49800',
    total: '2490',
    fee: '2.49',
    timestamp: Date.now() - 7200000
  },
  {
    id: 2,
    symbol: 'ETHUSDT',
    side: 'SELL',
    quantity: '1.0',
    price: '2950',
    total: '2950',
    fee: '2.95',
    timestamp: Date.now() - 14400000
  }
])

const positions = ref([
  {
    id: 1,
    symbol: 'BTCUSDT',
    side: 'LONG',
    size: '0.2',
    entryPrice: '48500',
    markPrice: '50000',
    pnl: 300,
    margin: '1000'
  }
])

const notifications = ref([])

// Computed properties
const baseAsset = computed(() => selectedSymbol.value.replace('USDT', ''))
const orderTotal = computed(() => {
  const price = selectedOrderType.value === 'Market' ? currentPrice.value : parseFloat(orderPrice.value) || 0
  const quantity = parseFloat(orderQuantity.value) || 0
  return price * quantity
})

const canPlaceOrder = computed(() => {
  const hasQuantity = parseFloat(orderQuantity.value) > 0
  const hasPrice = selectedOrderType.value === 'Market' || parseFloat(orderPrice.value) > 0
  const hasBalance = orderTotal.value <= availableBalance.value
  return hasQuantity && hasPrice && hasBalance
})

// Methods
const selectMarket = (symbol: string) => {
  selectedSymbol.value = symbol
  // Update current price and other market data
  const market = topMarkets.value.find(m => m.symbol === symbol)
  if (market) {
    currentPrice.value = market.price
    priceChange24h.value = market.change24h
  }
}

const setPercentage = (percentage: number) => {
  const balance = availableBalance.value
  const price = selectedOrderType.value === 'Market' ? currentPrice.value : parseFloat(orderPrice.value) || currentPrice.value
  
  if (orderSide.value === 'BUY') {
    const totalValue = (balance * percentage) / 100
    orderQuantity.value = (totalValue / price).toFixed(6)
  } else {
    orderQuantity.value = ((balance * percentage) / 100).toFixed(6)
  }
}

const placeOrder = async () => {
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Add to open orders
    const newOrder = {
      id: Date.now(),
      symbol: selectedSymbol.value,
      type: selectedOrderType.value.toUpperCase(),
      side: orderSide.value,
      quantity: orderQuantity.value,
      price: selectedOrderType.value === 'Market' ? currentPrice.value.toString() : orderPrice.value,
      filledPercentage: 0,
      status: 'NEW',
      createdAt: Date.now()
    }
    
    openOrders.value.unshift(newOrder)
    
    // Clear form
    orderPrice.value = ''
    orderQuantity.value = ''
    
    // Show notification
    showNotification('Order placed successfully', 'success')
  } catch (error) {
    showNotification('Failed to place order', 'error')
  }
}

const cancelOrder = async (orderId: number) => {
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Remove from open orders
    const index = openOrders.value.findIndex(order => order.id === orderId)
    if (index !== -1) {
      openOrders.value.splice(index, 1)
      showNotification('Order cancelled successfully', 'success')
    }
  } catch (error) {
    showNotification('Failed to cancel order', 'error')
  }
}

const closePosition = async (positionId: number) => {
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Remove from positions
    const index = positions.value.findIndex(position => position.id === positionId)
    if (index !== -1) {
      positions.value.splice(index, 1)
      showNotification('Position closed successfully', 'success')
    }
  } catch (error) {
    showNotification('Failed to close position', 'error')
  }
}

const showNotification = (message: string, type: 'success' | 'error' | 'info') => {
  const notification = {
    id: Date.now(),
    message,
    type
  }
  
  notifications.value.push(notification)
  
  // Auto remove after 3 seconds
  setTimeout(() => {
    const index = notifications.value.findIndex(n => n.id === notification.id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }, 3000)
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

// WebSocket connection for real-time data
let ws: WebSocket | null = null

const connectWebSocket = () => {
  ws = new WebSocket('ws://localhost:8080/ws')
  
  ws.onopen = () => {
    console.log('WebSocket connected')
    // Subscribe to market data
    ws?.send(JSON.stringify({
      method: 'subscribe',
      params: {
        channel: `ticker@${selectedSymbol.value.toLowerCase()}`
      }
    }))
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // Handle real-time updates
    if (data.channel?.includes('ticker')) {
      currentPrice.value = data.price
      priceChange24h.value = data.change24h
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected')
    // Reconnect after 3 seconds
    setTimeout(connectWebSocket, 3000)
  }
}

// Lifecycle hooks
onMounted(() => {
  connectWebSocket()
  
  // Simulate real-time price updates
  setInterval(() => {
    currentPrice.value += (Math.random() - 0.5) * 100
    priceChange24h.value += (Math.random() - 0.5) * 0.5
  }, 2000)
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Custom input styles */
input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}
</style>