import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Plus, Edit, Trash2, Settings, TrendingUp, AlertCircle } from 'lucide-react';

interface TradingPair {
  id: number;
  symbol: string;
  base_asset: string;
  quote_asset: string;
  trading_type: string;
  status: string;
  min_order_size: number;
  max_order_size?: number;
  min_price: number;
  max_price?: number;
  price_precision: number;
  quantity_precision: number;
  maker_fee: number;
  taker_fee: number;
  created_at: string;
  updated_at: string;
  additional_params?: any;
}

interface CreatePairForm {
  trading_type: string;
  symbol: string;
  base_asset: string;
  quote_asset: string;
  min_order_size: string;
  max_order_size: string;
  min_price: string;
  max_price: string;
  price_precision: string;
  quantity_precision: string;
  maker_fee: string;
  taker_fee: string;
  // Type-specific fields
  is_spot_enabled?: boolean;
  is_margin_enabled?: boolean;
  margin_leverage_max?: string;
  contract_type?: string;
  settlement_asset?: string;
  leverage_max?: string;
  underlying_asset?: string;
  option_type?: string;
  strike_price?: string;
  expiry_date?: string;
  exercise_style?: string;
  etf_type?: string;
  expense_ratio?: string;
  alpha_strategy_type?: string;
  min_alpha_score?: string;
}

const TradingPairsAdminPage: React.FC = () => {
  const [tradingPairs, setTradingPairs] = useState<TradingPair[]>([]);
  const [filteredPairs, setFilteredPairs] = useState<TradingPair[]>([]);
  const [supportedAssets, setSupportedAssets] = useState<{[key: string]: string[]}>({});
  
  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Form states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedPair, setSelectedPair] = useState<TradingPair | null>(null);
  const [createForm, setCreateForm] = useState<CreatePairForm>({
    trading_type: 'SPOT',
    symbol: '',
    base_asset: '',
    quote_asset: '',
    min_order_size: '',
    max_order_size: '',
    min_price: '',
    max_price: '',
    price_precision: '4',
    quantity_precision: '4',
    maker_fee: '0.001',
    taker_fee: '0.001',
  });
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadTradingPairs();
    loadSupportedAssets();
  }, []);

  useEffect(() => {
    filterPairs();
  }, [tradingPairs, typeFilter, statusFilter, searchQuery]);

  const loadTradingPairs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/trading-pairs');
      if (response.ok) {
        const pairs = await response.json();
        setTradingPairs(pairs);
      }
    } catch (error) {
      console.error('Failed to load trading pairs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSupportedAssets = async () => {
    try {
      const response = await fetch('/api/v1/supported-assets');
      if (response.ok) {
        const assets = await response.json();
        setSupportedAssets(assets);
      }
    } catch (error) {
      console.error('Failed to load supported assets:', error);
    }
  };

  const filterPairs = () => {
    let filtered = tradingPairs;
    
    if (typeFilter !== 'all') {
      filtered = filtered.filter(pair => pair.trading_type === typeFilter);
    }
    
    if (statusFilter !== 'all') {
      filtered = filtered.filter(pair => pair.status === statusFilter);
    }
    
    if (searchQuery) {
      filtered = filtered.filter(pair => 
        pair.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pair.base_asset.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pair.quote_asset.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    setFilteredPairs(filtered);
  };

  const createTradingPair = async () => {
    try {
      setCreating(true);
      
      // Build pair data based on trading type
      const pairData: any = {
        symbol: createForm.symbol,
        base_asset: createForm.base_asset,
        quote_asset: createForm.quote_asset,
        min_order_size: parseFloat(createForm.min_order_size),
        max_order_size: createForm.max_order_size ? parseFloat(createForm.max_order_size) : null,
        min_price: parseFloat(createForm.min_price),
        max_price: createForm.max_price ? parseFloat(createForm.max_price) : null,
        price_precision: parseInt(createForm.price_precision),
        quantity_precision: parseInt(createForm.quantity_precision),
        maker_fee: parseFloat(createForm.maker_fee),
        taker_fee: parseFloat(createForm.taker_fee),
      };

      // Add type-specific fields
      switch (createForm.trading_type) {
        case 'SPOT':
          pairData.is_spot_enabled = createForm.is_spot_enabled ?? true;
          pairData.is_margin_enabled = createForm.is_margin_enabled ?? false;
          if (createForm.margin_leverage_max) {
            pairData.margin_leverage_max = parseFloat(createForm.margin_leverage_max);
          }
          break;
        case 'FUTURES':
          pairData.is_futures_enabled = true;
          pairData.contract_type = createForm.contract_type;
          pairData.settlement_asset = createForm.settlement_asset;
          pairData.leverage_max = parseFloat(createForm.leverage_max || '100');
          pairData.funding_interval = 8;
          pairData.maintenance_margin_rate = 0.05;
          pairData.initial_margin_rate = 0.1;
          break;
        case 'OPTIONS':
          pairData.is_options_enabled = true;
          pairData.underlying_asset = createForm.underlying_asset;
          pairData.option_type = createForm.option_type;
          pairData.strike_price = parseFloat(createForm.strike_price || '0');
          pairData.expiry_date = createForm.expiry_date;
          pairData.exercise_style = createForm.exercise_style;
          pairData.contract_size = 1;
          break;
        case 'ETF':
          pairData.is_etf_enabled = true;
          pairData.etf_type = createForm.etf_type;
          pairData.expense_ratio = parseFloat(createForm.expense_ratio || '0.001');
          pairData.nav_calculation_frequency = 'DAILY';
          pairData.creation_unit_size = 50000;
          break;
        case 'MARGIN':
          pairData.is_margin_enabled = true;
          pairData.max_leverage = parseFloat(createForm.leverage_max || '10');
          pairData.maintenance_margin_rate = 0.05;
          pairData.initial_margin_rate = 0.1;
          pairData.liquidation_fee = 0.01;
          break;
        case 'ALPHA':
          pairData.is_alpha_enabled = true;
          pairData.alpha_strategy_type = createForm.alpha_strategy_type;
          pairData.min_alpha_score = parseFloat(createForm.min_alpha_score || '0.1');
          pairData.max_position_size = parseFloat(createForm.max_order_size || '1000000');
          pairData.rebalance_frequency = 'DAILY';
          break;
      }

      const response = await fetch('/api/v1/trading-pairs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trading_type: createForm.trading_type,
          pair_data: pairData,
        }),
      });

      if (response.ok) {
        const newPair = await response.json();
        setTradingPairs(prev => [newPair, ...prev]);
        setIsCreateDialogOpen(false);
        resetCreateForm();
      } else {
        const error = await response.json();
        alert(`Failed to create trading pair: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to create trading pair:', error);
      alert('Failed to create trading pair');
    } finally {
      setCreating(false);
    }
  };

  const updateTradingPair = async () => {
    if (!selectedPair) return;
    
    try {
      setUpdating(true);
      
      const updateData = {
        status: selectedPair.status,
        min_order_size: selectedPair.min_order_size,
        max_order_size: selectedPair.max_order_size,
        min_price: selectedPair.min_price,
        max_price: selectedPair.max_price,
        maker_fee: selectedPair.maker_fee,
        taker_fee: selectedPair.taker_fee,
      };

      const response = await fetch(`/api/v1/trading-pairs/${selectedPair.symbol}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        const updatedPair = await response.json();
        setTradingPairs(prev => prev.map(pair => 
          pair.id === selectedPair.id ? updatedPair : pair
        ));
        setIsEditDialogOpen(false);
        setSelectedPair(null);
      } else {
        const error = await response.json();
        alert(`Failed to update trading pair: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to update trading pair:', error);
      alert('Failed to update trading pair');
    } finally {
      setUpdating(false);
    }
  };

  const deleteTradingPair = async (symbol: string) => {
    if (!confirm(`Are you sure you want to delist ${symbol}?`)) return;
    
    try {
      const response = await fetch(`/api/v1/trading-pairs/${symbol}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setTradingPairs(prev => prev.filter(pair => pair.symbol !== symbol));
      } else {
        const error = await response.json();
        alert(`Failed to delete trading pair: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to delete trading pair:', error);
      alert('Failed to delete trading pair');
    }
  };

  const resetCreateForm = () => {
    setCreateForm({
      trading_type: 'SPOT',
      symbol: '',
      base_asset: '',
      quote_asset: '',
      min_order_size: '',
      max_order_size: '',
      min_price: '',
      max_price: '',
      price_precision: '4',
      quantity_precision: '4',
      maker_fee: '0.001',
      taker_fee: '0.001',
    });
  };

  const renderTypeSpecificFields = () => {
    switch (createForm.trading_type) {
      case 'SPOT':
        return (
          <>
            <div className="flex items-center space-x-2">
              <Switch
                id="is_spot_enabled"
                checked={createForm.is_spot_enabled ?? true}
                onCheckedChange={(checked) => setCreateForm(prev => ({ ...prev, is_spot_enabled: checked }))}
              />
              <Label htmlFor="is_spot_enabled">Enable Spot Trading</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="is_margin_enabled"
                checked={createForm.is_margin_enabled ?? false}
                onCheckedChange={(checked) => setCreateForm(prev => ({ ...prev, is_margin_enabled: checked }))}
              />
              <Label htmlFor="is_margin_enabled">Enable Margin Trading</Label>
            </div>
            {createForm.is_margin_enabled && (
              <div>
                <Label htmlFor="margin_leverage_max">Max Margin Leverage</Label>
                <Input
                  id="margin_leverage_max"
                  type="number"
                  value={createForm.margin_leverage_max || ''}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, margin_leverage_max: e.target.value }))}
                  placeholder="10"
                />
              </div>
            )}
          </>
        );
      case 'FUTURES':
        return (
          <>
            <div>
              <Label htmlFor="contract_type">Contract Type</Label>
              <Select value={createForm.contract_type || ''} onValueChange={(value) => setCreateForm(prev => ({ ...prev, contract_type: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select contract type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PERPETUAL">Perpetual</SelectItem>
                  <SelectItem value="QUARTERLY">Quarterly</SelectItem>
                  <SelectItem value="MONTHLY">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="settlement_asset">Settlement Asset</Label>
              <Input
                id="settlement_asset"
                value={createForm.settlement_asset || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, settlement_asset: e.target.value }))}
                placeholder="USDT"
              />
            </div>
            <div>
              <Label htmlFor="leverage_max">Max Leverage</Label>
              <Input
                id="leverage_max"
                type="number"
                value={createForm.leverage_max || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, leverage_max: e.target.value }))}
                placeholder="100"
              />
            </div>
          </>
        );
      case 'OPTIONS':
        return (
          <>
            <div>
              <Label htmlFor="underlying_asset">Underlying Asset</Label>
              <Input
                id="underlying_asset"
                value={createForm.underlying_asset || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, underlying_asset: e.target.value }))}
                placeholder="BTC"
              />
            </div>
            <div>
              <Label htmlFor="option_type">Option Type</Label>
              <Select value={createForm.option_type || ''} onValueChange={(value) => setCreateForm(prev => ({ ...prev, option_type: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select option type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CALL">Call</SelectItem>
                  <SelectItem value="PUT">Put</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="strike_price">Strike Price</Label>
              <Input
                id="strike_price"
                type="number"
                value={createForm.strike_price || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, strike_price: e.target.value }))}
                placeholder="50000"
              />
            </div>
            <div>
              <Label htmlFor="expiry_date">Expiry Date</Label>
              <Input
                id="expiry_date"
                type="datetime-local"
                value={createForm.expiry_date || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, expiry_date: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="exercise_style">Exercise Style</Label>
              <Select value={createForm.exercise_style || ''} onValueChange={(value) => setCreateForm(prev => ({ ...prev, exercise_style: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select exercise style" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EUROPEAN">European</SelectItem>
                  <SelectItem value="AMERICAN">American</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        );
      case 'ETF':
        return (
          <>
            <div>
              <Label htmlFor="etf_type">ETF Type</Label>
              <Select value={createForm.etf_type || ''} onValueChange={(value) => setCreateForm(prev => ({ ...prev, etf_type: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select ETF type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EQUITY">Equity</SelectItem>
                  <SelectItem value="BOND">Bond</SelectItem>
                  <SelectItem value="COMMODITY">Commodity</SelectItem>
                  <SelectItem value="SECTOR">Sector</SelectItem>
                  <SelectItem value="MIXED">Mixed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="expense_ratio">Expense Ratio (%)</Label>
              <Input
                id="expense_ratio"
                type="number"
                step="0.001"
                value={createForm.expense_ratio || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, expense_ratio: e.target.value }))}
                placeholder="0.1"
              />
            </div>
          </>
        );
      case 'ALPHA':
        return (
          <>
            <div>
              <Label htmlFor="alpha_strategy_type">Alpha Strategy Type</Label>
              <Select value={createForm.alpha_strategy_type || ''} onValueChange={(value) => setCreateForm(prev => ({ ...prev, alpha_strategy_type: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select strategy type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MOMENTUM">Momentum</SelectItem>
                  <SelectItem value="MEAN_REVERSION">Mean Reversion</SelectItem>
                  <SelectItem value="ARBITRAGE">Arbitrage</SelectItem>
                  <SelectItem value="MARKET_MAKING">Market Making</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="min_alpha_score">Min Alpha Score</Label>
              <Input
                id="min_alpha_score"
                type="number"
                step="0.01"
                value={createForm.min_alpha_score || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, min_alpha_score: e.target.value }))}
                placeholder="0.1"
              />
            </div>
          </>
        );
      default:
        return null;
    }
  };

  const formatNumber = (num: number, decimals: number = 4) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Pairs Management</h1>
          <p className="text-gray-600">Manage trading pairs across all trading types</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Pairs</p>
                  <p className="text-2xl font-bold text-gray-900">{tradingPairs.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Settings className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Pairs</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tradingPairs.filter(p => p.status === 'ACTIVE').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <AlertCircle className="h-8 w-8 text-yellow-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Inactive Pairs</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tradingPairs.filter(p => p.status === 'INACTIVE').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Trash2 className="h-8 w-8 text-red-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Delisted Pairs</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tradingPairs.filter(p => p.status === 'DELISTED').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Actions */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
              <div className="flex flex-col md:flex-row gap-4 flex-1">
                <Input
                  placeholder="Search pairs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="max-w-sm"
                />
                
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="SPOT">Spot</SelectItem>
                    <SelectItem value="FUTURES">Futures</SelectItem>
                    <SelectItem value="OPTIONS">Options</SelectItem>
                    <SelectItem value="ETF">ETF</SelectItem>
                    <SelectItem value="MARGIN">Margin</SelectItem>
                    <SelectItem value="ALPHA">Alpha</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="ACTIVE">Active</SelectItem>
                    <SelectItem value="INACTIVE">Inactive</SelectItem>
                    <SelectItem value="DELISTED">Delisted</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Create Trading Pair
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Create New Trading Pair</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="trading_type">Trading Type</Label>
                      <Select value={createForm.trading_type} onValueChange={(value) => setCreateForm(prev => ({ ...prev, trading_type: value }))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="SPOT">Spot</SelectItem>
                          <SelectItem value="FUTURES">Futures</SelectItem>
                          <SelectItem value="OPTIONS">Options</SelectItem>
                          <SelectItem value="ETF">ETF</SelectItem>
                          <SelectItem value="MARGIN">Margin</SelectItem>
                          <SelectItem value="ALPHA">Alpha</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="symbol">Symbol</Label>
                        <Input
                          id="symbol"
                          value={createForm.symbol}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                          placeholder="BTCUSDT"
                        />
                      </div>
                      <div>
                        <Label htmlFor="base_asset">Base Asset</Label>
                        <Input
                          id="base_asset"
                          value={createForm.base_asset}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, base_asset: e.target.value.toUpperCase() }))}
                          placeholder="BTC"
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="quote_asset">Quote Asset</Label>
                      <Input
                        id="quote_asset"
                        value={createForm.quote_asset}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, quote_asset: e.target.value.toUpperCase() }))}
                        placeholder="USDT"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="min_order_size">Min Order Size</Label>
                        <Input
                          id="min_order_size"
                          type="number"
                          step="0.0001"
                          value={createForm.min_order_size}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, min_order_size: e.target.value }))}
                          placeholder="0.001"
                        />
                      </div>
                      <div>
                        <Label htmlFor="max_order_size">Max Order Size (Optional)</Label>
                        <Input
                          id="max_order_size"
                          type="number"
                          step="0.0001"
                          value={createForm.max_order_size}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, max_order_size: e.target.value }))}
                          placeholder="1000"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="min_price">Min Price</Label>
                        <Input
                          id="min_price"
                          type="number"
                          step="0.0001"
                          value={createForm.min_price}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, min_price: e.target.value }))}
                          placeholder="0.0001"
                        />
                      </div>
                      <div>
                        <Label htmlFor="max_price">Max Price (Optional)</Label>
                        <Input
                          id="max_price"
                          type="number"
                          step="0.0001"
                          value={createForm.max_price}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, max_price: e.target.value }))}
                          placeholder="1000000"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="price_precision">Price Precision</Label>
                        <Input
                          id="price_precision"
                          type="number"
                          min="0"
                          max="8"
                          value={createForm.price_precision}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, price_precision: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label htmlFor="quantity_precision">Quantity Precision</Label>
                        <Input
                          id="quantity_precision"
                          type="number"
                          min="0"
                          max="8"
                          value={createForm.quantity_precision}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, quantity_precision: e.target.value }))}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="maker_fee">Maker Fee (%)</Label>
                        <Input
                          id="maker_fee"
                          type="number"
                          step="0.0001"
                          value={createForm.maker_fee}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, maker_fee: e.target.value }))}
                          placeholder="0.1"
                        />
                      </div>
                      <div>
                        <Label htmlFor="taker_fee">Taker Fee (%)</Label>
                        <Input
                          id="taker_fee"
                          type="number"
                          step="0.0001"
                          value={createForm.taker_fee}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, taker_fee: e.target.value }))}
                          placeholder="0.1"
                        />
                      </div>
                    </div>

                    {/* Type-specific fields */}
                    {renderTypeSpecificFields()}

                    <div className="flex justify-end gap-2 pt-4">
                      <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button onClick={createTradingPair} disabled={creating}>
                        {creating ? 'Creating...' : 'Create Pair'}
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>

        {/* Trading Pairs Table */}
        <Card>
          <CardHeader>
            <CardTitle>Trading Pairs ({filteredPairs.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Base/Quote</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Min Order Size</TableHead>
                    <TableHead>Price Range</TableHead>
                    <TableHead>Fees (M/T)</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPairs.map((pair) => (
                    <TableRow key={pair.id}>
                      <TableCell className="font-medium">{pair.symbol}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{pair.trading_type}</Badge>
                      </TableCell>
                      <TableCell>{pair.base_asset}/{pair.quote_asset}</TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            pair.status === 'ACTIVE' ? 'default' :
                            pair.status === 'INACTIVE' ? 'secondary' :
                            'destructive'
                          }
                        >
                          {pair.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatNumber(pair.min_order_size)}</TableCell>
                      <TableCell>
                        ${formatNumber(pair.min_price)} - {pair.max_price ? `$${formatNumber(pair.max_price)}` : '∞'}
                      </TableCell>
                      <TableCell>
                        {(pair.maker_fee * 100).toFixed(3)}% / {(pair.taker_fee * 100).toFixed(3)}%
                      </TableCell>
                      <TableCell>
                        {new Date(pair.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedPair(pair);
                              setIsEditDialogOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => deleteTradingPair(pair.symbol)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Edit Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Edit Trading Pair: {selectedPair?.symbol}</DialogTitle>
            </DialogHeader>
            {selectedPair && (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="edit_status">Status</Label>
                  <Select 
                    value={selectedPair.status} 
                    onValueChange={(value) => setSelectedPair(prev => prev ? { ...prev, status: value } : null)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ACTIVE">Active</SelectItem>
                      <SelectItem value="INACTIVE">Inactive</SelectItem>
                      <SelectItem value="DELISTED">Delisted</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="edit_maker_fee">Maker Fee (%)</Label>
                    <Input
                      id="edit_maker_fee"
                      type="number"
                      step="0.0001"
                      value={selectedPair.maker_fee}
                      onChange={(e) => setSelectedPair(prev => prev ? { ...prev, maker_fee: parseFloat(e.target.value) } : null)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit_taker_fee">Taker Fee (%)</Label>
                    <Input
                      id="edit_taker_fee"
                      type="number"
                      step="0.0001"
                      value={selectedPair.taker_fee}
                      onChange={(e) => setSelectedPair(prev => prev ? { ...prev, taker_fee: parseFloat(e.target.value) } : null)}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={updateTradingPair} disabled={updating}>
                    {updating ? 'Updating...' : 'Update Pair'}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default TradingPairsAdminPage;
