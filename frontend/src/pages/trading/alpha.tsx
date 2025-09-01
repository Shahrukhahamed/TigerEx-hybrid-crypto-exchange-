import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Building2, DollarSign, BarChart3, TrendingUp, TrendingDown, Brain, Zap, Target, Star } from 'lucide-react';

interface AlphaStrategy {
  id: string;
  name: string;
  symbol: string;
  strategyType: 'MOMENTUM' | 'MEAN_REVERSION' | 'ARBITRAGE' | 'MARKET_MAKING';
  alphaScore: number;
  sharpeRatio: number;
  maxDrawdown: number;
  annualizedReturn: number;
  volatility: number;
  winRate: number;
  totalTrades: number;
  aum: number;
  minInvestment: number;
  performanceFee: number;
  managementFee: number;
  isActive: boolean;
}

interface AlphaPosition {
  strategyId: string;
  strategyName: string;
  investedAmount: number;
  currentValue: number;
  unrealizedPnl: number;
  roi: number;
  entryDate: string;
  allocation: number;
}

interface AlphaOrder {
  id: string;
  strategyId: string;
  strategyName: string;
  side: 'INVEST' | 'REDEEM';
  amount: number;
  status: string;
  createdAt: string;
}

interface AlphaPortfolio {
  totalInvested: number;
  totalValue: number;
  totalPnl: number;
  totalRoi: number;
  diversificationScore: number;
  riskScore: number;
}

const AlphaTradingPage: React.FC = () => {
  const [strategies, setStrategies] = useState<AlphaStrategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<AlphaStrategy | null>(null);
  const [positions, setPositions] = useState<AlphaPosition[]>([]);
  const [orders, setOrders] = useState<AlphaOrder[]>([]);
  const [portfolio, setPortfolio] = useState<AlphaPortfolio | null>(null);
  
  // Filters
  const [strategyTypeFilter, setStrategyTypeFilter] = useState<string>('ALL');
  const [minAlphaScore, setMinAlphaScore] = useState(0.1);
  const [sortBy, setSortBy] = useState<'alphaScore' | 'sharpeRatio' | 'annualizedReturn'>('alphaScore');
  
  // Order form state
  const [orderSide, setOrderSide] = useState<'INVEST' | 'REDEEM'>('INVEST');
  const [amount, setAmount] = useState('');
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    loadStrategies();
    loadPositions();
    loadOrders();
    loadPortfolio();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      // Mock data - in production, fetch from API
      const mockStrategies: AlphaStrategy[] = [
        {
          id: 'momentum_btc_1',
          name: 'BTC Momentum Alpha',
          symbol: 'BTC-MOM-ALPHA',
          strategyType: 'MOMENTUM',
          alphaScore: 0.85,
          sharpeRatio: 2.34,
          maxDrawdown: 0.12,
          annualizedReturn: 0.45,
          volatility: 0.18,
          winRate: 0.68,
          totalTrades: 1250,
          aum: 25000000,
          minInvestment: 1000,
          performanceFee: 0.20,
          managementFee: 0.02,
          isActive: true
        },
        {
          id: 'mean_reversion_eth_1',
          name: 'ETH Mean Reversion',
          symbol: 'ETH-MR-ALPHA',
          strategyType: 'MEAN_REVERSION',
          alphaScore: 0.72,
          sharpeRatio: 1.89,
          maxDrawdown: 0.08,
          annualizedReturn: 0.32,
          volatility: 0.15,
          winRate: 0.74,
          totalTrades: 2100,
          aum: 18000000,
          minInvestment: 500,
          performanceFee: 0.15,
          managementFee: 0.015,
          isActive: true
        },
        {
          id: 'arbitrage_multi_1',
          name: 'Multi-Exchange Arbitrage',
          symbol: 'MULTI-ARB-ALPHA',
          strategyType: 'ARBITRAGE',
          alphaScore: 0.91,
          sharpeRatio: 3.12,
          maxDrawdown: 0.05,
          annualizedReturn: 0.28,
          volatility: 0.09,
          winRate: 0.89,
          totalTrades: 5600,
          aum: 45000000,
          minInvestment: 2000,
          performanceFee: 0.25,
          managementFee: 0.025,
          isActive: true
        }
      ];
      
      let filtered = mockStrategies.filter(s => s.alphaScore >= minAlphaScore);
      
      if (strategyTypeFilter !== 'ALL') {
        filtered = filtered.filter(s => s.strategyType === strategyTypeFilter);
      }
      
      filtered.sort((a, b) => b[sortBy] - a[sortBy]);
      
      setStrategies(filtered);
      if (filtered.length > 0 && !selectedStrategy) {
        setSelectedStrategy(filtered[0]);
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPositions = async () => {
    try {
      // Mock data - in production, fetch from API
      const mockPositions: AlphaPosition[] = [
        {
          strategyId: 'momentum_btc_1',
          strategyName: 'BTC Momentum Alpha',
          investedAmount: 5000,
          currentValue: 6250,
          unrealizedPnl: 1250,
          roi: 0.25,
          entryDate: '2024-01-01T00:00:00Z',
          allocation: 0.35
        }
      ];
      setPositions(mockPositions);
    } catch (error) {
      console.error('Failed to load positions:', error);
    }
  };

  const loadOrders = async () => {
    try {
      // Mock data - in production, fetch from API
      const mockOrders: AlphaOrder[] = [
        {
          id: '1',
          strategyId: 'mean_reversion_eth_1',
          strategyName: 'ETH Mean Reversion',
          side: 'INVEST',
          amount: 2000,
          status: 'PENDING',
          createdAt: '2024-01-15T10:30:00Z'
        }
      ];
      setOrders(mockOrders);
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };

  const loadPortfolio = async () => {
    try {
      // Mock data - in production, fetch from API
      const mockPortfolio: AlphaPortfolio = {
        totalInvested: 8000,
        totalValue: 9670,
        totalPnl: 1670,
        totalRoi: 0.209,
        diversificationScore: 0.78,
        riskScore: 0.42
      };
      setPortfolio(mockPortfolio);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    }
  };

  const placeOrder = async () => {
    if (!selectedStrategy || !amount) return;
    
    try {
      setPlacingOrder(true);
      
      const orderData = {
        strategyId: selectedStrategy.id,
        side: orderSide,
        amount: parseFloat(amount)
      };

      // Mock API call - in production, call actual API
      console.log('Placing alpha order:', orderData);
      
      // Simulate API response
      const newOrder: AlphaOrder = {
        id: Date.now().toString(),
        strategyId: selectedStrategy.id,
        strategyName: selectedStrategy.name,
        side: orderSide,
        amount: parseFloat(amount),
        status: 'PENDING',
        createdAt: new Date().toISOString()
      };
      
      setOrders(prev => [newOrder, ...prev]);
      
      // Reset form
      setAmount('');
      
    } catch (error) {
      console.error('Failed to place order:', error);
      alert('Failed to place order');
    } finally {
      setPlacingOrder(false);
    }
  };

  const cancelOrder = async (orderId: string) => {
    try {
      // Mock API call - in production, call actual API
      console.log('Cancelling order:', orderId);
      setOrders(prev => prev.filter(order => order.id !== orderId));
    } catch (error) {
      console.error('Failed to cancel order:', error);
    }
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  };

  const formatPercent = (num: number, decimals: number = 2) => {
    return `${(num * 100).toFixed(decimals)}%`;
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
    return volume.toFixed(2);
  };

  const getStrategyTypeColor = (type: string) => {
    switch (type) {
      case 'MOMENTUM': return 'bg-blue-100 text-blue-800';
      case 'MEAN_REVERSION': return 'bg-green-100 text-green-800';
      case 'ARBITRAGE': return 'bg-purple-100 text-purple-800';
      case 'MARKET_MAKING': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlphaScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskScoreColor = (score: number) => {
    if (score <= 0.3) return 'text-green-600';
    if (score <= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Alpha Trading</h1>
          <p className="text-gray-600">Invest in AI-powered alpha generation strategies</p>
        </div>

        {/* Portfolio Overview */}
        {portfolio && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                Alpha Portfolio Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    ${formatNumber(portfolio.totalInvested)}
                  </div>
                  <div className="text-sm text-gray-500">Total Invested</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    ${formatNumber(portfolio.totalValue)}
                  </div>
                  <div className="text-sm text-gray-500">Current Value</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${portfolio.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${formatNumber(portfolio.totalPnl)}
                  </div>
                  <div className="text-sm text-gray-500">Total P&L</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${portfolio.totalRoi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(portfolio.totalRoi)}
                  </div>
                  <div className="text-sm text-gray-500">Total ROI</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {formatPercent(portfolio.diversificationScore)}
                  </div>
                  <div className="text-sm text-gray-500">Diversification</div>
                  <Progress value={portfolio.diversificationScore * 100} className="h-2 mt-1" />
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getRiskScoreColor(portfolio.riskScore)}`}>
                    {formatPercent(portfolio.riskScore)}
                  </div>
                  <div className="text-sm text-gray-500">Risk Score</div>
                  <Progress value={portfolio.riskScore * 100} className="h-2 mt-1" />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Strategy Type</label>
                <Select value={strategyTypeFilter} onValueChange={setStrategyTypeFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Types</SelectItem>
                    <SelectItem value="MOMENTUM">Momentum</SelectItem>
                    <SelectItem value="MEAN_REVERSION">Mean Reversion</SelectItem>
                    <SelectItem value="ARBITRAGE">Arbitrage</SelectItem>
                    <SelectItem value="MARKET_MAKING">Market Making</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Alpha Score</label>
                <Select value={minAlphaScore.toString()} onValueChange={(value) => setMinAlphaScore(parseFloat(value))}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.1">0.1+</SelectItem>
                    <SelectItem value="0.5">0.5+</SelectItem>
                    <SelectItem value="0.7">0.7+</SelectItem>
                    <SelectItem value="0.8">0.8+</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
                <Select value={sortBy} onValueChange={(value) => setSortBy(value as any)}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="alphaScore">Alpha Score</SelectItem>
                    <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                    <SelectItem value="annualizedReturn">Annual Return</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alpha Strategies */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Alpha Strategies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Alpha Score</TableHead>
                    <TableHead>Sharpe Ratio</TableHead>
                    <TableHead>Annual Return</TableHead>
                    <TableHead>Max Drawdown</TableHead>
                    <TableHead>Win Rate</TableHead>
                    <TableHead>AUM</TableHead>
                    <TableHead>Min Investment</TableHead>
                    <TableHead>Fees</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {strategies.map((strategy) => (
                    <TableRow 
                      key={strategy.id}
                      className={selectedStrategy?.id === strategy.id ? 'bg-blue-50' : ''}
                    >
                      <TableCell className="font-medium">
                        <div>
                          <div className="font-semibold">{strategy.name}</div>
                          <div className="text-sm text-gray-500">{strategy.symbol}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStrategyTypeColor(strategy.strategyType)}>
                          {strategy.strategyType.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className={`font-semibold ${getAlphaScoreColor(strategy.alphaScore)}`}>
                            {strategy.alphaScore.toFixed(2)}
                          </span>
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <Star 
                                key={i} 
                                className={`h-3 w-3 ${i < Math.floor(strategy.alphaScore * 5) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
                              />
                            ))}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="font-semibold">{strategy.sharpeRatio.toFixed(2)}</TableCell>
                      <TableCell className="text-green-600 font-semibold">
                        {formatPercent(strategy.annualizedReturn)}
                      </TableCell>
                      <TableCell className="text-red-600">
                        {formatPercent(strategy.maxDrawdown)}
                      </TableCell>
                      <TableCell>{formatPercent(strategy.winRate)}</TableCell>
                      <TableCell>${formatVolume(strategy.aum)}</TableCell>
                      <TableCell>${formatNumber(strategy.minInvestment, 0)}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>Mgmt: {formatPercent(strategy.managementFee)}</div>
                          <div>Perf: {formatPercent(strategy.performanceFee)}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant={selectedStrategy?.id === strategy.id ? "default" : "outline"}
                          onClick={() => setSelectedStrategy(strategy)}
                        >
                          {selectedStrategy?.id === strategy.id ? 'Selected' : 'Select'}
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
          {/* Investment Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Invest/Redeem
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedStrategy && (
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="font-semibold text-sm">{selectedStrategy.name}</div>
                  <div className="text-xs text-gray-600">{selectedStrategy.symbol}</div>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <Badge className={getStrategyTypeColor(selectedStrategy.strategyType)}>
                      {selectedStrategy.strategyType.replace('_', ' ')}
                    </Badge>
                    <span className={`text-sm font-semibold ${getAlphaScoreColor(selectedStrategy.alphaScore)}`}>
                      α {selectedStrategy.alphaScore.toFixed(2)}
                    </span>
                  </div>
                </div>
              )}

              <Tabs value={orderSide} onValueChange={(value) => setOrderSide(value as 'INVEST' | 'REDEEM')}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="INVEST" className="text-green-600">Invest</TabsTrigger>
                  <TabsTrigger value="REDEEM" className="text-red-600">Redeem</TabsTrigger>
                </TabsList>
              </Tabs>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Amount (USD)</label>
                <Input
                  type="number"
                  placeholder="1000"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  step="100"
                  min={selectedStrategy?.minInvestment || 0}
                />
                {selectedStrategy && (
                  <div className="text-xs text-gray-500 mt-1">
                    Min: ${formatNumber(selectedStrategy.minInvestment, 0)}
                  </div>
                )}
              </div>

              {selectedStrategy && amount && (
                <div className="p-3 bg-gray-50 rounded-lg space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Management Fee:</span>
                    <span className="font-semibold">
                      {formatPercent(selectedStrategy.managementFee)} annually
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Performance Fee:</span>
                    <span className="font-semibold">
                      {formatPercent(selectedStrategy.performanceFee)} on profits
                    </span>
                  </div>
                  {orderSide === 'INVEST' && (
                    <div className="flex justify-between text-sm">
                      <span>Expected Annual Return:</span>
                      <span className="font-semibold text-green-600">
                        {formatPercent(selectedStrategy.annualizedReturn)}
                      </span>
                    </div>
                  )}
                </div>
              )}

              <Button
                className={`w-full ${orderSide === 'INVEST' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                onClick={placeOrder}
                disabled={placingOrder || !selectedStrategy || !amount || parseFloat(amount) < (selectedStrategy?.minInvestment || 0)}
              >
                {placingOrder ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Processing...
                  </div>
                ) : (
                  `${orderSide === 'INVEST' ? 'Invest' : 'Redeem'} $${amount || '0'}`
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Positions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Alpha Positions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {positions.map((position, index) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold text-sm">{position.strategyName}</div>
                        <div className="text-xs text-gray-500">
                          {formatPercent(position.allocation)} allocation
                        </div>
                      </div>
                      <Badge variant="outline">
                        {formatPercent(position.roi)}
                      </Badge>
                    </div>
                    
                    <div className="text-xs space-y-1">
                      <div className="flex justify-between">
                        <span>Invested:</span>
                        <span>${formatNumber(position.investedAmount)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Current Value:</span>
                        <span>${formatNumber(position.currentValue)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>P&L:</span>
                        <span className={position.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${formatNumber(position.unrealizedPnl)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Entry: {new Date(position.entryDate).toLocaleDateString()}
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-2 text-xs"
                    >
                      Redeem Position
                    </Button>
                  </div>
                ))}

                {positions.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">No alpha positions</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Pending Orders */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Pending Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {orders.filter(order => order.status === 'PENDING').map((order) => (
                  <div key={order.id} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold text-sm">{order.strategyName}</div>
                        <div className="text-xs text-gray-500">
                          {order.side} order
                        </div>
                      </div>
                      <Badge variant={order.side === 'INVEST' ? 'default' : 'destructive'}>
                        {order.side}
                      </Badge>
                    </div>
                    
                    <div className="text-xs space-y-1">
                      <div className="flex justify-between">
                        <span>Amount:</span>
                        <span>${formatNumber(order.amount)}</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Created: {new Date(order.createdAt).toLocaleDateString()}
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-2 text-red-600 hover:text-red-700 text-xs"
                      onClick={() => cancelOrder(order.id)}
                    >
                      Cancel Order
                    </Button>
                  </div>
                ))}

                {orders.filter(order => order.status === 'PENDING').length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">No pending orders</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AlphaTradingPage;
