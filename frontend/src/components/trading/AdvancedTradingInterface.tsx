import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Slider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Badge,
  LinearProgress,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ShowChartIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Settings as SettingsIcon,
  Fullscreen as FullscreenIcon,
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Share as ShareIcon,
  Notifications as NotificationsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';
import { createChart, ColorType, CrosshairMode, LineStyle } from 'lightweight-charts';

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

interface OrderBookEntry {
  price: number;
  quantity: number;
  total: number;
}

interface Trade {
  id: string;
  price: number;
  quantity: number;
  side: 'BUY' | 'SELL';
  timestamp: Date;
}

interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  markPrice: number;
  unrealizedPnl: number;
  margin: number;
  leverage: number;
}

interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: string;
  quantity: number;
  price: number;
  filled: number;
  status: string;
  timestamp: Date;
}

const AdvancedTradingInterface: React.FC = () => {
  const [selectedPair, setSelectedPair] = useState<TradingPair>({
    symbol: 'BTCUSDT',
    baseAsset: 'BTC',
    quoteAsset: 'USDT',
    price: 45000,
    change24h: 2.5,
    volume24h: 1234567890,
    high24h: 46000,
    low24h: 44000
  });

  const [tradingMode, setTradingMode] = useState('SPOT'); // SPOT, MARGIN, FUTURES, OPTIONS
  const [orderType, setOrderType] = useState('LIMIT');
  const [orderSide, setOrderSide] = useState('BUY');
  const [orderQuantity, setOrderQuantity] = useState('');
  const [orderPrice, setOrderPrice] = useState('');
  const [leverage, setLeverage] = useState(1);
  const [marginType, setMarginType] = useState('CROSS');
  
  const [orderBook, setOrderBook] = useState<{
    bids: OrderBookEntry[];
    asks: OrderBookEntry[];
  }>({
    bids: [],
    asks: []
  });

  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [openOrders, setOpenOrders] = useState<Order[]>([]);
  const [orderHistory, setOrderHistory] = useState<Order[]>([]);

  const [selectedTab, setSelectedTab] = useState(0);
  const [chartInterval, setChartInterval] = useState('1h');
  const [showOrderBook, setShowOrderBook] = useState(true);
  const [showTrades, setShowTrades] = useState(true);
  const [showPositions, setShowPositions] = useState(true);
  
  const [balance, setBalance] = useState({
    available: 10000,
    locked: 500,
    total: 10500
  });

  const [riskMetrics, setRiskMetrics] = useState({
    totalEquity: 10500,
    unrealizedPnl: 250,
    marginUsed: 2000,
    marginAvailable: 8500,
    marginRatio: 0.19
  });

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  // Advanced order types
  const orderTypes = [
    'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT',
    'TRAILING_STOP', 'ICEBERG', 'TWAP', 'VWAP', 'POST_ONLY', 'REDUCE_ONLY'
  ];

  // Trading pairs
  const tradingPairs = [
    { symbol: 'BTCUSDT', price: 45000, change: 2.5 },
    { symbol: 'ETHUSDT', price: 3200, change: -1.2 },
    { symbol: 'BNBUSDT', price: 320, change: 3.8 },
    { symbol: 'ADAUSDT', price: 0.45, change: 5.2 },
    { symbol: 'SOLUSDT', price: 95, change: -2.1 },
    { symbol: 'DOTUSDT', price: 6.8, change: 1.9 },
    { symbol: 'AVAXUSDT', price: 28, change: 4.3 },
    { symbol: 'MATICUSDT', price: 0.85, change: -0.8 }
  ];

  useEffect(() => {
    initializeChart();
    loadMarketData();
    
    // Set up real-time data subscriptions
    const interval = setInterval(() => {
      updateMarketData();
    }, 1000);

    return () => {
      clearInterval(interval);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, []);

  const initializeChart = () => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a1a' },
        textColor: '#ffffff',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: '#485158',
      },
      timeScale: {
        borderColor: '#485158',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Sample data
    const candleData = generateSampleCandleData();
    const volumeData = generateSampleVolumeData();

    candlestickSeries.setData(candleData);
    volumeSeries.setData(volumeData);

    chartRef.current = chart;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  };

  const generateSampleCandleData = () => {
    const data = [];
    let time = Math.floor(Date.now() / 1000) - 86400; // 24 hours ago
    let price = 45000;

    for (let i = 0; i < 24; i++) {
      const open = price;
      const high = open + Math.random() * 1000;
      const low = open - Math.random() * 1000;
      const close = low + Math.random() * (high - low);

      data.push({
        time,
        open,
        high,
        low,
        close,
      });

      time += 3600; // 1 hour
      price = close;
    }

    return data;
  };

  const generateSampleVolumeData = () => {
    const data = [];
    let time = Math.floor(Date.now() / 1000) - 86400;

    for (let i = 0; i < 24; i++) {
      data.push({
        time,
        value: Math.random() * 1000000,
        color: Math.random() > 0.5 ? '#26a69a' : '#ef5350',
      });
      time += 3600;
    }

    return data;
  };

  const loadMarketData = () => {
    // Load order book
    const bids = Array.from({ length: 20 }, (_, i) => ({
      price: 45000 - (i + 1) * 10,
      quantity: Math.random() * 10,
      total: 0
    }));

    const asks = Array.from({ length: 20 }, (_, i) => ({
      price: 45000 + (i + 1) * 10,
      quantity: Math.random() * 10,
      total: 0
    }));

    // Calculate totals
    let bidTotal = 0;
    bids.forEach(bid => {
      bidTotal += bid.quantity;
      bid.total = bidTotal;
    });

    let askTotal = 0;
    asks.forEach(ask => {
      askTotal += ask.quantity;
      ask.total = askTotal;
    });

    setOrderBook({ bids, asks });

    // Load recent trades
    const trades = Array.from({ length: 50 }, (_, i) => ({
      id: `trade_${i}`,
      price: 45000 + (Math.random() - 0.5) * 200,
      quantity: Math.random() * 5,
      side: Math.random() > 0.5 ? 'BUY' : 'SELL' as 'BUY' | 'SELL',
      timestamp: new Date(Date.now() - i * 10000)
    }));

    setRecentTrades(trades);

    // Load positions
    const samplePositions = [
      {
        symbol: 'BTCUSDT',
        side: 'LONG' as 'LONG',
        size: 0.5,
        entryPrice: 44500,
        markPrice: 45000,
        unrealizedPnl: 250,
        margin: 2000,
        leverage: 10
      }
    ];

    setPositions(samplePositions);

    // Load open orders
    const sampleOrders = [
      {
        id: 'order_1',
        symbol: 'BTCUSDT',
        side: 'BUY' as 'BUY',
        type: 'LIMIT',
        quantity: 0.1,
        price: 44000,
        filled: 0,
        status: 'NEW',
        timestamp: new Date()
      }
    ];

    setOpenOrders(sampleOrders);
  };

  const updateMarketData = () => {
    // Simulate real-time price updates
    setSelectedPair(prev => ({
      ...prev,
      price: prev.price + (Math.random() - 0.5) * 100
    }));

    // Update order book
    setOrderBook(prev => ({
      bids: prev.bids.map(bid => ({
        ...bid,
        quantity: bid.quantity + (Math.random() - 0.5) * 0.1
      })),
      asks: prev.asks.map(ask => ({
        ...ask,
        quantity: ask.quantity + (Math.random() - 0.5) * 0.1
      }))
    }));
  };

  const handlePlaceOrder = () => {
    const newOrder: Order = {
      id: `order_${Date.now()}`,
      symbol: selectedPair.symbol,
      side: orderSide as 'BUY' | 'SELL',
      type: orderType,
      quantity: parseFloat(orderQuantity),
      price: parseFloat(orderPrice),
      filled: 0,
      status: 'NEW',
      timestamp: new Date()
    };

    setOpenOrders(prev => [...prev, newOrder]);
    
    // Clear form
    setOrderQuantity('');
    setOrderPrice('');
  };

  const handleCancelOrder = (orderId: string) => {
    setOpenOrders(prev => prev.filter(order => order.id !== orderId));
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a' }}>
      {/* Top Bar */}
      <Box sx={{ p: 1, bgcolor: '#1a1a1a', borderBottom: '1px solid #2a2a2a' }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select
                value={selectedPair.symbol}
                onChange={(e) => {
                  const pair = tradingPairs.find(p => p.symbol === e.target.value);
                  if (pair) {
                    setSelectedPair(prev => ({ ...prev, ...pair }));
                  }
                }}
                sx={{ color: 'white' }}
              >
                {tradingPairs.map((pair) => (
                  <MenuItem key={pair.symbol} value={pair.symbol}>
                    {pair.symbol}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item>
            <Typography variant="h6" color="white">
              {formatCurrency(selectedPair.price)}
            </Typography>
          </Grid>
          
          <Grid item>
            <Chip
              label={`${selectedPair.change24h > 0 ? '+' : ''}${selectedPair.change24h}%`}
              color={selectedPair.change24h > 0 ? 'success' : 'error'}
              size="small"
            />
          </Grid>
          
          <Grid item>
            <Typography variant="body2" color="grey.400">
              24h Vol: {formatNumber(selectedPair.volume24h / 1000000, 1)}M
            </Typography>
          </Grid>
          
          <Grid item>
            <Typography variant="body2" color="grey.400">
              24h High: {formatCurrency(selectedPair.high24h)}
            </Typography>
          </Grid>
          
          <Grid item>
            <Typography variant="body2" color="grey.400">
              24h Low: {formatCurrency(selectedPair.low24h)}
            </Typography>
          </Grid>
          
          <Grid item sx={{ ml: 'auto' }}>
            <Box display="flex" gap={1}>
              <Tooltip title="Trading Mode">
                <FormControl size="small">
                  <Select
                    value={tradingMode}
                    onChange={(e) => setTradingMode(e.target.value)}
                    sx={{ color: 'white', minWidth: 80 }}
                  >
                    <MenuItem value="SPOT">Spot</MenuItem>
                    <MenuItem value="MARGIN">Margin</MenuItem>
                    <MenuItem value="FUTURES">Futures</MenuItem>
                    <MenuItem value="OPTIONS">Options</MenuItem>
                  </Select>
                </FormControl>
              </Tooltip>
              
              <Tooltip title="Settings">
                <IconButton size="small" sx={{ color: 'white' }}>
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Fullscreen">
                <IconButton size="small" sx={{ color: 'white' }}>
                  <FullscreenIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Main Trading Interface */}
      <Grid container sx={{ flex: 1, height: 'calc(100vh - 64px)' }}>
        {/* Left Panel - Order Book & Trades */}
        <Grid item xs={3} sx={{ borderRight: '1px solid #2a2a2a', height: '100%' }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Tabs
              value={selectedTab}
              onChange={(e, newValue) => setSelectedTab(newValue)}
              sx={{ borderBottom: '1px solid #2a2a2a' }}
            >
              <Tab label="Order Book" sx={{ color: 'white' }} />
              <Tab label="Trades" sx={{ color: 'white' }} />
            </Tabs>

            {selectedTab === 0 && (
              <Box sx={{ flex: 1, overflow: 'hidden' }}>
                {/* Order Book */}
                <Box sx={{ height: '50%', overflow: 'auto' }}>
                  <Typography variant="subtitle2" sx={{ p: 1, color: 'white', bgcolor: '#1a1a1a' }}>
                    Order Book
                  </Typography>
                  
                  {/* Asks */}
                  <Box sx={{ height: '50%', overflow: 'auto' }}>
                    {orderBook.asks.slice().reverse().map((ask, index) => (
                      <Box
                        key={index}
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          p: 0.5,
                          fontSize: '0.75rem',
                          color: '#ef5350',
                          '&:hover': { bgcolor: '#2a2a2a' }
                        }}
                      >
                        <span>{formatNumber(ask.price, 2)}</span>
                        <span>{formatNumber(ask.quantity, 4)}</span>
                        <span>{formatNumber(ask.total, 4)}</span>
                      </Box>
                    ))}
                  </Box>
                  
                  {/* Spread */}
                  <Box sx={{ p: 1, textAlign: 'center', bgcolor: '#1a1a1a', color: 'white' }}>
                    <Typography variant="body2">
                      Spread: {formatNumber(orderBook.asks[0]?.price - orderBook.bids[0]?.price, 2)}
                    </Typography>
                  </Box>
                  
                  {/* Bids */}
                  <Box sx={{ height: '50%', overflow: 'auto' }}>
                    {orderBook.bids.map((bid, index) => (
                      <Box
                        key={index}
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          p: 0.5,
                          fontSize: '0.75rem',
                          color: '#26a69a',
                          '&:hover': { bgcolor: '#2a2a2a' }
                        }}
                      >
                        <span>{formatNumber(bid.price, 2)}</span>
                        <span>{formatNumber(bid.quantity, 4)}</span>
                        <span>{formatNumber(bid.total, 4)}</span>
                      </Box>
                    ))}
                  </Box>
                </Box>
              </Box>
            )}

            {selectedTab === 1 && (
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                <Typography variant="subtitle2" sx={{ p: 1, color: 'white', bgcolor: '#1a1a1a' }}>
                  Recent Trades
                </Typography>
                {recentTrades.map((trade) => (
                  <Box
                    key={trade.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      p: 0.5,
                      fontSize: '0.75rem',
                      color: trade.side === 'BUY' ? '#26a69a' : '#ef5350',
                      '&:hover': { bgcolor: '#2a2a2a' }
                    }}
                  >
                    <span>{formatNumber(trade.price, 2)}</span>
                    <span>{formatNumber(trade.quantity, 4)}</span>
                    <span>{trade.timestamp.toLocaleTimeString()}</span>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </Grid>

        {/* Center Panel - Chart */}
        <Grid item xs={6} sx={{ height: '100%' }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Chart Controls */}
            <Box sx={{ p: 1, bgcolor: '#1a1a1a', borderBottom: '1px solid #2a2a2a' }}>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="body2" color="white">Interval:</Typography>
                {['1m', '5m', '15m', '1h', '4h', '1d'].map((interval) => (
                  <Button
                    key={interval}
                    size="small"
                    variant={chartInterval === interval ? 'contained' : 'outlined'}
                    onClick={() => setChartInterval(interval)}
                    sx={{ minWidth: 40 }}
                  >
                    {interval}
                  </Button>
                ))}
                
                <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                  <Tooltip title="Indicators">
                    <IconButton size="small" sx={{ color: 'white' }}>
                      <TimelineIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Drawing Tools">
                    <IconButton size="small" sx={{ color: 'white' }}>
                      <ShowChartIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Save Layout">
                    <IconButton size="small" sx={{ color: 'white' }}>
                      <SaveIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            </Box>

            {/* Chart */}
            <Box ref={chartContainerRef} sx={{ flex: 1 }} />
          </Box>
        </Grid>

        {/* Right Panel - Trading & Positions */}
        <Grid item xs={3} sx={{ borderLeft: '1px solid #2a2a2a', height: '100%' }}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Trading Panel */}
            <Box sx={{ p: 2, borderBottom: '1px solid #2a2a2a' }}>
              <Typography variant="h6" color="white" gutterBottom>
                Place Order
              </Typography>

              {/* Order Type Tabs */}
              <Box sx={{ mb: 2 }}>
                <Button
                  variant={orderSide === 'BUY' ? 'contained' : 'outlined'}
                  color="success"
                  onClick={() => setOrderSide('BUY')}
                  sx={{ mr: 1 }}
                >
                  Buy
                </Button>
                <Button
                  variant={orderSide === 'SELL' ? 'contained' : 'outlined'}
                  color="error"
                  onClick={() => setOrderSide('SELL')}
                >
                  Sell
                </Button>
              </Box>

              {/* Order Type */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel sx={{ color: 'white' }}>Order Type</InputLabel>
                <Select
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value)}
                  sx={{ color: 'white' }}
                >
                  {orderTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.replace('_', ' ')}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Leverage (for margin/futures) */}
              {(tradingMode === 'MARGIN' || tradingMode === 'FUTURES') && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="white" gutterBottom>
                    Leverage: {leverage}x
                  </Typography>
                  <Slider
                    value={leverage}
                    onChange={(e, newValue) => setLeverage(newValue as number)}
                    min={1}
                    max={125}
                    step={1}
                    marks={[
                      { value: 1, label: '1x' },
                      { value: 25, label: '25x' },
                      { value: 50, label: '50x' },
                      { value: 100, label: '100x' },
                      { value: 125, label: '125x' }
                    ]}
                    sx={{ color: 'primary.main' }}
                  />
                </Box>
              )}

              {/* Quantity */}
              <TextField
                fullWidth
                label="Quantity"
                value={orderQuantity}
                onChange={(e) => setOrderQuantity(e.target.value)}
                sx={{ mb: 2 }}
                InputLabelProps={{ style: { color: 'white' } }}
                InputProps={{ style: { color: 'white' } }}
              />

              {/* Price */}
              {orderType !== 'MARKET' && (
                <TextField
                  fullWidth
                  label="Price"
                  value={orderPrice}
                  onChange={(e) => setOrderPrice(e.target.value)}
                  sx={{ mb: 2 }}
                  InputLabelProps={{ style: { color: 'white' } }}
                  InputProps={{ style: { color: 'white' } }}
                />
              )}

              {/* Order Summary */}
              <Box sx={{ mb: 2, p: 1, bgcolor: '#1a1a1a', borderRadius: 1 }}>
                <Typography variant="body2" color="white">
                  Total: {formatCurrency(parseFloat(orderQuantity || '0') * parseFloat(orderPrice || '0'))}
                </Typography>
                <Typography variant="body2" color="grey.400">
                  Available: {formatCurrency(balance.available)}
                </Typography>
              </Box>

              {/* Place Order Button */}
              <Button
                fullWidth
                variant="contained"
                color={orderSide === 'BUY' ? 'success' : 'error'}
                onClick={handlePlaceOrder}
                disabled={!orderQuantity || (orderType !== 'MARKET' && !orderPrice)}
              >
                {orderSide} {selectedPair.baseAsset}
              </Button>
            </Box>

            {/* Positions & Orders */}
            <Box sx={{ flex: 1, overflow: 'hidden' }}>
              <Tabs
                value={0}
                sx={{ borderBottom: '1px solid #2a2a2a' }}
              >
                <Tab label="Positions" sx={{ color: 'white' }} />
                <Tab label="Open Orders" sx={{ color: 'white' }} />
                <Tab label="Order History" sx={{ color: 'white' }} />
              </Tabs>

              {/* Positions */}
              <Box sx={{ p: 1, overflow: 'auto', height: 'calc(100% - 48px)' }}>
                {positions.length > 0 ? (
                  positions.map((position, index) => (
                    <Card key={index} sx={{ mb: 1, bgcolor: '#1a1a1a' }}>
                      <CardContent sx={{ p: 1 }}>
                        <Box display="flex" justifyContent="between" alignItems="center">
                          <Typography variant="body2" color="white">
                            {position.symbol}
                          </Typography>
                          <Chip
                            label={position.side}
                            color={position.side === 'LONG' ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                        <Typography variant="body2" color="grey.400">
                          Size: {formatNumber(position.size, 4)}
                        </Typography>
                        <Typography variant="body2" color="grey.400">
                          Entry: {formatCurrency(position.entryPrice)}
                        </Typography>
                        <Typography variant="body2" color="grey.400">
                          Mark: {formatCurrency(position.markPrice)}
                        </Typography>
                        <Typography
                          variant="body2"
                          color={position.unrealizedPnl >= 0 ? 'success.main' : 'error.main'}
                        >
                          PnL: {formatCurrency(position.unrealizedPnl)}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <Typography variant="body2" color="grey.400" textAlign="center" sx={{ mt: 2 }}>
                    No open positions
                  </Typography>
                )}

                {/* Open Orders */}
                {openOrders.map((order) => (
                  <Card key={order.id} sx={{ mb: 1, bgcolor: '#1a1a1a' }}>
                    <CardContent sx={{ p: 1 }}>
                      <Box display="flex" justifyContent="between" alignItems="center">
                        <Typography variant="body2" color="white">
                          {order.symbol}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={() => handleCancelOrder(order.id)}
                          sx={{ color: 'error.main' }}
                        >
                          <StopIcon />
                        </IconButton>
                      </Box>
                      <Typography variant="body2" color="grey.400">
                        {order.side} {formatNumber(order.quantity, 4)} @ {formatCurrency(order.price)}
                      </Typography>
                      <Typography variant="body2" color="grey.400">
                        Type: {order.type}
                      </Typography>
                      <Chip
                        label={order.status}
                        size="small"
                        color="info"
                      />
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Box>
          </Box>
        </Grid>
      </Grid>

      {/* Bottom Status Bar */}
      <Box sx={{ p: 1, bgcolor: '#1a1a1a', borderTop: '1px solid #2a2a2a' }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item>
            <Typography variant="body2" color="white">
              Total Equity: {formatCurrency(riskMetrics.totalEquity)}
            </Typography>
          </Grid>
          <Grid item>
            <Typography
              variant="body2"
              color={riskMetrics.unrealizedPnl >= 0 ? 'success.main' : 'error.main'}
            >
              Unrealized PnL: {formatCurrency(riskMetrics.unrealizedPnl)}
            </Typography>
          </Grid>
          <Grid item>
            <Typography variant="body2" color="white">
              Margin Used: {formatCurrency(riskMetrics.marginUsed)}
            </Typography>
          </Grid>
          <Grid item>
            <Typography variant="body2" color="white">
              Margin Available: {formatCurrency(riskMetrics.marginAvailable)}
            </Typography>
          </Grid>
          <Grid item>
            <Typography variant="body2" color="white">
              Margin Ratio: {formatNumber(riskMetrics.marginRatio * 100, 2)}%
            </Typography>
          </Grid>
          <Grid item sx={{ ml: 'auto' }}>
            <Box display="flex" alignItems="center" gap={1}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'success.main'
                }}
              />
              <Typography variant="body2" color="white">
                Connected
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default AdvancedTradingInterface;