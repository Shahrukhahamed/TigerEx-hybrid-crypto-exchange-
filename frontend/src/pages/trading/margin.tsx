import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Slider } from '@/components/ui/slider';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3, Zap, AlertTriangle, Shield } from 'lucide-react';

interface MarginPair {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  lastPrice: number;
  priceChange: number;
  priceChangePercent: number;
  volume: number;
  maxLeverage: number;
  marginRate: number;
  borrowRate: number;
}

interface MarginPosition {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  markPrice: number;
  liquidationPrice: number;
  unrealizedPnl: number;
  roe: number;
  margin: number;
  leverage: number;
  borrowedAmount: number;
  interestOwed: number;
}

interface MarginAccount {
  totalEquity: number;
  totalDebt: number;
  availableBalance: number;
  marginLevel: number;
  borrowingPower: number;
  dailyInterest: number;
}

const MarginTradingPage: React.FC = () => {
  const [pairs, setPairs] = useState<MarginPair[]>([]);
  const [selectedPair, setSelectedPair] = useState<MarginPair | null>(null);
  const [positions, setPositions] = useState<MarginPosition[]>([]);
  const [account, setAccount] = useState<MarginAccount | null>(null);
  
  // Order form state
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('LIMIT');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [leverage, setLeverage] = useState([2]);
  const [marginType, setMarginType] = useState<'ISOLATED' | 'CROSS'>('ISOLATED');
  
  // Borrow/Repay state
  const [borrowAsset, setBorrowAsset] = useState('USDT');
  const [borrowAmount, setBorrowAmount] = useState('');
  const [repayAsset, setRepayAsset] = useState('USDT');
  const [repayAmount, setRepayAmount] = useState('');
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    loadPairs();
    loadPositions();
    loadAccount();
  }, []);

  useEffect(() => {
    if (selectedPair) {
      setPrice(selectedPair.lastPrice.toString());
    }
  }, [selectedPair]);

  const loadPairs = async () => {
    try {
      setLoading(true);
      // Mock data - in production, fetch from API
      const mockPairs: MarginPair[] = [
        {
          symbol: 'BTCUSDT',
          baseAsset: 'BTC',
          quoteAsset: 'USDT',
          lastPrice: 43250.50,
          priceChange: 1250.30,
          priceChangePercent: 2.98,
          volume: 125000000,
          maxLeverage: 10,
          marginRate: 0.1,
          borrowRate: 0.0001
        },
        {
          symbol: 'ETHUSDT',
          baseAsset: 'ETH',
          quoteAsset: 'USDT',
          lastPrice: 2650.75,
          priceChange: -45.25,
          priceChangePercent: -1.68,
          volume: 95000000,
          maxLeverage: 5,
          marginRate: 0.2,
          borrowRate: 0.00015
        }
      ];
      setPairs(mockPairs);
      if (!selectedPair) {
        setSelectedPair(mockPairs[0]);
      }
    } catch (error) {
      console.error('Failed to load pairs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPositions = async () => {
    try {
      // Mock data - in production, fetch from API
      const mockPositions: MarginPosition[] = [
        {
          symbol: 'BTCUSDT',
          side: 'LONG',
          size: 0.5,
          entryPrice: 42000.00,
          markPrice: 43250.50,
          liquidationPrice: 38500.00,
          unrealizedPnl: 625.25,
          roe: 14.88,
          margin: 4200.00,
          leverage: 5,
          borrowedAmount: 16800.00,
          interestOwed: 2.45
        }
      ];
      setPositions(mockPositions);
    } catch (error) {
      console.error('Failed to load positions:', error);
    }
  };

  const loadAccount = async () => {
    try {
      // Mock data - in production, fetch from API
      const mockAccount: MarginAccount = {
        totalEquity: 25000.00,
        totalDebt: 15000.00,
        availableBalance: 8500.00,
        marginLevel: 1.67,
        borrowingPower: 42500.00,
        dailyInterest: 3.75
      };
      setAccount(mockAccount);
    } catch (error) {
      console.error('Failed to load account:', error);
    }
  };

  const placeOrder = async () => {
    if (!selectedPair || !quantity) return;
    
    try {
      setPlacingOrder(true);
      
      const orderData = {
        symbol: selectedPair.symbol,
        side: orderSide,
        type: orderType,
        quantity: parseFloat(quantity),
        price: orderType === 'LIMIT' ? parseFloat(price) : undefined,
        leverage: leverage[0],
        marginType: marginType,
        timeInForce: 'GTC'
      };

      // Mock API call - in production, call actual API
      console.log('Placing margin order:', orderData);
      
      // Reset form
      setQuantity('');
      if (orderType === 'MARKET') {
        setPrice('');
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

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
    return volume.toFixed(2);
  };

  const calculateMargin = () => {
    if (!selectedPair || !quantity || !price) return 0;
    return (parseFloat(quantity) * parseFloat(price)) / leverage[0];
  };

  const getMarginLevelColor = (level: number) => {
    if (level >= 2) return 'text-green-600';
    if (level >= 1.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMarginLevelProgress = (level: number) => {
    return Math.min((level / 3) * 100, 100);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Margin Trading</h1>
          <p className="text-gray-600">Trade with borrowed funds to amplify your positions</p>
        </div>

        {/* Account Overview */}
        {account && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Margin Account Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    ${formatNumber(account.totalEquity)}
                  </div>
                  <div className="text-sm text-gray-500">Total Equity</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    ${formatNumber(account.totalDebt)}
                  </div>
                  <div className="text-sm text-gray-500">Total Debt</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    ${formatNumber(account.availableBalance)}
                  </div>
                  <div className="text-sm text-gray-500">Available</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getMarginLevelColor(account.marginLevel)}`}>
                    {account.marginLevel.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500">Margin Level</div>
                  <Progress 
                    value={getMarginLevelProgress(account.marginLevel)} 
                    className="h-2 mt-1"
                  />
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    ${formatNumber(account.borrowingPower)}
                  </div>
                  <div className="text-sm text-gray-500">Borrowing Power</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    ${formatNumber(account.dailyInterest)}
                  </div>
                  <div className="text-sm text-gray-500">Daily Interest</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Trading Pairs */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Margin Trading Pairs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Pair</TableHead>
                    <TableHead>Last Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>Volume</TableHead>
                    <TableHead>Max Leverage</TableHead>
                    <TableHead>Borrow Rate</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pairs.map((pair) => (
                    <TableRow 
                      key={pair.symbol}
                      className={selectedPair?.symbol === pair.symbol ? 'bg-blue-50' : ''}
                    >
                      <TableCell className="font-medium">
                        <div>
                          <div className="font-semibold">{pair.symbol}</div>
                          <div className="text-sm text-gray-500">{pair.baseAsset}/{pair.quoteAsset}</div>
                        </div>
                      </TableCell>
                      <TableCell>${formatNumber(pair.lastPrice, 2)}</TableCell>
                      <TableCell>
                        <div className={`flex items-center gap-1 ${pair.priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {pair.priceChangePercent >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          {pair.priceChangePercent >= 0 ? '+' : ''}{pair.priceChangePercent.toFixed(2)}%
                        </div>
                      </TableCell>
                      <TableCell>{formatVolume(pair.volume)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{pair.maxLeverage}x</Badge>
                      </TableCell>
                      <TableCell>{(pair.borrowRate * 100).toFixed(3)}%/day</TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant={selectedPair?.symbol === pair.symbol ? "default" : "outline"}
                          onClick={() => setSelectedPair(pair)}
                        >
                          {selectedPair?.symbol === pair.symbol ? 'Selected' : 'Select'}
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
          {/* Order Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Place Order
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedPair && (
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="font-semibold text-lg">{selectedPair.symbol}</div>
                  <div className="text-sm text-gray-600">{selectedPair.baseAsset}/{selectedPair.quoteAsset}</div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Leverage: {leverage[0]}x
                </label>
                <Slider
                  value={leverage}
                  onValueChange={setLeverage}
                  max={selectedPair?.maxLeverage || 10}
                  min={1}
                  step={1}
                  className="w-full"
                />
              </div>

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
                  <label className="block text-sm font-medium text-gray-700 mb-2">Price</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  step="0.001"
                />
              </div>

              {selectedPair && quantity && (orderType === 'MARKET' || price) && (
                <div className="p-3 bg-gray-50 rounded-lg space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Margin Required:</span>
                    <span className="font-semibold">${formatNumber(calculateMargin(), 2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Borrowed Amount:</span>
                    <span className="font-semibold">
                      ${formatNumber(calculateMargin() * (leverage[0] - 1), 2)}
                    </span>
                  </div>
                </div>
              )}

              <Button
                className={`w-full ${orderSide === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                onClick={placeOrder}
                disabled={placingOrder || !selectedPair || !quantity || (orderType === 'LIMIT' && !price)}
              >
                {placingOrder ? 'Placing Order...' : `${orderSide} ${selectedPair?.baseAsset || ''}`}
              </Button>
            </CardContent>
          </Card>

          {/* Positions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Positions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {positions.map((position, index) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold">{position.symbol}</div>
                        <div className="text-sm text-gray-500">{position.leverage}x {position.side}</div>
                      </div>
                      <Badge variant={position.side === 'LONG' ? 'default' : 'destructive'}>
                        {position.side}
                      </Badge>
                    </div>
                    
                    <div className="text-sm space-y-1">
                      <div className="flex justify-between">
                        <span>Size:</span>
                        <span>{formatNumber(position.size, 4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Entry Price:</span>
                        <span>${formatNumber(position.entryPrice, 2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Unrealized PnL:</span>
                        <span className={position.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${formatNumber(position.unrealizedPnl, 2)} ({position.roe.toFixed(2)}%)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Borrowed:</span>
                        <span className="text-orange-600">${formatNumber(position.borrowedAmount, 2)}</span>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-2 text-red-600 hover:text-red-700"
                    >
                      Close Position
                    </Button>
                  </div>
                ))}

                {positions.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No open positions</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Borrow/Repay */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Borrow/Repay
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="borrow" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="borrow">Borrow</TabsTrigger>
                  <TabsTrigger value="repay">Repay</TabsTrigger>
                </TabsList>
                
                <TabsContent value="borrow" className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Asset</label>
                    <Select value={borrowAsset} onValueChange={setBorrowAsset}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USDT">USDT</SelectItem>
                        <SelectItem value="BTC">BTC</SelectItem>
                        <SelectItem value="ETH">ETH</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Amount</label>
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={borrowAmount}
                      onChange={(e) => setBorrowAmount(e.target.value)}
                      step="0.01"
                    />
                  </div>
                  
                  <Button 
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    disabled={!borrowAmount}
                  >
                    Borrow {borrowAsset}
                  </Button>
                </TabsContent>
                
                <TabsContent value="repay" className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Asset</label>
                    <Select value={repayAsset} onValueChange={setRepayAsset}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USDT">USDT</SelectItem>
                        <SelectItem value="BTC">BTC</SelectItem>
                        <SelectItem value="ETH">ETH</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Amount</label>
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={repayAmount}
                      onChange={(e) => setRepayAmount(e.target.value)}
                      step="0.01"
                    />
                  </div>
                  
                  <Button 
                    className="w-full bg-green-600 hover:bg-green-700"
                    disabled={!repayAmount}
                  >
                    Repay {repayAsset}
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        {/* Risk Warning */}
        <Card className="mt-6 border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-800 mb-1">Margin Trading Risk Warning</h3>
                <p className="text-sm text-red-700">
                  Margin trading involves substantial risk and may result in losses exceeding your initial investment. 
                  You may be subject to margin calls and forced liquidation. Interest charges apply to borrowed funds. 
                  Please ensure you understand the risks before trading on margin.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MarginTradingPage;
