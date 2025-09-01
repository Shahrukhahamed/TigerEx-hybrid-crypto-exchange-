import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Target, DollarSign, BarChart3, AlertTriangle, Calculator } from 'lucide-react';

interface OptionContract {
  symbol: string;
  underlying: string;
  optionType: 'CALL' | 'PUT';
  strikePrice: number;
  expiryDate: string;
  exerciseStyle: 'EUROPEAN' | 'AMERICAN';
  lastPrice: number;
  bid: number;
  ask: number;
  volume: number;
  openInterest: number;
  impliedVolatility: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

interface OptionPosition {
  symbol: string;
  optionType: 'CALL' | 'PUT';
  side: 'LONG' | 'SHORT';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  strikePrice: number;
  expiryDate: string;
  unrealizedPnl: number;
  delta: number;
  theta: number;
}

const OptionsTradingPage: React.FC = () => {
  const [contracts, setContracts] = useState<OptionContract[]>([]);
  const [selectedContract, setSelectedContract] = useState<OptionContract | null>(null);
  const [positions, setPositions] = useState<OptionPosition[]>([]);
  
  // Filters
  const [underlyingFilter, setUnderlyingFilter] = useState('BTC');
  const [optionTypeFilter, setOptionTypeFilter] = useState<'ALL' | 'CALL' | 'PUT'>('ALL');
  
  // Order form state
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    loadContracts();
    loadPositions();
  }, [underlyingFilter, optionTypeFilter]);

  useEffect(() => {
    if (selectedContract) {
      setPrice(((selectedContract.bid + selectedContract.ask) / 2).toString());
    }
  }, [selectedContract]);

  const loadContracts = async () => {
    try {
      setLoading(true);
      // Mock data - in production, fetch from API
      const mockContracts: OptionContract[] = [
        {
          symbol: 'BTC-240315-45000-C',
          underlying: 'BTC',
          optionType: 'CALL',
          strikePrice: 45000,
          expiryDate: '2024-03-15T08:00:00Z',
          exerciseStyle: 'EUROPEAN',
          lastPrice: 1250.50,
          bid: 1240.00,
          ask: 1260.00,
          volume: 125,
          openInterest: 850,
          impliedVolatility: 0.65,
          delta: 0.6234,
          gamma: 0.0001,
          theta: -12.45,
          vega: 18.75
        },
        {
          symbol: 'BTC-240315-45000-P',
          underlying: 'BTC',
          optionType: 'PUT',
          strikePrice: 45000,
          expiryDate: '2024-03-15T08:00:00Z',
          exerciseStyle: 'EUROPEAN',
          lastPrice: 875.25,
          bid: 870.00,
          ask: 880.00,
          volume: 95,
          openInterest: 650,
          impliedVolatility: 0.68,
          delta: -0.3766,
          gamma: 0.0001,
          theta: -10.25,
          vega: 16.85
        }
      ];
      
      let filtered = mockContracts;
      if (underlyingFilter !== 'ALL') {
        filtered = filtered.filter(c => c.underlying === underlyingFilter);
      }
      if (optionTypeFilter !== 'ALL') {
        filtered = filtered.filter(c => c.optionType === optionTypeFilter);
      }
      
      setContracts(filtered);
      if (filtered.length > 0 && !selectedContract) {
        setSelectedContract(filtered[0]);
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
      const mockPositions: OptionPosition[] = [
        {
          symbol: 'BTC-240315-45000-C',
          optionType: 'CALL',
          side: 'LONG',
          quantity: 2,
          entryPrice: 1200.00,
          currentPrice: 1250.50,
          strikePrice: 45000,
          expiryDate: '2024-03-15T08:00:00Z',
          unrealizedPnl: 101.00,
          delta: 0.6234,
          theta: -12.45
        }
      ];
      setPositions(mockPositions);
    } catch (error) {
      console.error('Failed to load positions:', error);
    }
  };

  const placeOrder = async () => {
    if (!selectedContract || !quantity || !price) return;
    
    try {
      setPlacingOrder(true);
      
      const orderData = {
        symbol: selectedContract.symbol,
        optionType: selectedContract.optionType,
        side: orderSide,
        quantity: parseInt(quantity),
        price: parseFloat(price),
        timeInForce: 'GTC'
      };

      // Mock API call - in production, call actual API
      console.log('Placing options order:', orderData);
      
      // Reset form
      setQuantity('');
      
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

  const formatGreek = (value: number, decimals: number = 4) => {
    return value.toFixed(decimals);
  };

  const getDaysToExpiry = (expiryDate: string) => {
    const expiry = new Date(expiryDate);
    const now = new Date();
    const diffTime = expiry.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Options Trading</h1>
          <p className="text-gray-600">Trade cryptocurrency options with advanced Greeks analysis</p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Underlying</label>
                <Select value={underlyingFilter} onValueChange={setUnderlyingFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BTC">BTC</SelectItem>
                    <SelectItem value="ETH">ETH</SelectItem>
                    <SelectItem value="BNB">BNB</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <Select value={optionTypeFilter} onValueChange={(value) => setOptionTypeFilter(value as any)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All</SelectItem>
                    <SelectItem value="CALL">Calls</SelectItem>
                    <SelectItem value="PUT">Puts</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Options Chain */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Options Chain
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Strike</TableHead>
                    <TableHead>Expiry</TableHead>
                    <TableHead>Last Price</TableHead>
                    <TableHead>Bid/Ask</TableHead>
                    <TableHead>Volume</TableHead>
                    <TableHead>IV</TableHead>
                    <TableHead>Delta</TableHead>
                    <TableHead>Theta</TableHead>
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
                        <div className="text-sm">{contract.symbol}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={contract.optionType === 'CALL' ? 'default' : 'destructive'}>
                          {contract.optionType}
                        </Badge>
                      </TableCell>
                      <TableCell>${formatNumber(contract.strikePrice, 0)}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {new Date(contract.expiryDate).toLocaleDateString()}
                          <div className="text-xs text-gray-500">
                            {getDaysToExpiry(contract.expiryDate)}d
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>${formatNumber(contract.lastPrice, 2)}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          ${formatNumber(contract.bid, 2)} / ${formatNumber(contract.ask, 2)}
                        </div>
                      </TableCell>
                      <TableCell>{contract.volume}</TableCell>
                      <TableCell>{(contract.impliedVolatility * 100).toFixed(1)}%</TableCell>
                      <TableCell>
                        <span className={contract.delta >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatGreek(contract.delta)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-red-600">{formatGreek(contract.theta)}</span>
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
                  <div className="font-semibold text-sm">{selectedContract.symbol}</div>
                  <div className="text-xs text-gray-600">
                    {selectedContract.underlying} ${selectedContract.strikePrice} {selectedContract.optionType}
                  </div>
                  <div className="text-xs text-gray-500">
                    Expires: {new Date(selectedContract.expiryDate).toLocaleDateString()}
                  </div>
                </div>
              )}

              <Tabs value={orderSide} onValueChange={(value) => setOrderSide(value as 'BUY' | 'SELL')}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="BUY" className="text-green-600">Buy</TabsTrigger>
                  <TabsTrigger value="SELL" className="text-red-600">Sell</TabsTrigger>
                </TabsList>
              </Tabs>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Quantity (Contracts)</label>
                <Input
                  type="number"
                  placeholder="1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  min="1"
                  step="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Price per Contract</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  step="0.01"
                />
                {selectedContract && (
                  <div className="text-xs text-gray-500 mt-1">
                    Mid: ${formatNumber((selectedContract.bid + selectedContract.ask) / 2, 2)}
                  </div>
                )}
              </div>

              {selectedContract && quantity && price && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span>Total Cost:</span>
                    <span className="font-semibold">
                      ${formatNumber(parseInt(quantity) * parseFloat(price), 2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Max Loss:</span>
                    <span>
                      {orderSide === 'BUY' ? 'Premium Paid' : 'Unlimited'}
                    </span>
                  </div>
                </div>
              )}

              <Button
                className={`w-full ${orderSide === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                onClick={placeOrder}
                disabled={placingOrder || !selectedContract || !quantity || !price}
              >
                {placingOrder ? 'Placing Order...' : `${orderSide} ${quantity || '0'} Contract${parseInt(quantity) !== 1 ? 's' : ''}`}
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
                        <div className="font-semibold text-sm">{position.symbol}</div>
                        <div className="text-xs text-gray-500">
                          {position.quantity} contracts • {position.side}
                        </div>
                      </div>
                      <Badge variant={position.optionType === 'CALL' ? 'default' : 'destructive'}>
                        {position.optionType}
                      </Badge>
                    </div>
                    
                    <div className="text-xs space-y-1">
                      <div className="flex justify-between">
                        <span>Entry:</span>
                        <span>${formatNumber(position.entryPrice, 2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Current:</span>
                        <span>${formatNumber(position.currentPrice, 2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>P&L:</span>
                        <span className={position.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${formatNumber(position.unrealizedPnl, 2)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Expires: {new Date(position.expiryDate).toLocaleDateString()}
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-2 text-xs text-red-600"
                    >
                      Close Position
                    </Button>
                  </div>
                ))}

                {positions.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">No open positions</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Options Calculator */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Options Calculator
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Spot Price</label>
                <Input
                  type="number"
                  placeholder="43250"
                  className="text-sm"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Strike Price</label>
                <Input
                  type="number"
                  placeholder="45000"
                  className="text-sm"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Volatility (%)</label>
                <Input
                  type="number"
                  placeholder="65"
                  className="text-sm"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Days to Expiry</label>
                <Input
                  type="number"
                  placeholder="30"
                  className="text-sm"
                />
              </div>

              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs font-medium text-gray-700 mb-2">Theoretical Prices:</div>
                <div className="flex justify-between text-xs">
                  <span>Call:</span>
                  <span className="font-semibold">$1,250.00</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Put:</span>
                  <span className="font-semibold">$875.00</span>
                </div>
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
                <h3 className="font-semibold text-yellow-800 mb-1">Options Trading Risk Warning</h3>
                <p className="text-sm text-yellow-700">
                  Options trading involves substantial risk and may result in the loss of your entire investment. 
                  Options may expire worthless. Please ensure you understand the risks and Greeks before trading.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default OptionsTradingPage;
