import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Tabs,
  Tab,
  LinearProgress,
  CircularProgress,
  Badge,
  Avatar
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  SwapHoriz as SwapHorizIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  MonetizationOn as MonetizationOnIcon,
  AccountBalance as AccountBalanceIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

interface TradingPair {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  status: string;
  min_qty: string;
  max_qty: string;
  step_size: string;
  min_price: string;
  max_price: string;
  tick_size: string;
  min_notional: string;
  maker_fee: string;
  taker_fee: string;
  is_spot_trading_allowed: boolean;
  is_margin_trading_allowed: boolean;
  is_futures_trading_allowed: boolean;
  created_at: string;
  updated_at: string;
}

interface TradingStats {
  volume_24h: string;
  trades_24h: number;
  active_orders: number;
  fee_revenue_24h: string;
  top_trading_pairs: Array<{
    symbol: string;
    trade_count: number;
    volume: string;
  }>;
}

interface RiskParameters {
  max_position_size?: string;
  max_daily_volume?: string;
  max_withdrawal_amount?: string;
  price_deviation_threshold?: string;
}

interface TradingHalt {
  symbol?: string;
  reason: string;
  start_time: string;
  end_time?: string;
  admin_id: string;
}

const TradingControl: React.FC = () => {
  const [tradingPairs, setTradingPairs] = useState<TradingPair[]>([]);
  const [tradingStats, setTradingStats] = useState<TradingStats | null>(null);
  const [riskParameters, setRiskParameters] = useState<RiskParameters>({});
  const [tradingHalts, setTradingHalts] = useState<TradingHalt[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  
  // Dialog states
  const [haltDialogOpen, setHaltDialogOpen] = useState(false);
  const [pairDialogOpen, setPairDialogOpen] = useState(false);
  const [riskDialogOpen, setRiskDialogOpen] = useState(false);
  
  // Form states
  const [haltSymbol, setHaltSymbol] = useState('');
  const [haltReason, setHaltReason] = useState('');
  const [haltDuration, setHaltDuration] = useState('');
  const [haltAction, setHaltAction] = useState('HALT');
  
  const [newPair, setNewPair] = useState({
    symbol: '',
    base_asset: '',
    quote_asset: '',
    min_qty: '',
    max_qty: '',
    step_size: '',
    min_price: '',
    max_price: '',
    tick_size: '',
    min_notional: '',
    maker_fee: '',
    taker_fee: ''
  });

  const [newRiskParams, setNewRiskParams] = useState<RiskParameters>({});

  useEffect(() => {
    loadTradingData();
    loadTradingPairs();
    loadRiskParameters();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadTradingData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadTradingData = async () => {
    try {
      const response = await fetch('/api/v1/admin/dashboard/overview', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTradingStats(data.trading_analytics);
      }
    } catch (error) {
      console.error('Error loading trading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTradingPairs = async () => {
    try {
      const response = await fetch('/api/v1/admin/trading/pairs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTradingPairs(data.trading_pairs);
      }
    } catch (error) {
      console.error('Error loading trading pairs:', error);
    }
  };

  const loadRiskParameters = async () => {
    try {
      // Load current risk parameters from Redis/database
      // This would be implemented based on your backend API
      setRiskParameters({
        max_position_size: '1000000',
        max_daily_volume: '10000000',
        max_withdrawal_amount: '100000',
        price_deviation_threshold: '0.05'
      });
    } catch (error) {
      console.error('Error loading risk parameters:', error);
    }
  };

  const handleTradingControl = async () => {
    try {
      const response = await fetch('/api/v1/admin/trading/control', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          action: haltAction,
          symbol: haltSymbol || undefined,
          reason: haltReason,
          duration_minutes: haltDuration ? parseInt(haltDuration) : undefined
        })
      });

      if (response.ok) {
        setHaltDialogOpen(false);
        setHaltSymbol('');
        setHaltReason('');
        setHaltDuration('');
        loadTradingData();
      }
    } catch (error) {
      console.error('Error controlling trading:', error);
    }
  };

  const handleCreateTradingPair = async () => {
    try {
      const response = await fetch('/api/v1/admin/trading/pairs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify(newPair)
      });

      if (response.ok) {
        setPairDialogOpen(false);
        setNewPair({
          symbol: '',
          base_asset: '',
          quote_asset: '',
          min_qty: '',
          max_qty: '',
          step_size: '',
          min_price: '',
          max_price: '',
          tick_size: '',
          min_notional: '',
          maker_fee: '',
          taker_fee: ''
        });
        loadTradingPairs();
      }
    } catch (error) {
      console.error('Error creating trading pair:', error);
    }
  };

  const handleUpdateRiskParameters = async () => {
    try {
      const response = await fetch('/api/v1/admin/risk/parameters', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify(newRiskParams)
      });

      if (response.ok) {
        setRiskDialogOpen(false);
        setRiskParameters({ ...riskParameters, ...newRiskParams });
        setNewRiskParams({});
      }
    } catch (error) {
      console.error('Error updating risk parameters:', error);
    }
  };

  const togglePairStatus = async (symbol: string, currentStatus: string) => {
    const newStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    
    try {
      const response = await fetch(`/api/v1/admin/trading/pairs/${symbol}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        loadTradingPairs();
      }
    } catch (error) {
      console.error('Error updating pair status:', error);
    }
  };

  const formatCurrency = (amount: string) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num);
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Trading Control Center
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            color="error"
            startIcon={<StopIcon />}
            onClick={() => {
              setHaltAction('HALT');
              setHaltDialogOpen(true);
            }}
          >
            Emergency Halt
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadTradingData}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Trading Stats Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    24h Volume
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatCurrency(tradingStats?.volume_24h || '0')}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <TrendingUpIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    24h Trades
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatNumber(tradingStats?.trades_24h || 0)}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <SwapHorizIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Orders
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatNumber(tradingStats?.active_orders || 0)}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <TimelineIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Fee Revenue
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatCurrency(tradingStats?.fee_revenue_24h || '0')}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <MonetizationOnIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                color="error"
                startIcon={<StopIcon />}
                onClick={() => {
                  setHaltAction('HALT');
                  setHaltDialogOpen(true);
                }}
              >
                Halt Trading
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                color="success"
                startIcon={<PlayIcon />}
                onClick={() => {
                  setHaltAction('RESUME');
                  setHaltDialogOpen(true);
                }}
              >
                Resume Trading
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                color="warning"
                startIcon={<WarningIcon />}
                onClick={() => {
                  setHaltAction('RESTRICT');
                  setHaltDialogOpen(true);
                }}
              >
                Restrict Trading
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<SettingsIcon />}
                onClick={() => setRiskDialogOpen(true)}
              >
                Risk Settings
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Card>
        <CardContent>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab label="Trading Pairs" />
            <Tab label="Top Performers" />
            <Tab label="Risk Parameters" />
            <Tab label="Trading Halts" />
          </Tabs>

          {selectedTab === 0 && (
            <Box sx={{ mt: 2 }}>
              <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                <Typography variant="h6">Trading Pairs Management</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setPairDialogOpen(true)}
                >
                  Add Pair
                </Button>
              </Box>
              
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Base/Quote</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Min Quantity</TableCell>
                      <TableCell>Min Price</TableCell>
                      <TableCell>Maker Fee</TableCell>
                      <TableCell>Taker Fee</TableCell>
                      <TableCell>Trading Types</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tradingPairs.map((pair) => (
                      <TableRow key={pair.symbol}>
                        <TableCell>
                          <Typography fontWeight="bold">{pair.symbol}</Typography>
                        </TableCell>
                        <TableCell>{pair.base_asset}/{pair.quote_asset}</TableCell>
                        <TableCell>
                          <Chip
                            label={pair.status}
                            color={pair.status === 'ACTIVE' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{pair.min_qty}</TableCell>
                        <TableCell>{pair.min_price}</TableCell>
                        <TableCell>{(parseFloat(pair.maker_fee) * 100).toFixed(3)}%</TableCell>
                        <TableCell>{(parseFloat(pair.taker_fee) * 100).toFixed(3)}%</TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            {pair.is_spot_trading_allowed && (
                              <Chip label="Spot" size="small" />
                            )}
                            {pair.is_margin_trading_allowed && (
                              <Chip label="Margin" size="small" />
                            )}
                            {pair.is_futures_trading_allowed && (
                              <Chip label="Futures" size="small" />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <Tooltip title="Toggle Status">
                              <IconButton
                                size="small"
                                onClick={() => togglePairStatus(pair.symbol, pair.status)}
                              >
                                {pair.status === 'ACTIVE' ? <PauseIcon /> : <PlayIcon />}
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Edit">
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="View Details">
                              <IconButton size="small">
                                <VisibilityIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {selectedTab === 1 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>Top Trading Pairs (24h)</Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Trade Count</TableCell>
                      <TableCell align="right">Volume</TableCell>
                      <TableCell align="right">Market Share</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tradingStats?.top_trading_pairs.map((pair) => (
                      <TableRow key={pair.symbol}>
                        <TableCell>
                          <Typography fontWeight="bold">{pair.symbol}</Typography>
                        </TableCell>
                        <TableCell align="right">{formatNumber(pair.trade_count)}</TableCell>
                        <TableCell align="right">{formatCurrency(pair.volume)}</TableCell>
                        <TableCell align="right">
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinearProgress
                              variant="determinate"
                              value={(parseFloat(pair.volume) / parseFloat(tradingStats.volume_24h)) * 100}
                              sx={{ width: 100 }}
                            />
                            <Typography variant="caption">
                              {((parseFloat(pair.volume) / parseFloat(tradingStats.volume_24h)) * 100).toFixed(1)}%
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {selectedTab === 2 && (
            <Box sx={{ mt: 2 }}>
              <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                <Typography variant="h6">Risk Management Parameters</Typography>
                <Button
                  variant="contained"
                  startIcon={<EditIcon />}
                  onClick={() => setRiskDialogOpen(true)}
                >
                  Update Parameters
                </Button>
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Position Limits</Typography>
                      <List>
                        <ListItem>
                          <ListItemText
                            primary="Max Position Size"
                            secondary={formatCurrency(riskParameters.max_position_size || '0')}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Max Daily Volume"
                            secondary={formatCurrency(riskParameters.max_daily_volume || '0')}
                          />
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Risk Thresholds</Typography>
                      <List>
                        <ListItem>
                          <ListItemText
                            primary="Max Withdrawal Amount"
                            secondary={formatCurrency(riskParameters.max_withdrawal_amount || '0')}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Price Deviation Threshold"
                            secondary={`${(parseFloat(riskParameters.price_deviation_threshold || '0') * 100).toFixed(1)}%`}
                          />
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}

          {selectedTab === 3 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>Active Trading Halts</Typography>
              {tradingHalts.length > 0 ? (
                <List>
                  {tradingHalts.map((halt, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <StopIcon color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={halt.symbol ? `${halt.symbol} Trading Halt` : 'Global Trading Halt'}
                        secondary={
                          <Box>
                            <Typography variant="body2">Reason: {halt.reason}</Typography>
                            <Typography variant="body2">
                              Started: {format(new Date(halt.start_time), 'MMM dd, yyyy HH:mm')}
                            </Typography>
                            {halt.end_time && (
                              <Typography variant="body2">
                                Ends: {format(new Date(halt.end_time), 'MMM dd, yyyy HH:mm')}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                      <Button
                        variant="outlined"
                        color="success"
                        size="small"
                        onClick={() => {
                          setHaltAction('RESUME');
                          setHaltSymbol(halt.symbol || '');
                          setHaltDialogOpen(true);
                        }}
                      >
                        Resume
                      </Button>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Alert severity="info">No active trading halts</Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Trading Control Dialog */}
      <Dialog open={haltDialogOpen} onClose={() => setHaltDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Trading Control - {haltAction}
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Symbol (Optional)</InputLabel>
            <Select
              value={haltSymbol}
              onChange={(e) => setHaltSymbol(e.target.value)}
              label="Symbol (Optional)"
            >
              <MenuItem value="">All Symbols</MenuItem>
              {tradingPairs.map((pair) => (
                <MenuItem key={pair.symbol} value={pair.symbol}>
                  {pair.symbol}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason"
            value={haltReason}
            onChange={(e) => setHaltReason(e.target.value)}
            sx={{ mt: 2 }}
            required
          />
          
          {haltAction !== 'RESUME' && (
            <TextField
              fullWidth
              type="number"
              label="Duration (minutes, optional)"
              value={haltDuration}
              onChange={(e) => setHaltDuration(e.target.value)}
              sx={{ mt: 2 }}
              helperText="Leave empty for indefinite duration"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHaltDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleTradingControl}
            variant="contained"
            color={haltAction === 'HALT' ? 'error' : haltAction === 'RESUME' ? 'success' : 'warning'}
          >
            {haltAction}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Trading Pair Dialog */}
      <Dialog open={pairDialogOpen} onClose={() => setPairDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Trading Pair</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Symbol"
                value={newPair.symbol}
                onChange={(e) => setNewPair({ ...newPair, symbol: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Base Asset"
                value={newPair.base_asset}
                onChange={(e) => setNewPair({ ...newPair, base_asset: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Quote Asset"
                value={newPair.quote_asset}
                onChange={(e) => setNewPair({ ...newPair, quote_asset: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Min Quantity"
                value={newPair.min_qty}
                onChange={(e) => setNewPair({ ...newPair, min_qty: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Quantity"
                value={newPair.max_qty}
                onChange={(e) => setNewPair({ ...newPair, max_qty: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Step Size"
                value={newPair.step_size}
                onChange={(e) => setNewPair({ ...newPair, step_size: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tick Size"
                value={newPair.tick_size}
                onChange={(e) => setNewPair({ ...newPair, tick_size: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Maker Fee (%)"
                value={newPair.maker_fee}
                onChange={(e) => setNewPair({ ...newPair, maker_fee: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Taker Fee (%)"
                value={newPair.taker_fee}
                onChange={(e) => setNewPair({ ...newPair, taker_fee: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPairDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateTradingPair} variant="contained">
            Create Pair
          </Button>
        </DialogActions>
      </Dialog>

      {/* Risk Parameters Dialog */}
      <Dialog open={riskDialogOpen} onClose={() => setRiskDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Update Risk Parameters</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Max Position Size"
            value={newRiskParams.max_position_size || ''}
            onChange={(e) => setNewRiskParams({ ...newRiskParams, max_position_size: e.target.value })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="Max Daily Volume"
            value={newRiskParams.max_daily_volume || ''}
            onChange={(e) => setNewRiskParams({ ...newRiskParams, max_daily_volume: e.target.value })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="Max Withdrawal Amount"
            value={newRiskParams.max_withdrawal_amount || ''}
            onChange={(e) => setNewRiskParams({ ...newRiskParams, max_withdrawal_amount: e.target.value })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="Price Deviation Threshold (%)"
            value={newRiskParams.price_deviation_threshold || ''}
            onChange={(e) => setNewRiskParams({ ...newRiskParams, price_deviation_threshold: e.target.value })}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRiskDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpdateRiskParameters} variant="contained">
            Update Parameters
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TradingControl;