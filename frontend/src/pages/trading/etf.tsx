import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, PieChart, DollarSign, BarChart3, Target, Building2 } from 'lucide-react';

interface ETF {
  etf_id: string;
  symbol: string;
  name: string;
  description: string;
  category: string;
  expense_ratio: number;
  aum: number;
  inception_date: string;
  benchmark_index?: string;
  dividend_yield?: number;
  is_active: boolean;
}

interface ETFHolding {
  asset_symbol: string;
  asset_name: string;
  weight: number;
  market_value: number;
  sector?: string;
  country?: string;
}

interface ETFPerformance {
  etf_symbol: string;
  nav: number;
  market_price: number;
  premium_discount: number;
  daily_return: number;
  ytd_return: number;
  one_year_return: number;
  three_year_return?: number;
  five_year_return?: number;
  volatility: number;
  sharpe_ratio?: number;
  beta?: number;
}

interface ETFOrder {
  order_id: string;
  user_id: string;
  etf_symbol: string;
  side: 'BUY' | 'SELL';
  order_type: string;
  quantity: number;
  price?: number;
  status: string;
  created_at: string;
  filled_at?: string;
  filled_price?: number;
}

interface ETFPortfolio {
  user_id: string;
  etf_holdings: Array<{
    etf_symbol: string;
    quantity: number;
    avg_cost: number;
    current_price: number;
    market_value: number;
    unrealized_pnl: number;
  }>;
  total_value: number;
  total_cost: number;
  unrealized_pnl: number;
  realized_pnl: number;
  dividend_income: number;
}

const ETFTradingPage: React.FC = () => {
  const [etfs, setETFs] = useState<ETF[]>([]);
  const [selectedETF, setSelectedETF] = useState<ETF | null>(null);
  const [etfHoldings, setETFHoldings] = useState<ETFHolding[]>([]);
  const [etfPerformance, setETFPerformance] = useState<ETFPerformance | null>(null);
  const [portfolio, setPortfolio] = useState<ETFPortfolio | null>(null);
  const [orders, setOrders] = useState<ETFOrder[]>([]);
  
  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  
  // Order form state
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    loadETFs();
    loadPortfolio();
  }, []);

  useEffect(() => {
    if (selectedETF) {
      loadETFHoldings(selectedETF.symbol);
      loadETFPerformance(selectedETF.symbol);
    }
  }, [selectedETF]);

  const loadETFs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/etf/list');
      if (response.ok) {
        const etfList = await response.json();
        setETFs(etfList);
        if (etfList.length > 0 && !selectedETF) {
          setSelectedETF(etfList[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load ETFs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadETFHoldings = async (symbol: string) => {
    try {
      const response = await fetch(`/api/v1/etf/${symbol}/holdings`);
      if (response.ok) {
        const holdings = await response.json();
        setETFHoldings(holdings);
      }
    } catch (error) {
      console.error('Failed to load ETF holdings:', error);
    }
  };

  const loadETFPerformance = async (symbol: string) => {
    try {
      const response = await fetch(`/api/v1/etf/${symbol}/performance`);
      if (response.ok) {
        const performance = await response.json();
        setETFPerformance(performance);
        setPrice(performance.market_price.toString());
      }
    } catch (error) {
      console.error('Failed to load ETF performance:', error);
    }
  };

  const loadPortfolio = async () => {
    try {
      const response = await fetch('/api/v1/etf/portfolio');
      if (response.ok) {
        const portfolioData = await response.json();
        setPortfolio(portfolioData);
      }
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    }
  };

  const placeETFOrder = async () => {
    if (!selectedETF || !quantity) return;
    
    try {
      setPlacingOrder(true);
      
      const orderData = {
        etf_symbol: selectedETF.symbol,
        side: orderSide,
        order_type: orderType,
        quantity: parseInt(quantity),
        price: orderType === 'LIMIT' ? parseFloat(price) : undefined,
      };

      const response = await fetch('/api/v1/etf/order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      if (response.ok) {
        const newOrder = await response.json();
        setOrders(prev => [newOrder, ...prev]);
        
        // Reset form
        setQuantity('');
        if (orderType === 'MARKET') {
          setPrice('');
        }
        
        // Reload portfolio
        loadPortfolio();
      } else {
        const error = await response.json();
        alert(`Failed to place order: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to place order:', error);
      alert('Failed to place order');
    } finally {
      setPlacingOrder(false);
    }
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatLargeNumber = (num: number) => {
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`;
    return formatCurrency(num);
  };

  const filteredETFs = etfs.filter(etf => 
    categoryFilter === 'all' || etf.category === categoryFilter
  );

  const categories = ['all', ...Array.from(new Set(etfs.map(etf => etf.category)))];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">ETF Trading</h1>
          <p className="text-gray-600">Trade Exchange-Traded Funds with professional portfolio management</p>
        </div>

        {/* Portfolio Overview */}
        {portfolio && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Portfolio Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatCurrency(portfolio.total_value)}
                  </div>
                  <div className="text-sm text-gray-500">Total Value</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatCurrency(portfolio.total_cost)}
                  </div>
                  <div className="text-sm text-gray-500">Total Cost</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${portfolio.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(portfolio.unrealized_pnl)}
                  </div>
                  <div className="text-sm text-gray-500">Unrealized P&L</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${portfolio.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(portfolio.realized_pnl)}
                  </div>
                  <div className="text-sm text-gray-500">Realized P&L</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(portfolio.dividend_income)}
                  </div>
                  <div className="text-sm text-gray-500">Dividend Income</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ETF List and Filters */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                Available ETFs
              </CardTitle>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ETF</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>AUM</TableHead>
                    <TableHead>Expense Ratio</TableHead>
                    <TableHead>Dividend Yield</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredETFs.map((etf) => (
                    <TableRow 
                      key={etf.etf_id}
                      className={selectedETF?.etf_id === etf.etf_id ? 'bg-blue-50' : ''}
                    >
                      <TableCell>
                        <div>
                          <div className="font-semibold">{etf.symbol}</div>
                          <div className="text-sm text-gray-500 max-w-xs truncate">{etf.name}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {etf.category.charAt(0).toUpperCase() + etf.category.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatLargeNumber(etf.aum)}</TableCell>
                      <TableCell>{(etf.expense_ratio * 100).toFixed(2)}%</TableCell>
                      <TableCell>
                        {etf.dividend_yield ? `${etf.dividend_yield.toFixed(2)}%` : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant={selectedETF?.etf_id === etf.etf_id ? "default" : "outline"}
                          onClick={() => setSelectedETF(etf)}
                        >
                          {selectedETF?.etf_id === etf.etf_id ? 'Selected' : 'Select'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ETF Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                ETF Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedETF ? (
                <>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="font-bold text-xl">{selectedETF.symbol}</div>
                    <div className="text-sm text-gray-600 mt-1">{selectedETF.name}</div>
                    <div className="text-xs text-gray-500 mt-2">{selectedETF.description}</div>
                  </div>

                  {etfPerformance && (
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">NAV:</span>
                        <span className="font-semibold">{formatCurrency(etfPerformance.nav)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Market Price:</span>
                        <span className="font-semibold">{formatCurrency(etfPerformance.market_price)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Premium/Discount:</span>
                        <span className={`font-semibold ${etfPerformance.premium_discount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {etfPerformance.premium_discount >= 0 ? '+' : ''}{etfPerformance.premium_discount.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Daily Return:</span>
                        <span className={`font-semibold ${etfPerformance.daily_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {etfPerformance.daily_return >= 0 ? '+' : ''}{etfPerformance.daily_return.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">YTD Return:</span>
                        <span className={`font-semibold ${etfPerformance.ytd_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {etfPerformance.ytd_return >= 0 ? '+' : ''}{etfPerformance.ytd_return.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">1Y Return:</span>
                        <span className={`font-semibold ${etfPerformance.one_year_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {etfPerformance.one_year_return >= 0 ? '+' : ''}{etfPerformance.one_year_return.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Volatility:</span>
                        <span className="font-semibold">{etfPerformance.volatility.toFixed(2)}%</span>
                      </div>
                      {etfPerformance.sharpe_ratio && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Sharpe Ratio:</span>
                          <span className="font-semibold">{etfPerformance.sharpe_ratio.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>AUM:</span>
                      <span>{formatLargeNumber(selectedETF.aum)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Expense Ratio:</span>
                      <span>{(selectedETF.expense_ratio * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Inception:</span>
                      <span>{new Date(selectedETF.inception_date).toLocaleDateString()}</span>
                    </div>
                    {selectedETF.benchmark_index && (
                      <div className="flex justify-between text-sm">
                        <span>Benchmark:</span>
                        <span className="text-right">{selectedETF.benchmark_index}</span>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select an ETF to view details</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Order Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Place Order
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedETF && (
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="font-semibold text-lg">{selectedETF.symbol}</div>
                  <div className="text-sm text-gray-600">{selectedETF.name}</div>
                </div>
              )}

              <Tabs value={orderSide} onValueChange={(value) => setOrderSide(value as 'BUY' | 'SELL')}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="BUY" className="text-green-600">Buy</TabsTrigger>
                  <TabsTrigger value="SELL" className="text-red-600">Sell</TabsTrigger>
                </TabsList>
              </Tabs>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Order Type</label>
                <Select value={orderType} onValueChange={(value) => setOrderType(value as 'MARKET' | 'LIMIT')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MARKET">Market</SelectItem>
                    <SelectItem value="LIMIT">Limit</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {orderType === 'LIMIT' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Price per Share</label>
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    step="0.01"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Quantity (Shares)</label>
                <Input
                  type="number"
                  placeholder="0"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  step="1"
                  min="1"
                />
              </div>

              {selectedETF && quantity && etfPerformance && (orderType === 'MARKET' || price) && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Estimated Total:</span>
                    <span className="font-semibold">
                      {formatCurrency(
                        parseInt(quantity) * (orderType === 'MARKET' ? etfPerformance.market_price : parseFloat(price || '0'))
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Price per Share:</span>
                    <span>
                      {formatCurrency(orderType === 'MARKET' ? etfPerformance.market_price : parseFloat(price || '0'))}
                    </span>
                  </div>
                </div>
              )}

              <Button
                className={`w-full ${orderSide === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                onClick={placeETFOrder}
                disabled={placingOrder || !selectedETF || !quantity || (orderType === 'LIMIT' && !price)}
              >
                {placingOrder ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Placing Order...
                  </div>
                ) : (
                  `${orderSide} ${quantity || '0'} Shares`
                )}
              </Button>
            </CardContent>
          </Card>

          {/* ETF Holdings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Holdings
                {selectedETF && <Badge variant="outline">{selectedETF.symbol}</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {etfHoldings.map((holding, index) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold text-sm">{holding.asset_symbol}</div>
                        <div className="text-xs text-gray-500 truncate max-w-32">{holding.asset_name}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-sm">{holding.weight.toFixed(2)}%</div>
                        <div className="text-xs text-gray-500">{formatCurrency(holding.market_value)}</div>
                      </div>
                    </div>
                    
                    <Progress value={holding.weight} className="h-2" />
                    
                    {holding.sector && (
                      <div className="mt-2">
                        <Badge variant="outline" className="text-xs">
                          {holding.sector}
                        </Badge>
                      </div>
                    )}
                  </div>
                ))}

                {etfHoldings.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No holdings data available</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Portfolio Holdings */}
        {portfolio && portfolio.etf_holdings.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>My ETF Holdings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ETF</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead>Avg Cost</TableHead>
                      <TableHead>Current Price</TableHead>
                      <TableHead>Market Value</TableHead>
                      <TableHead>Unrealized P&L</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {portfolio.etf_holdings.map((holding, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{holding.etf_symbol}</TableCell>
                        <TableCell>{holding.quantity}</TableCell>
                        <TableCell>{formatCurrency(holding.avg_cost)}</TableCell>
                        <TableCell>{formatCurrency(holding.current_price)}</TableCell>
                        <TableCell>{formatCurrency(holding.market_value)}</TableCell>
                        <TableCell>
                          <div className={`flex items-center gap-1 ${holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {holding.unrealized_pnl >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                            {formatCurrency(holding.unrealized_pnl)}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ETFTradingPage;
