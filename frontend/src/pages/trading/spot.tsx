import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3, Zap } from 'lucide-react';

interface TradingPair {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  lastPrice: number;
  priceChange: number;
  priceChangePercent: number;
  volume: number;
  high: number;
  low: number;
}

interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: string;
  quantity: number;
  price: number;
  status: string;
  createdAt: string;
}

interface OrderBookLevel {
  price: number;
  quantity: number;
  total: number;
}

const SpotTradingPage: React.FC = () => {
  const [selectedPair, setSelectedPair] = useState<TradingPair | null>(null);
  const [tradingPairs, setTradingPairs] = useState<TradingPair[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [orderBook, setOrderBook] = useState<{
    bids: OrderBookLevel[];
    asks: OrderBookLevel[];
  }>({ bids: [], asks: [] });
  
  // Order form state
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('LIMIT');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    loadTradingPairs();
    loadOrders();
  }, []);

  useEffect(() => {
    if (selectedPair) {
      loadOrderBook(selectedPair.symbol);
      setPrice(selectedPair.lastPrice.toString());
    }
  }, [selectedPair]);

  const loadTradingPairs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/spot/pairs');
      if (response.ok) {
        const pairs = await response.json();
        setTradingPairs(pairs);
        if (pairs.length > 0 && !selectedPair) {
          setSelectedPair(pairs[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load trading pairs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOrders = async () => {
    try {
      const response = await fetch('/api/v1/spot/orders');
      if (response.ok) {
        const userOrders = await response.json();
        setOrders(userOrders);
      }
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };

  const loadOrderBook = async (symbol: string) => {
    try {
      const response = await fetch(`/api/v1/spot/orderbook/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        
        // Process order book data
        const bids = data.bids.map((bid: any, index: number) => ({
          price: bid.price,
          quantity: bid.quantity,
          total: data.bids.slice(0, index + 1).reduce((sum: number, b: any) => sum + b.quantity, 0)
        }));
        
        const asks = data.asks.map((ask: any, index: number) => ({
          price: ask.price,
          quantity: ask.quantity,
          total: data.asks.slice(0, index + 1).reduce((sum: number, a: any) => sum + a.quantity, 0)
        }));
        
        setOrderBook({ bids, asks });
      }
    } catch (error) {
      console.error('Failed to load order book:', error);
    }
  };

  const placeOrder = async () => {
    if (!selectedPair || !quantity) return;
    
    try {
      setPlacingOrder(true);
      
      const orderData = {
        symbol: selectedPair.symbol,
        side: orderSide,
        order_type: orderType,
        quantity: parseFloat(quantity),
        price: orderType === 'LIMIT' ? parseFloat(price) : undefined,
        time_in_force: 'GTC'
      };

      const response = await fetch('/api/v1/spot/orders', {
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
        
        // Reload order book
        loadOrderBook(selectedPair.symbol);
      } else {
        const error = await response.json();
        alert(`Failed to place order: ${error.error}`);
      }
    } catch (error) {
      console.error('Failed to place order:', error);
      alert('Failed to place order');
    } finally {
      setPlacingOrder(false);
    }
  };

  const cancelOrder = async (orderId: string) => {
    try {
      const response = await fetch(`/api/v1/spot/orders/${orderId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setOrders(prev => prev.filter(order => order.id !== orderId));
        if (selectedPair) {
          loadOrderBook(selectedPair.symbol);
        }
      }
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

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
    return volume.toFixed(2);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Spot Trading</h1>
          <p className="text-gray-600">Trade cryptocurrencies with zero fees on selected pairs</p>
        </div>

        {/* Trading Pair Selector */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Market Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {selectedPair && (
                <>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      ${formatNumber(selectedPair.lastPrice, 4)}
                    </div>
                    <div className="text-sm text-gray-500">Last Price</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-2xl font-bold ${selectedPair.priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {selectedPair.priceChangePercent >= 0 ? '+' : ''}{selectedPair.priceChangePercent.toFixed(2)}%
                    </div>
                    <div className="text-sm text-gray-500">24h Change</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      ${formatNumber(selectedPair.high, 4)}
                    </div>
                    <div className="text-sm text-gray-500">24h High</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {formatVolume(selectedPair.volume)}
                    </div>
                    <div className="text-sm text-gray-500">24h Volume</div>
                  </div>
                </>
              )}
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Pair</TableHead>
                    <TableHead>Last Price</TableHead>
                    <TableHead>24h Change</TableHead>
                    <TableHead>24h Volume</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tradingPairs.map((pair) => (
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
                      <TableCell>${formatNumber(pair.lastPrice, 4)}</TableCell>
                      <TableCell>
                        <div className={`flex items-center gap-1 ${pair.priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {pair.priceChangePercent >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          {pair.priceChangePercent >= 0 ? '+' : ''}{pair.priceChangePercent.toFixed(2)}%
                        </div>
                      </TableCell>
                      <TableCell>{formatVolume(pair.volume)}</TableCell>
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
                    step="0.0001"
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
                  step="0.0001"
                />
              </div>

              {selectedPair && quantity && (orderType === 'MARKET' || price) && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span>Total:</span>
                    <span className="font-semibold">
                      ${formatNumber(
                        parseFloat(quantity) * (orderType === 'MARKET' ? selectedPair.lastPrice : parseFloat(price || '0')),
                        2
                      )}
                    </span>
                  </div>
                </div>
              )}

              <Button
                className={`w-full ${orderSide === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                onClick={placeOrder}
                disabled={placingOrder || !selectedPair || !quantity || (orderType === 'LIMIT' && !price)}
              >
                {placingOrder ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Placing Order...
                  </div>
                ) : (
                  `${orderSide} ${selectedPair?.baseAsset || ''}`
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Order Book */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Order Book
                {selectedPair && <Badge variant="outline">{selectedPair.symbol}</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Asks (Sell Orders) */}
                <div>
                  <div className="text-sm font-medium text-red-600 mb-2">Asks (Sell)</div>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {orderBook.asks.slice(0, 10).reverse().map((ask, index) => (
                      <div key={index} className="flex justify-between text-sm py-1 px-2 hover:bg-red-50 rounded">
                        <span className="text-red-600">${formatNumber(ask.price, 4)}</span>
                        <span>{formatNumber(ask.quantity, 4)}</span>
                        <span className="text-gray-500">{formatNumber(ask.total, 4)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Spread */}
                {orderBook.bids.length > 0 && orderBook.asks.length > 0 && (
                  <div className="text-center py-2 border-y">
                    <div className="text-sm text-gray-500">Spread</div>
                    <div className="font-semibold">
                      ${formatNumber(orderBook.asks[0].price - orderBook.bids[0].price, 4)}
                    </div>
                  </div>
                )}

                {/* Bids (Buy Orders) */}
                <div>
                  <div className="text-sm font-medium text-green-600 mb-2">Bids (Buy)</div>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {orderBook.bids.slice(0, 10).map((bid, index) => (
                      <div key={index} className="flex justify-between text-sm py-1 px-2 hover:bg-green-50 rounded">
                        <span className="text-green-600">${formatNumber(bid.price, 4)}</span>
                        <span>{formatNumber(bid.quantity, 4)}</span>
                        <span className="text-gray-500">{formatNumber(bid.total, 4)}</span>
                      </div>
                    ))}
                  </div>
                </div>
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
                {orders.filter(order => order.status === 'NEW' || order.status === 'PARTIALLY_FILLED').map((order) => (
                  <div key={order.id} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold">{order.symbol}</div>
                        <div className="text-sm text-gray-500">{order.type} • {order.side}</div>
                      </div>
                      <Badge variant={order.side === 'BUY' ? 'default' : 'destructive'}>
                        {order.side}
                      </Badge>
                    </div>
                    
                    <div className="text-sm space-y-1">
                      <div className="flex justify-between">
                        <span>Quantity:</span>
                        <span>{formatNumber(order.quantity, 4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Price:</span>
                        <span>${formatNumber(order.price, 4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <Badge variant="outline" className="text-xs">
                          {order.status}
                        </Badge>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-2 text-red-600 hover:text-red-700"
                      onClick={() => cancelOrder(order.id)}
                    >
                      Cancel Order
                    </Button>
                  </div>
                ))}

                {orders.filter(order => order.status === 'NEW' || order.status === 'PARTIALLY_FILLED').length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No open orders</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Order History */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Order History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Pair</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="text-sm">
                        {new Date(order.createdAt).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-medium">{order.symbol}</TableCell>
                      <TableCell>{order.type}</TableCell>
                      <TableCell>
                        <Badge variant={order.side === 'BUY' ? 'default' : 'destructive'}>
                          {order.side}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatNumber(order.quantity, 4)}</TableCell>
                      <TableCell>${formatNumber(order.price, 4)}</TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            order.status === 'FILLED' ? 'default' :
                            order.status === 'CANCELED' ? 'destructive' :
                            'outline'
                          }
                        >
                          {order.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SpotTradingPage;
