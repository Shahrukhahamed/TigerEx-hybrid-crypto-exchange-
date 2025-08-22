const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
    
    // Get token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Authentication
  async login(email: string, password: string) {
    return this.request<{ token: string; user: any }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(userData: any) {
    return this.request<{ token: string; user: any }>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  // Market Data
  async getExchangeInfo() {
    return this.request<any>('/api/v1/exchange/info')
  }

  async getTicker(symbol?: string) {
    const endpoint = symbol ? `/api/v1/market/ticker/${symbol}` : '/api/v1/market/ticker'
    return this.request<any>(endpoint)
  }

  async getOrderBook(symbol: string, limit: number = 100) {
    return this.request<any>(`/api/v1/market/depth/${symbol}?limit=${limit}`)
  }

  async getRecentTrades(symbol: string, limit: number = 100) {
    return this.request<any>(`/api/v1/market/trades/${symbol}?limit=${limit}`)
  }

  async getKlines(symbol: string, interval: string, limit: number = 500) {
    return this.request<any>(`/api/v1/market/klines/${symbol}?interval=${interval}&limit=${limit}`)
  }

  // Account
  async getAccountInfo() {
    return this.request<any>('/api/v1/account/info')
  }

  async getBalance() {
    return this.request<any>('/api/v1/account/balance')
  }

  async getOrders(symbol?: string) {
    const endpoint = symbol ? `/api/v1/orders?symbol=${symbol}` : '/api/v1/orders'
    return this.request<any>(endpoint)
  }

  async getOpenOrders(symbol?: string) {
    const endpoint = symbol ? `/api/v1/orders/open?symbol=${symbol}` : '/api/v1/orders/open'
    return this.request<any>(endpoint)
  }

  async getTrades(symbol?: string, limit: number = 100) {
    const params = new URLSearchParams()
    if (symbol) params.append('symbol', symbol)
    params.append('limit', limit.toString())
    
    return this.request<any>(`/api/v1/account/trades?${params}`)
  }

  // Trading
  async placeOrder(orderData: any) {
    return this.request<any>('/api/v1/order', {
      method: 'POST',
      body: JSON.stringify(orderData),
    })
  }

  async cancelOrder(orderId: string) {
    return this.request<any>('/api/v1/order', {
      method: 'DELETE',
      body: JSON.stringify({ orderId }),
    })
  }

  async cancelAllOrders(symbol?: string) {
    const body = symbol ? JSON.stringify({ symbol }) : undefined
    return this.request<any>('/api/v1/orders', {
      method: 'DELETE',
      body,
    })
  }

  // Futures
  async getFuturesAccount() {
    return this.request<any>('/api/v1/futures/account')
  }

  async getFuturesPositions() {
    return this.request<any>('/api/v1/futures/positions')
  }

  async placeFuturesOrder(orderData: any) {
    return this.request<any>('/api/v1/futures/order', {
      method: 'POST',
      body: JSON.stringify(orderData),
    })
  }

  // Margin
  async getMarginAccount() {
    return this.request<any>('/api/v1/margin/account')
  }

  async marginBorrow(asset: string, amount: number) {
    return this.request<any>('/api/v1/margin/borrow', {
      method: 'POST',
      body: JSON.stringify({ asset, amount }),
    })
  }

  async marginRepay(asset: string, amount: number) {
    return this.request<any>('/api/v1/margin/repay', {
      method: 'POST',
      body: JSON.stringify({ asset, amount }),
    })
  }

  // Staking
  async getStakingProducts() {
    return this.request<any>('/api/v1/staking/products')
  }

  async stake(asset: string, amount: number, duration: number) {
    return this.request<any>('/api/v1/staking/stake', {
      method: 'POST',
      body: JSON.stringify({ asset, amount, duration }),
    })
  }

  // Copy Trading
  async getCopyTradingLeaders() {
    return this.request<any>('/api/v1/copy/leaders')
  }

  async followTrader(traderId: string, amount: number) {
    return this.request<any>('/api/v1/copy/follow', {
      method: 'POST',
      body: JSON.stringify({ traderId, amount }),
    })
  }
}

export const apiClient = new ApiClient(API_BASE_URL)