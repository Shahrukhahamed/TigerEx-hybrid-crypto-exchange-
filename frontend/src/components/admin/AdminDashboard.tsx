import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  LinearProgress,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Badge,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon,
  SwapHoriz as SwapHorizIcon,
  MonetizationOn as MonetizationOnIcon,
  Shield as ShieldIcon,
  Gavel as GavelIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  CloudUpload as CloudUploadIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Phone as PhoneIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  newUsers: number;
  volume24h: string;
  trades24h: number;
  feeRevenue24h: string;
  activeOrders: number;
  highRiskUsers: number;
  pendingKyc: number;
  systemAlerts: number;
}

interface UserAnalytics {
  totalUsers: number;
  activeUsers: number;
  newUsers: number;
  kycStatistics: Array<{ kyc_status: string; count: number }>;
  volumeStatistics: Array<{ vip_level: number; volume: string; users: number }>;
  geographicDistribution: Array<{ country: string; count: number }>;
}

interface TradingAnalytics {
  volume24h: string;
  trades24h: number;
  topTradingPairs: Array<{
    symbol: string;
    trade_count: number;
    volume: string;
  }>;
  activeOrders: number;
  feeRevenue24h: string;
}

interface RiskMetrics {
  highRiskUsers: Array<{
    user_id: string;
    risk_score: number;
    total_trading_volume: string;
  }>;
  largePositions: Array<{
    user_id: string;
    symbol: string;
    size: string;
    mark_price: string;
    unrealized_pnl: string;
  }>;
  liquidationRisks: Array<{
    user_id: string;
    symbol: string;
    ltv: string;
    liquidation_threshold: string;
  }>;
  suspiciousActivities: Array<{
    user_id: string;
    activity_type: string;
    risk_score: number;
    timestamp: string;
  }>;
}

interface SystemAlert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  is_resolved: boolean;
  created_at: string;
}

const AdminDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<{
    userAnalytics: UserAnalytics;
    tradingAnalytics: TradingAnalytics;
    riskMetrics: RiskMetrics;
  } | null>(null);
  const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([]);
  const [selectedTab, setSelectedTab] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('24h');

  // Chart data states
  const [volumeChartData, setVolumeChartData] = useState([]);
  const [userGrowthData, setUserGrowthData] = useState([]);
  const [revenueData, setRevenueData] = useState([]);

  useEffect(() => {
    loadDashboardData();
    loadSystemAlerts();
    loadChartData();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      loadDashboardData();
      loadSystemAlerts();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [timeRange]);

  const loadDashboardData = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/v1/admin/dashboard/overview', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadSystemAlerts = async () => {
    try {
      const response = await fetch('/api/v1/admin/system/alerts?limit=10', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSystemAlerts(data.alerts);
      }
    } catch (error) {
      console.error('Error loading system alerts:', error);
    }
  };

  const loadChartData = async () => {
    try {
      // Load volume chart data
      const volumeResponse = await fetch(`/api/v1/admin/analytics/charts?chart_type=trading_volume&period=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (volumeResponse.ok) {
        const volumeData = await volumeResponse.json();
        setVolumeChartData(volumeData.chart_data);
      }

      // Load user growth data
      const userResponse = await fetch('/api/v1/admin/analytics/charts?chart_type=user_growth&period=30d', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUserGrowthData(userData.chart_data);
      }

      // Load revenue data
      const revenueResponse = await fetch('/api/v1/admin/analytics/charts?chart_type=fee_revenue&period=30d', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (revenueResponse.ok) {
        const revenueData = await revenueResponse.json();
        setRevenueData(revenueData.chart_data);
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
    loadSystemAlerts();
    loadChartData();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Admin Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small">
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="1h">1 Hour</MenuItem>
              <MenuItem value="24h">24 Hours</MenuItem>
              <MenuItem value="7d">7 Days</MenuItem>
              <MenuItem value="30d">30 Days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Users
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatNumber(dashboardData?.userAnalytics.totalUsers || 0)}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    +{dashboardData?.userAnalytics.newUsers || 0} new today
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <PeopleIcon />
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
                    24h Volume
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatCurrency(dashboardData?.tradingAnalytics.volume24h || '0')}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    {dashboardData?.tradingAnalytics.trades24h || 0} trades
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
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
                    Fee Revenue
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatCurrency(dashboardData?.tradingAnalytics.feeRevenue24h || '0')}
                  </Typography>
                  <Typography variant="body2" color="info.main">
                    24h revenue
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <MonetizationOnIcon />
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
                    High Risk Users
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardData?.riskMetrics.highRiskUsers.length || 0}
                  </Typography>
                  <Typography variant="body2" color="warning.main">
                    Requires attention
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <SecurityIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Alerts */}
      {systemAlerts.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Badge badgeContent={systemAlerts.filter(a => !a.is_resolved).length} color="error">
                System Alerts
              </Badge>
            </Typography>
            <List>
              {systemAlerts.slice(0, 5).map((alert) => (
                <ListItem key={alert.id}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: getSeverityColor(alert.severity) + '.main' }}>
                      <WarningIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={alert.title}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          {alert.description}
                        </Typography>
                        <Chip
                          label={alert.severity}
                          size="small"
                          color={getSeverityColor(alert.severity) as any}
                          sx={{ mt: 1, mr: 1 }}
                        />
                        <Chip
                          label={alert.alert_type}
                          size="small"
                          variant="outlined"
                          sx={{ mt: 1 }}
                        />
                      </Box>
                    }
                  />
                  {!alert.is_resolved && (
                    <Button size="small" variant="outlined">
                      Resolve
                    </Button>
                  )}
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Charts Section */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trading Volume Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={volumeChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip formatter={(value) => formatCurrency(value as string)} />
                  <Area
                    type="monotone"
                    dataKey="volume"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                KYC Status Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={dashboardData?.userAnalytics.kycStatistics || []}
                    dataKey="count"
                    nameKey="kyc_status"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    label
                  >
                    {(dashboardData?.userAnalytics.kycStatistics || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['#0088FE', '#00C49F', '#FFBB28', '#FF8042'][index % 4]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Analytics Tabs */}
      <Card>
        <CardContent>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab label="Top Trading Pairs" />
            <Tab label="High Risk Users" />
            <Tab label="Large Positions" />
            <Tab label="Geographic Distribution" />
          </Tabs>

          {selectedTab === 0 && (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
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
                  {dashboardData?.tradingAnalytics.topTradingPairs.map((pair) => (
                    <TableRow key={pair.symbol}>
                      <TableCell component="th" scope="row">
                        <Typography fontWeight="bold">{pair.symbol}</Typography>
                      </TableCell>
                      <TableCell align="right">{formatNumber(pair.trade_count)}</TableCell>
                      <TableCell align="right">{formatCurrency(pair.volume)}</TableCell>
                      <TableCell align="right">
                        <LinearProgress
                          variant="determinate"
                          value={(parseFloat(pair.volume) / parseFloat(dashboardData.tradingAnalytics.volume24h)) * 100}
                          sx={{ width: 100 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {selectedTab === 1 && (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>User ID</TableCell>
                    <TableCell align="right">Risk Score</TableCell>
                    <TableCell align="right">Trading Volume</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData?.riskMetrics.highRiskUsers.map((user) => (
                    <TableRow key={user.user_id}>
                      <TableCell component="th" scope="row">
                        {user.user_id}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={user.risk_score.toFixed(2)}
                          color={user.risk_score > 0.9 ? 'error' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">{formatCurrency(user.total_trading_volume)}</TableCell>
                      <TableCell align="right">
                        <Button size="small" variant="outlined" color="warning">
                          Review
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {selectedTab === 2 && (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>User ID</TableCell>
                    <TableCell>Symbol</TableCell>
                    <TableCell align="right">Position Size</TableCell>
                    <TableCell align="right">Mark Price</TableCell>
                    <TableCell align="right">Unrealized PnL</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData?.riskMetrics.largePositions.map((position, index) => (
                    <TableRow key={index}>
                      <TableCell component="th" scope="row">
                        {position.user_id}
                      </TableCell>
                      <TableCell>{position.symbol}</TableCell>
                      <TableCell align="right">{position.size}</TableCell>
                      <TableCell align="right">{formatCurrency(position.mark_price)}</TableCell>
                      <TableCell align="right">
                        <Typography
                          color={parseFloat(position.unrealized_pnl) >= 0 ? 'success.main' : 'error.main'}
                        >
                          {formatCurrency(position.unrealized_pnl)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {selectedTab === 3 && (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Country</TableCell>
                    <TableCell align="right">User Count</TableCell>
                    <TableCell align="right">Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData?.userAnalytics.geographicDistribution.map((geo) => (
                    <TableRow key={geo.country}>
                      <TableCell component="th" scope="row">
                        {geo.country}
                      </TableCell>
                      <TableCell align="right">{formatNumber(geo.count)}</TableCell>
                      <TableCell align="right">
                        {((geo.count / dashboardData.userAnalytics.totalUsers) * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AdminDashboard;