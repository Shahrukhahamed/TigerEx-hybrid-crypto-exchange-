import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Tabs, 
  Tab, 
  Card, 
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  AccountBalance,
  Settings,
  Notifications,
  Security,
  Help,
  Refresh,
  FullscreenExit,
  Fullscreen,
  Star,
  StarBorder
} from '@mui/icons-material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  CandlestickChart,
  AreaChart,
  Area
} from 'recharts';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuth } from '../../hooks/useAuth';
import { OrderBook } from './components/OrderBook';
import { TradeHistory } from './components/TradeHistory';
import { MarketData } from './components/MarketData';

interface TradingPair {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'STOP_LIMIT' | 'TAKE_PROFIT';
  quantity: number;
  price?: number;
  stopPrice?: number;
  status: 'NEW' | 'PARTIALLY_FILLED' | 'FILLED' | 'CANCELED';
  createdAt: string;
}

interface Balance {
  asset: string;
  available: number;
  locked: number;
  total: number;
}

interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  markPrice: number;
  unrealizedPnl: number;
  leverage: number;
}

const TradingPlatform: React.FC = () => {
  const { user } = useAuth();
  const [selectedPair, setSelectedPair] = useState<string>('BTCUSDT');
  const [tradingPairs, setTradingPairs] = useState<TradingPair[]>([]);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'STOP_LOSS'>('LIMIT');
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderQuantity, setOrderQuantity] = useState<string>('');
  const [orderPrice, setOrderPrice] = useState<string>('');
  const [stopPrice, setStopPrice] = useState<string>('');
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  const [showOrderConfirm, setShowOrderConfirm] = useState(false);
  const [notification, setNotification] = useState<{ message: string; severity: 'success' | 'error' | 'warning' | 'info' } | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [favoriteSymbols, setFavoriteSymbols] = useState<Set<string>>(new Set());

  // WebSocket connection for real-time data
  const { 
    isConnected, 
    subscribe, 
    unsubscribe, 
    sendMessage 
  } = useWebSocket('ws://localhost:8080/ws');

  // Subscribe to market data
  useEffect(() => {
    if (isConnected) {
      subscribe(`ticker@${selectedPair.toLowerCase()}`);
      subscribe(`depth@${selectedPair.toLowerCase()}`);
      subscribe(`trade@${selectedPair.toLowerCase()}`);
      subscribe(`kline@${selectedPair.toLowerCase()}_1m`);
      
      if (user) {
        subscribe(`user@${user.id}`);
      }
    }
    
    return () => {
      unsubscribe(`ticker@${selectedPair.toLowerCase()}`);
      unsubscribe(`depth@${selectedPair.toLowerCase()}`);
      unsubscribe(`trade@${selectedPair.toLowerCase()}`);
      unsubscribe(`kline@${selectedPair.toLowerCase()}_1m`);
      
      if (user) {
        unsubscribe(`user@${user.id}`);
      }
    };
  }, [isConnected, selectedPair, user, subscribe, unsubscribe]);

  // Load initial data
  useEffect(() => {
    loadTradingPairs();
    loadBalances();
    loadOrders();
    loadPositions();
  }, []);

  const loadTradingPairs = async () => {
    try {
      const response = await fetch('/api/v1/exchange/info');
      const data = await response.json();
      setTradingPairs(data.symbols || []);
    } catch (error) {
      console.error('Failed to load trading pairs:', error);
    }
  };

  const loadBalances = async () => {
    try {
      const response = await fetch('/api/v1/account/balance', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setBalances(data.balances || []);
    } catch (error) {
      console.error('Failed to load balances:', error);
    }
  };

  const loadOrders = async () => {
    try {
      const response = await fetch('/api/v1/orders/open', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setOrders(data.orders || []);
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await fetch('/api/v1/futures/account', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setPositions(data.positions || []);
    } catch (error) {
      console.error('Failed to load positions:', error);
    }
  };

  const handlePlaceOrder = async () => {
    try {
      const orderData = {
        symbol: selectedPair,
        side: orderSide,
        type: orderType,
        quantity: parseFloat(orderQuantity),
        ...(orderType !== 'MARKET' && { price: parseFloat(orderPrice) }),
        ...(orderType === 'STOP_LOSS' && { stopPrice: parseFloat(stopPrice) })
      };

      const response = await fetch('/api/v1/order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(orderData)
      });

      if (response.ok) {
        setNotification({ message: 'Order placed successfully', severity: 'success' });
        setOrderQuantity('');
        setOrderPrice('');
        setStopPrice('');
        setShowOrderConfirm(false);
        loadOrders();
        loadBalances();
      } else {
        const error = await response.json();
        setNotification({ message: error.message || 'Failed to place order', severity: 'error' });
      }
    } catch (error) {
      setNotification({ message: 'Failed to place order', severity: 'error' });
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const response = await fetch('/api/v1/order', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ orderId })
      });

      if (response.ok) {
        setNotification({ message: 'Order canceled successfully', severity: 'success' });
        loadOrders();
      } else {
        setNotification({ message: 'Failed to cancel order', severity: 'error' });
      }
    } catch (error) {
      setNotification({ message: 'Failed to cancel order', severity: 'error' });
    }
  };

  const toggleFavorite = (symbol: string) => {
    const newFavorites = new Set(favoriteSymbols);
    if (newFavorites.has(symbol)) {
      newFavorites.delete(symbol);
    } else {
      newFavorites.add(symbol);
    }
    setFavoriteSymbols(newFavorites);
    localStorage.setItem('favoriteSymbols', JSON.stringify(Array.from(newFavorites)));
  };

  const selectedPairData = useMemo(() => {
    return tradingPairs.find(pair => pair.symbol === selectedPair);
  }, [tradingPairs, selectedPair]);

  const currentBalance = useMemo(() => {
    if (!selectedPairData) return null;
    const baseBalance = balances.find(b => b.asset === selectedPairData.baseAsset);
    const quoteBalance = balances.find(b => b.asset === selectedPairData.quoteAsset);
    return { base: baseBalance, quote: quoteBalance };
  }, [balances, selectedPairData]);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 1 }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Trading Pair</InputLabel>
              <Select
                value={selectedPair}
                onChange={(e) => setSelectedPair(e.target.value)}
                label="Trading Pair"
              >
                {tradingPairs.map((pair) => (
                  <MenuItem key={pair.symbol} value={pair.symbol}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(pair.symbol);
                        }}
                      >
                        {favoriteSymbols.has(pair.symbol) ? <Star color="primary" /> : <StarBorder />}
                      </IconButton>
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {pair.symbol}
                      </Typography>
                      <Box sx={{ ml: 'auto', textAlign: 'right' }}>
                        <Typography variant="body2" fontWeight="bold">
                          ${pair.price.toFixed(2)}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          color={pair.change24h >= 0 ? 'success.main' : 'error.main'}
                        >
                          {pair.change24h >= 0 ? '+' : ''}{pair.change24h.toFixed(2)}%
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            {selectedPairData && (
              <Grid container spacing={2}>
                <Grid item>
                  <Typography variant="h6" fontWeight="bold">
                    ${selectedPairData.price.toFixed(2)}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    color={selectedPairData.change24h >= 0 ? 'success.main' : 'error.main'}
                  >
                    {selectedPairData.change24h >= 0 ? <TrendingUp /> : <TrendingDown />}
                    {selectedPairData.change24h >= 0 ? '+' : ''}{selectedPairData.change24h.toFixed(2)}%
                  </Typography>
                </Grid>
                <Grid item>
                  <Typography variant="body2" color="text.secondary">
                    24h High
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    ${selectedPairData.high24h.toFixed(2)}
                  </Typography>
                </Grid>
                <Grid item>
                  <Typography variant="body2" color="text.secondary">
                    24h Low
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    ${selectedPairData.low24h.toFixed(2)}
                  </Typography>
                </Grid>
                <Grid item>
                  <Typography variant="body2" color="text.secondary">
                    24h Volume
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {selectedPairData.volume24h.toLocaleString()}
                  </Typography>
                </Grid>
              </Grid>
            )}
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={isAdvancedMode}
                    onChange={(e) => setIsAdvancedMode(e.target.checked)}
                  />
                }
                label="Advanced"
              />
              <IconButton onClick={() => setIsFullscreen(!isFullscreen)}>
                {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
              </IconButton>
              <IconButton>
                <Settings />
              </IconButton>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Main Trading Interface */}
      <Grid container spacing={1} sx={{ flex: 1, overflow: 'hidden' }}>
        {/* Left Panel - Order Book & Recent Trades */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
              <Tab label="Order Book" />
              <Tab label="Recent Trades" />
            </Tabs>
            <Box sx={{ flex: 1, overflow: 'hidden' }}>
              {activeTab === 0 && <OrderBook symbol={selectedPair} />}
              {activeTab === 1 && <TradeHistory symbol={selectedPair} />}
            </Box>
          </Paper>
        </Grid>

        {/* Center Panel - Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ height: '100%', p: 1 }}>
            <MarketData symbol={selectedPair} />
          </Paper>
        </Grid>

        {/* Right Panel - Trading Form */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ height: '100%', p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Place Order
            </Typography>
            
            {/* Order Type Tabs */}
            <Tabs 
              value={orderType} 
              onChange={(e, v) => setOrderType(v)}
              variant="fullWidth"
              sx={{ mb: 2 }}
            >
              <Tab label="Limit" value="LIMIT" />
              <Tab label="Market" value="MARKET" />
              <Tab label="Stop" value="STOP_LOSS" />
            </Tabs>

            {/* Buy/Sell Toggle */}
            <Grid container spacing={1} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <Button
                  fullWidth
                  variant={orderSide === 'BUY' ? 'contained' : 'outlined'}
                  color="success"
                  onClick={() => setOrderSide('BUY')}
                >
                  Buy
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  fullWidth
                  variant={orderSide === 'SELL' ? 'contained' : 'outlined'}
                  color="error"
                  onClick={() => setOrderSide('SELL')}
                >
                  Sell
                </Button>
              </Grid>
            </Grid>

            {/* Order Form */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {orderType !== 'MARKET' && (
                <TextField
                  label="Price"
                  type="number"
                  value={orderPrice}
                  onChange={(e) => setOrderPrice(e.target.value)}
                  fullWidth
                  size="small"
                  InputProps={{
                    endAdornment: selectedPairData?.quoteAsset
                  }}
                />
              )}

              {orderType === 'STOP_LOSS' && (
                <TextField
                  label="Stop Price"
                  type="number"
                  value={stopPrice}
                  onChange={(e) => setStopPrice(e.target.value)}
                  fullWidth
                  size="small"
                  InputProps={{
                    endAdornment: selectedPairData?.quoteAsset
                  }}
                />
              )}

              <TextField
                label="Quantity"
                type="number"
                value={orderQuantity}
                onChange={(e) => setOrderQuantity(e.target.value)}
                fullWidth
                size="small"
                InputProps={{
                  endAdornment: selectedPairData?.baseAsset
                }}
              />

              {/* Balance Display */}
              {currentBalance && (
                <Box sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Available Balance:
                  </Typography>
                  <Typography variant="body2">
                    {orderSide === 'BUY' 
                      ? `${currentBalance.quote?.available.toFixed(4) || '0'} ${selectedPairData?.quoteAsset}`
                      : `${currentBalance.base?.available.toFixed(4) || '0'} ${selectedPairData?.baseAsset}`
                    }
                  </Typography>
                </Box>
              )}

              {/* Quick Amount Buttons */}
              <Grid container spacing={1}>
                {['25%', '50%', '75%', '100%'].map((percentage) => (
                  <Grid item xs={3} key={percentage}>
                    <Button
                      size="small"
                      variant="outlined"
                      fullWidth
                      onClick={() => {
                        // Calculate quantity based on percentage
                        if (currentBalance) {
                          const balance = orderSide === 'BUY' 
                            ? currentBalance.quote?.available || 0
                            : currentBalance.base?.available || 0;
                          
                          const percent = parseInt(percentage) / 100;
                          let quantity: number;
                          
                          if (orderSide === 'BUY' && orderType !== 'MARKET') {
                            quantity = (balance * percent) / parseFloat(orderPrice || '1');
                          } else {
                            quantity = balance * percent;
                          }
                          
                          setOrderQuantity(quantity.toFixed(6));
                        }
                      }}
                    >
                      {percentage}
                    </Button>
                  </Grid>
                ))}
              </Grid>

              <Button
                variant="contained"
                color={orderSide === 'BUY' ? 'success' : 'error'}
                fullWidth
                size="large"
                onClick={() => setShowOrderConfirm(true)}
                disabled={!orderQuantity || (orderType !== 'MARKET' && !orderPrice)}
              >
                {orderSide === 'BUY' ? 'Buy' : 'Sell'} {selectedPairData?.baseAsset}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Bottom Panel - Orders, Positions, History */}
      <Paper sx={{ mt: 1, height: '300px' }}>
        <Tabs value={0}>
          <Tab label="Open Orders" />
          <Tab label="Order History" />
          <Tab label="Trade History" />
          <Tab label="Positions" />
        </Tabs>
        
        <TableContainer sx={{ height: '250px' }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Side</TableCell>
                <TableCell>Quantity</TableCell>
                <TableCell>Price</TableCell>
                <TableCell>Filled</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell>{order.symbol}</TableCell>
                  <TableCell>{order.type}</TableCell>
                  <TableCell>
                    <Chip 
                      label={order.side} 
                      color={order.side === 'BUY' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{order.quantity}</TableCell>
                  <TableCell>{order.price || 'Market'}</TableCell>
                  <TableCell>{((order.quantity - (order.quantity || 0)) / order.quantity * 100).toFixed(1)}%</TableCell>
                  <TableCell>
                    <Chip 
                      label={order.status} 
                      color={order.status === 'FILLED' ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{new Date(order.createdAt).toLocaleTimeString()}</TableCell>
                  <TableCell>
                    {order.status === 'NEW' && (
                      <Button
                        size="small"
                        color="error"
                        onClick={() => handleCancelOrder(order.id)}
                      >
                        Cancel
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Order Confirmation Dialog */}
      <Dialog open={showOrderConfirm} onClose={() => setShowOrderConfirm(false)}>
        <DialogTitle>Confirm Order</DialogTitle>
        <DialogContent>
          <Typography>
            {orderSide} {orderQuantity} {selectedPairData?.baseAsset} 
            {orderType !== 'MARKET' && ` at ${orderPrice} ${selectedPairData?.quoteAsset}`}
          </Typography>
          {orderType === 'STOP_LOSS' && (
            <Typography>
              Stop Price: {stopPrice} {selectedPairData?.quoteAsset}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowOrderConfirm(false)}>Cancel</Button>
          <Button onClick={handlePlaceOrder} variant="contained">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={!!notification}
        autoHideDuration={6000}
        onClose={() => setNotification(null)}
      >
        {notification && (
          <Alert severity={notification.severity} onClose={() => setNotification(null)}>
            {notification.message}
          </Alert>
        )}
      </Snackbar>
    </Box>
  );
};

export default TradingPlatform;