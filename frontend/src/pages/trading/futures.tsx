import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Slider } from '@/components/ui/slider';
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3, Zap, AlertTriangle } from 'lucide-react';

interface FuturesContract {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  contractType: 'PERPETUAL' | 'QUARTERLY' | 'MONTHLY';
  lastPrice: number;
  priceChange: number;
  priceChangePercent: number;
  volume: number;
  openInterest: number;
  fundingRate: number;
  nextFundingTime: string;
  maxLeverage: number;
}

interface FuturesPosition {
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
}

interface FuturesOrder {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: string;
  quantity: number;
  price: number;
  stopPrice?: number;
  status: string;
  createdAt: string;
  leverage: number;
}

const FuturesTradingPage: React.FC = () => {
  const [contracts, setContracts] = useState<FuturesContract[]>([]);
  const [selectedContract, setSelectedContract] = useState<FuturesContract | null>(null);
  const [positions, setPositions] = useState<FuturesPosition[]>([]);
  const [orders, setOrders] = useState<FuturesOrder[]>([]);
  
  // Order form state
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'STOP' | 'STOP_MARKET'>('LIMIT');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [leverage, setLeverage] = useState([10]);
  const [marginType, setMarginType] = useState<'ISOLATED' | 'CROSS'>('ISOLATED');
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    loadContracts();
    loadPositions();
    loadOrders();
  }, []);

  useEffect(() => {
    if (selectedContract) {
      setPrice(selectedContract.lastPrice.toString());
    }
  }, [selectedContract]);

  const loadContracts = async () => {
    try {
      setLoading(true);
      // Mock data - in production, fetch from API
      const mockContracts: FuturesContract[] = [
        {
          symbol: 'BTCUSDT',
          baseAsset: 'BTC',
          quoteAsset: 'USDT',
          contractType: 'PERPETUAL',
          lastPrice: 43250.50,
          priceChange: 1250.30,
          priceChangePercent: 2.98,
          volume: 125000000,
          openInterest: 85000000,
          fundingRate: 0.0001,
          nextFundingTime: '2024-01-15T16:00:00Z',
          maxLeverage: 125
        },
        {
          symbol: 'ETHUSDT',
          baseAsset: 'ETH',
          quoteAsset: 'USDT',
          contractType: 'PERPETUAL',
          lastPrice: 2650.75,
          priceChange: -45.25,
          priceChangePercent: -1.68,
          volume: 95000000,
          openInterest: 65000000,
          fundingRate: -0.0002,
          nextFundingTime: '2024-01-15T16:00:00Z',
          maxLeverage: 100
        }
      ];
      setContracts(mockContracts);
      if (!selectedContract) {
        setSelectedContract(mockContracts[0]);
      }
    } catch (error) {
      console.error('Failed to load contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPositions = async () => {
    try {
      // Mock data - in production, fetch from API
      const mockPositions: FuturesPosition[] = [
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
          leverage: 10
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
      const mockOrders: FuturesOrder[] = [
        {
          id: '1',
          symbol: 'ETHUSDT',
          side: 'BUY',
          type: 'LIMIT',
          quantity: 2,
          price: 2600.00,
          status: 'NEW',
          createdAt: '2024-01-15T10:30:00Z',
          leverage: 20
        }
      ];
      setOrders(mockOrders);
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };

  const placeOrder = async () => {
    if (!selectedContract || !quantity) return;
    
    try {
      setPlacingOrder(true);
      
      const orderData = {
        symbol: selectedContract.symbol,
        side: orderSide,
        type: orderType,
        quantity: parseFloat(quantity),
        price: ['LIMIT', 'STOP'].includes(orderType) ? parseFloat(price) : undefined,
        stopPrice: ['STOP', 'STOP_MARKET'].includes(orderType) ? parseFloat(stopPrice) : undefined,
        leverage: leverage[0],
        marginType: marginType,
        timeInForce: 'GTC'
      };

      // Mock API call - in production, call actual API
      console.log('Placing futures order:', orderData);
      
      // Simulate API response
      const newOrder: FuturesOrder = {
        id: Date.now().toString(),
        symbol: selectedContract.symbol,
        side: orderSide,
        type: orderType,
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        stopPrice: stopPrice ? parseFloat(stopPrice) : undefined,
        status: 'NEW',
        createdAt: new Date().toISOString(),
        leverage: leverage[0]
      };
      
      setOrders(prev => [newOrder, ...prev]);
      
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
    if (!selectedContract || !quantity || !price) return 0;
    return (parseFloat(quantity) * parseFloat(price)) / leverage[0];
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Futures Trading</h1>
          <p className="text-gray-600">Trade cryptocurrency futures with up to 125x leverage</p>
        </div>

        {/* Contract Overview */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Futures Contracts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Mark Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>Volume</TableHead>
                    <TableHead>Open Interest</TableHead>
                    <TableHead>Funding Rate</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contracts.map((contract) => (
                    <TableRow 
                      key={contract.symbol}
                      className={selectedContract?.symbol === contract.symbol ? 'bg-blue-50' : ''}
                    >
                      <TableCell className="font-medium">
                        <div>
                          <div className="font-semibold">{contract.symbol}</div>
                          <div className="text-sm text-gray-500">{contract.baseAsset} Perpetual</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{contract.contractType}</Badge>
                      </TableCell>
                      <TableCell>${formatNumber(contract.lastPrice, 2)}</TableCell>
                      <TableCell>
                        <div className={`flex items-center gap-1 ${contract.priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {contract.priceChangePercent >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          {contract.priceChangePercent >= 0 ? '+' : ''}{contract.priceChangePercent.toFixed(2)}%
                        </div>
                      </TableCell>
                      <TableCell>{formatVolume(contract.volume)}</TableCell>
                      <TableCell>{formatVolume(contract.openInterest)}</TableCell>
                      <TableCell>
                        <span className={contract.fundingRate >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {(contract.fundingRate * 100).toFixed(4)}%
                        </span>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant={selectedContract?.symbol === contract.symbol ? "default" : "outline"}
                          onClick={() => setSelectedContract(contract)}
                        >
                          {selectedContract?.symbol === contract.symbol ? 'Selected' : 'Select'}
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
              {selectedContract && (
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="font-semibold text-lg">{selectedContract.symbol}</div>
                  <div className="text-sm text-gray-600">{selectedContract.baseAsset} Perpetual</div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Leverage: {leverage[0]}x
                </label>
                <Slider
                  value={leverage}
                  onValueChange={setLeverage}
                  max={selectedContract?.maxLeverage || 125}
                  min={1}
                  step={1}
                  className="w-full"
                />
              </div>

              <Tabs value={orderSide} onValueChange={(value) => setOrderSide(value as 'BUY' | 'SELL')}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="BUY" className="text-green-600">Long</TabsTrigger>
                  <TabsTrigger value="SELL" className="text-red-600">Short</TabsTrigger>
                </TabsList>
              </Tabs>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Order Type</label>
                <Select value={orderType} onValueChange={(value) => setOrderType(value as any)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MARKET">Market</SelectItem>
                    <SelectItem value="LIMIT">Limit</SelectItem>
                    <SelectItem value="STOP">Stop Limit</SelectItem>
                    <SelectItem value="STOP_MARKET">Stop Market</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {['LIMIT', 'STOP'].includes(orderType) && (
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

              {selectedContract && quantity && (orderType === 'MARKET' || price) && (
                <div className="p-3 bg-gray-50 rounded-lg space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Margin Required:</span>
                    <span className="font-semibold">${formatNumber(calculateMargin(), 2)}</span>
                  </div>
                </div>
              )}

              <Button
                className={`w-full ${orderSide === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                onClick={placeOrder}
                disabled={placingOrder || !selectedContract || !quantity}
              >
                {placingOrder ? 'Placing Order...' : `${orderSide === 'BUY' ? 'Long' : 'Short'} ${selectedContract?.baseAsset || ''}`}
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

          {/* Open Orders */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Open Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {orders.filter(order => order.status === 'NEW').map((order) => (
                  <div key={order.id} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold">{order.symbol}</div>
                        <div className="text-sm text-gray-500">{order.type} • {order.leverage}x</div>
                      </div>
                      <Badge variant={order.side === 'BUY' ? 'default' : 'destructive'}>
                        {order.side === 'BUY' ? 'LONG' : 'SHORT'}
                      </Badge>
                    </div>
                    
                    <div className="text-sm space-y-1">
                      <div className="flex justify-between">
                        <span>Quantity:</span>
                        <span>{formatNumber(order.quantity, 4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Price:</span>
                        <span>${formatNumber(order.price, 2)}</span>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-2 text-red-600 hover:text-red-700"
                    >
                      Cancel Order
                    </Button>
                  </div>
                ))}

                {orders.filter(order => order.status === 'NEW').length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No open orders</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Risk Warning */}
        <Card className="mt-6 border-yellow-200 bg-yellow-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-yellow-800 mb-1">Risk Warning</h3>
                <p className="text-sm text-yellow-700">
                  Futures trading involves substantial risk and may not be suitable for all investors. 
                  You could lose more than your initial investment. Please ensure you understand the risks involved.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FuturesTradingPage;
