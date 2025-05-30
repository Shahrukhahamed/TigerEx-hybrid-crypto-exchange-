import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
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
  Avatar,
  Grid,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Alert,
  Pagination,
  InputAdornment,
  Menu,
  ListItemIcon,
  Checkbox,
  FormControlLabel,
  Switch,
  Badge,
  LinearProgress
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Person as PersonIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  AccountBalance as AccountBalanceIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Verified as VerifiedIcon,
  Cancel as CancelIcon,
  History as HistoryIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

interface User {
  user_id: string;
  email: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  country?: string;
  kyc_status: string;
  kyc_level: number;
  user_status: string;
  trading_status: string;
  vip_level: number;
  referral_code: string;
  referred_by?: string;
  created_at: string;
  last_login?: string;
  total_trading_volume: string;
  total_fees_paid: string;
  risk_score: number;
}

interface UserBalance {
  asset: string;
  free: string;
  locked: string;
  total: string;
}

interface UserTrade {
  trade_id: string;
  symbol: string;
  side: string;
  quantity: string;
  price: string;
  commission: string;
  timestamp: string;
}

interface UserOrder {
  order_id: string;
  symbol: string;
  type: string;
  side: string;
  quantity: string;
  price: string;
  status: string;
  created_time: string;
}

interface ComplianceCase {
  id: string;
  case_type: string;
  status: string;
  assigned_to: string;
  details: any;
  created_at: string;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [kycFilter, setKycFilter] = useState('');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userDetailsOpen, setUserDetailsOpen] = useState(false);
  const [userBalances, setUserBalances] = useState<UserBalance[]>([]);
  const [userTrades, setUserTrades] = useState<UserTrade[]>([]);
  const [userOrders, setUserOrders] = useState<UserOrder[]>([]);
  const [complianceCases, setComplianceCases] = useState<ComplianceCase[]>([]);
  const [detailsTab, setDetailsTab] = useState(0);
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [actionMenuUser, setActionMenuUser] = useState<User | null>(null);
  const [statusUpdateOpen, setStatusUpdateOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusReason, setStatusReason] = useState('');
  const [bulkActionOpen, setBulkActionOpen] = useState(false);
  const [bulkAction, setBulkAction] = useState('');
  const [bulkReason, setBulkReason] = useState('');

  useEffect(() => {
    loadUsers();
  }, [page, searchTerm, statusFilter, kycFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20'
      });

      if (searchTerm) params.append('search', searchTerm);
      if (statusFilter) params.append('status', statusFilter);
      if (kycFilter) params.append('kyc_status', kycFilter);

      const response = await fetch(`/api/v1/admin/users?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
        setTotalPages(data.total_pages);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserDetails = async (userId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserBalances(data.balances);
        setUserTrades(data.recent_trades);
        setUserOrders(data.open_orders);
        setComplianceCases(data.compliance_cases);
      }
    } catch (error) {
      console.error('Error loading user details:', error);
    }
  };

  const handleUserClick = (user: User) => {
    setSelectedUser(user);
    setUserDetailsOpen(true);
    loadUserDetails(user.user_id);
  };

  const handleActionMenuOpen = (event: React.MouseEvent<HTMLElement>, user: User) => {
    setActionMenuAnchor(event.currentTarget);
    setActionMenuUser(user);
  };

  const handleActionMenuClose = () => {
    setActionMenuAnchor(null);
    setActionMenuUser(null);
  };

  const handleStatusUpdate = async () => {
    if (!actionMenuUser) return;

    try {
      const response = await fetch(`/api/v1/admin/users/${actionMenuUser.user_id}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          user_id: actionMenuUser.user_id,
          status: newStatus,
          reason: statusReason
        })
      });

      if (response.ok) {
        setStatusUpdateOpen(false);
        setNewStatus('');
        setStatusReason('');
        loadUsers();
      }
    } catch (error) {
      console.error('Error updating user status:', error);
    }
  };

  const handleBulkAction = async () => {
    if (selectedUsers.length === 0) return;

    try {
      const response = await fetch('/api/v1/admin/users/bulk-action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          user_ids: selectedUsers,
          action: bulkAction,
          reason: bulkReason
        })
      });

      if (response.ok) {
        setBulkActionOpen(false);
        setBulkAction('');
        setBulkReason('');
        setSelectedUsers([]);
        loadUsers();
      }
    } catch (error) {
      console.error('Error performing bulk action:', error);
    }
  };

  const handleUserSelection = (userId: string) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    if (selectedUsers.length === users.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users.map(user => user.user_id));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'SUSPENDED': return 'warning';
      case 'BANNED': return 'error';
      case 'PENDING_VERIFICATION': return 'info';
      case 'LOCKED': return 'error';
      default: return 'default';
    }
  };

  const getKycStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'success';
      case 'PENDING': return 'warning';
      case 'UNDER_REVIEW': return 'info';
      case 'REJECTED': return 'error';
      case 'EXPIRED': return 'error';
      default: return 'default';
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score >= 0.8) return 'error';
    if (score >= 0.6) return 'warning';
    if (score >= 0.4) return 'info';
    return 'success';
  };

  const formatCurrency = (amount: string) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          User Management
        </Typography>
        <Box display="flex" gap={2}>
          {selectedUsers.length > 0 && (
            <Button
              variant="contained"
              color="warning"
              onClick={() => setBulkActionOpen(true)}
            >
              Bulk Actions ({selectedUsers.length})
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadUsers}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="ACTIVE">Active</MenuItem>
                  <MenuItem value="SUSPENDED">Suspended</MenuItem>
                  <MenuItem value="BANNED">Banned</MenuItem>
                  <MenuItem value="PENDING_VERIFICATION">Pending Verification</MenuItem>
                  <MenuItem value="LOCKED">Locked</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>KYC Status</InputLabel>
                <Select
                  value={kycFilter}
                  onChange={(e) => setKycFilter(e.target.value)}
                  label="KYC Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="APPROVED">Approved</MenuItem>
                  <MenuItem value="PENDING">Pending</MenuItem>
                  <MenuItem value="UNDER_REVIEW">Under Review</MenuItem>
                  <MenuItem value="REJECTED">Rejected</MenuItem>
                  <MenuItem value="NOT_SUBMITTED">Not Submitted</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectedUsers.length === users.length && users.length > 0}
                    indeterminate={selectedUsers.length > 0 && selectedUsers.length < users.length}
                    onChange={handleSelectAll}
                  />
                }
                label="Select All"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedUsers.length === users.length && users.length > 0}
                    indeterminate={selectedUsers.length > 0 && selectedUsers.length < users.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell>User</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>KYC</TableCell>
                <TableCell>VIP Level</TableCell>
                <TableCell>Trading Volume</TableCell>
                <TableCell>Risk Score</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.user_id} hover>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedUsers.includes(user.user_id)}
                      onChange={() => handleUserSelection(user.user_id)}
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Avatar>
                        <PersonIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {user.first_name && user.last_name 
                            ? `${user.first_name} ${user.last_name}`
                            : user.email
                          }
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {user.email}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          ID: {user.user_id}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.user_status}
                      color={getStatusColor(user.user_status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={user.kyc_status}
                        color={getKycStatusColor(user.kyc_status) as any}
                        size="small"
                      />
                      <Typography variant="caption">
                        L{user.kyc_level}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Badge badgeContent={user.vip_level} color="primary">
                      <Chip label="VIP" size="small" />
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {formatCurrency(user.total_trading_volume)}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={user.risk_score * 100}
                        color={getRiskScoreColor(user.risk_score) as any}
                        sx={{ width: 60, height: 6 }}
                      />
                      <Typography variant="caption">
                        {(user.risk_score * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {user.last_login 
                      ? format(new Date(user.last_login), 'MMM dd, yyyy')
                      : 'Never'
                    }
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => handleUserClick(user)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <IconButton
                        size="small"
                        onClick={(e) => handleActionMenuOpen(e, user)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Pagination */}
        <Box display="flex" justifyContent="center" p={2}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(e, newPage) => setPage(newPage)}
            color="primary"
          />
        </Box>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={handleActionMenuClose}
      >
        <MenuItem onClick={() => {
          setStatusUpdateOpen(true);
          handleActionMenuClose();
        }}>
          <ListItemIcon>
            <EditIcon />
          </ListItemIcon>
          Update Status
        </MenuItem>
        <MenuItem onClick={() => {
          // Handle KYC review
          handleActionMenuClose();
        }}>
          <ListItemIcon>
            <VerifiedIcon />
          </ListItemIcon>
          Review KYC
        </MenuItem>
        <MenuItem onClick={() => {
          // Handle send notification
          handleActionMenuClose();
        }}>
          <ListItemIcon>
            <SendIcon />
          </ListItemIcon>
          Send Notification
        </MenuItem>
        <MenuItem onClick={() => {
          // Handle view audit log
          handleActionMenuClose();
        }}>
          <ListItemIcon>
            <HistoryIcon />
          </ListItemIcon>
          View Audit Log
        </MenuItem>
      </Menu>

      {/* User Details Dialog */}
      <Dialog
        open={userDetailsOpen}
        onClose={() => setUserDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="between" alignItems="center">
            <Typography variant="h6">
              User Details: {selectedUser?.email}
            </Typography>
            <Button onClick={() => setUserDetailsOpen(false)}>
              Close
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Tabs value={detailsTab} onChange={(e, newValue) => setDetailsTab(newValue)}>
            <Tab label="Profile" />
            <Tab label="Balances" />
            <Tab label="Trading History" />
            <Tab label="Open Orders" />
            <Tab label="Compliance" />
          </Tabs>

          {detailsTab === 0 && selectedUser && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Personal Information</Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Full Name"
                        secondary={`${selectedUser.first_name || ''} ${selectedUser.last_name || ''}`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Email"
                        secondary={selectedUser.email}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Phone"
                        secondary={selectedUser.phone || 'Not provided'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Country"
                        secondary={selectedUser.country || 'Not provided'}
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Account Information</Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="User Status"
                        secondary={
                          <Chip
                            label={selectedUser.user_status}
                            color={getStatusColor(selectedUser.user_status) as any}
                            size="small"
                          />
                        }
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="KYC Status"
                        secondary={
                          <Chip
                            label={selectedUser.kyc_status}
                            color={getKycStatusColor(selectedUser.kyc_status) as any}
                            size="small"
                          />
                        }
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="VIP Level"
                        secondary={selectedUser.vip_level}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Risk Score"
                        secondary={`${(selectedUser.risk_score * 100).toFixed(1)}%`}
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            </Box>
          )}

          {detailsTab === 1 && (
            <TableContainer sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Asset</TableCell>
                    <TableCell align="right">Free</TableCell>
                    <TableCell align="right">Locked</TableCell>
                    <TableCell align="right">Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {userBalances.map((balance) => (
                    <TableRow key={balance.asset}>
                      <TableCell>{balance.asset}</TableCell>
                      <TableCell align="right">{balance.free}</TableCell>
                      <TableCell align="right">{balance.locked}</TableCell>
                      <TableCell align="right">{balance.total}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {detailsTab === 2 && (
            <TableContainer sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Trade ID</TableCell>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">Commission</TableCell>
                    <TableCell>Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {userTrades.map((trade) => (
                    <TableRow key={trade.trade_id}>
                      <TableCell>{trade.trade_id}</TableCell>
                      <TableCell>{trade.symbol}</TableCell>
                      <TableCell>
                        <Chip
                          label={trade.side}
                          color={trade.side === 'BUY' ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">{trade.quantity}</TableCell>
                      <TableCell align="right">{trade.price}</TableCell>
                      <TableCell align="right">{trade.commission}</TableCell>
                      <TableCell>
                        {format(new Date(trade.timestamp), 'MMM dd, yyyy HH:mm')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {detailsTab === 3 && (
            <TableContainer sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Order ID</TableCell>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {userOrders.map((order) => (
                    <TableRow key={order.order_id}>
                      <TableCell>{order.order_id}</TableCell>
                      <TableCell>{order.symbol}</TableCell>
                      <TableCell>{order.type}</TableCell>
                      <TableCell>
                        <Chip
                          label={order.side}
                          color={order.side === 'BUY' ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">{order.quantity}</TableCell>
                      <TableCell align="right">{order.price}</TableCell>
                      <TableCell>
                        <Chip label={order.status} size="small" />
                      </TableCell>
                      <TableCell>
                        {format(new Date(order.created_time), 'MMM dd, yyyy HH:mm')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {detailsTab === 4 && (
            <Box sx={{ mt: 2 }}>
              {complianceCases.length > 0 ? (
                <List>
                  {complianceCases.map((case_) => (
                    <ListItem key={case_.id}>
                      <ListItemText
                        primary={case_.case_type}
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              Status: {case_.status}
                            </Typography>
                            <Typography variant="body2">
                              Created: {format(new Date(case_.created_at), 'MMM dd, yyyy')}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Alert severity="info">No compliance cases found</Alert>
              )}
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* Status Update Dialog */}
      <Dialog open={statusUpdateOpen} onClose={() => setStatusUpdateOpen(false)}>
        <DialogTitle>Update User Status</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>New Status</InputLabel>
            <Select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              label="New Status"
            >
              <MenuItem value="ACTIVE">Active</MenuItem>
              <MenuItem value="SUSPENDED">Suspended</MenuItem>
              <MenuItem value="BANNED">Banned</MenuItem>
              <MenuItem value="LOCKED">Locked</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason"
            value={statusReason}
            onChange={(e) => setStatusReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusUpdateOpen(false)}>Cancel</Button>
          <Button onClick={handleStatusUpdate} variant="contained">
            Update Status
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Action Dialog */}
      <Dialog open={bulkActionOpen} onClose={() => setBulkActionOpen(false)}>
        <DialogTitle>Bulk Action ({selectedUsers.length} users)</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Action</InputLabel>
            <Select
              value={bulkAction}
              onChange={(e) => setBulkAction(e.target.value)}
              label="Action"
            >
              <MenuItem value="SUSPEND">Suspend Users</MenuItem>
              <MenuItem value="ACTIVATE">Activate Users</MenuItem>
              <MenuItem value="SEND_NOTIFICATION">Send Notification</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason"
            value={bulkReason}
            onChange={(e) => setBulkReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkActionOpen(false)}>Cancel</Button>
          <Button onClick={handleBulkAction} variant="contained" color="warning">
            Execute Action
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;