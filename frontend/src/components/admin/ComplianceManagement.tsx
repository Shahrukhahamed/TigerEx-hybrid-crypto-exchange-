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
  Grid,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Alert,
  Pagination,
  IconButton,
  Tooltip,
  Badge,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent
} from '@mui/material';
import {
  Gavel as GavelIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  Timeline as TimelineIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Send as SendIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Flag as FlagIcon,
  Block as BlockIcon,
  Verified as VerifiedIcon,
  Schedule as ScheduleIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

interface ComplianceCase {
  id: string;
  user_id: string;
  case_type: string;
  status: string;
  priority: string;
  assigned_to: string;
  created_at: string;
  updated_at: string;
  due_date?: string;
  details: any;
  notes: string[];
  documents: string[];
  actions_taken: string[];
}

interface KYCReview {
  id: string;
  user_id: string;
  user_email: string;
  kyc_level: number;
  status: string;
  submitted_at: string;
  documents: Array<{
    type: string;
    url: string;
    status: string;
    notes?: string;
  }>;
  verification_notes: string;
  risk_assessment: {
    score: number;
    factors: string[];
  };
}

interface AMLAlert {
  id: string;
  user_id: string;
  alert_type: string;
  severity: string;
  description: string;
  transaction_id?: string;
  amount?: string;
  currency?: string;
  created_at: string;
  status: string;
  investigation_notes: string;
}

interface ComplianceReport {
  id: string;
  report_type: string;
  period: string;
  status: string;
  generated_at: string;
  file_url?: string;
  summary: {
    total_cases: number;
    resolved_cases: number;
    pending_cases: number;
    high_priority_cases: number;
  };
}

const ComplianceManagement: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [complianceCases, setComplianceCases] = useState<ComplianceCase[]>([]);
  const [kycReviews, setKycReviews] = useState<KYCReview[]>([]);
  const [amlAlerts, setAmlAlerts] = useState<AMLAlert[]>([]);
  const [complianceReports, setComplianceReports] = useState<ComplianceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Dialog states
  const [caseDialogOpen, setCaseDialogOpen] = useState(false);
  const [kycDialogOpen, setKycDialogOpen] = useState(false);
  const [amlDialogOpen, setAmlDialogOpen] = useState(false);
  const [selectedCase, setSelectedCase] = useState<ComplianceCase | null>(null);
  const [selectedKyc, setSelectedKyc] = useState<KYCReview | null>(null);
  const [selectedAml, setSelectedAml] = useState<AMLAlert | null>(null);
  
  // Form states
  const [newCaseType, setNewCaseType] = useState('');
  const [newCasePriority, setNewCasePriority] = useState('');
  const [newCaseUserId, setNewCaseUserId] = useState('');
  const [newCaseDetails, setNewCaseDetails] = useState('');
  const [caseNotes, setCaseNotes] = useState('');
  const [caseAction, setCaseAction] = useState('');

  useEffect(() => {
    loadComplianceData();
  }, [selectedTab, page]);

  const loadComplianceData = async () => {
    try {
      setLoading(true);
      
      if (selectedTab === 0) {
        // Load compliance cases
        const response = await fetch(`/api/v1/admin/compliance/cases?page=${page}&limit=20`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setComplianceCases(data.cases);
          setTotalPages(Math.ceil(data.total / 20));
        }
      } else if (selectedTab === 1) {
        // Load KYC reviews
        loadKycReviews();
      } else if (selectedTab === 2) {
        // Load AML alerts
        loadAmlAlerts();
      } else if (selectedTab === 3) {
        // Load compliance reports
        loadComplianceReports();
      }
    } catch (error) {
      console.error('Error loading compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadKycReviews = async () => {
    try {
      const response = await fetch('/api/v1/admin/kyc/reviews?status=PENDING', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setKycReviews(data.reviews);
      }
    } catch (error) {
      console.error('Error loading KYC reviews:', error);
    }
  };

  const loadAmlAlerts = async () => {
    try {
      const response = await fetch('/api/v1/admin/aml/alerts?status=OPEN', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAmlAlerts(data.alerts);
      }
    } catch (error) {
      console.error('Error loading AML alerts:', error);
    }
  };

  const loadComplianceReports = async () => {
    try {
      const response = await fetch('/api/v1/admin/compliance/reports', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setComplianceReports(data.reports);
      }
    } catch (error) {
      console.error('Error loading compliance reports:', error);
    }
  };

  const handleCreateCase = async () => {
    try {
      const response = await fetch('/api/v1/admin/compliance/cases', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          user_id: newCaseUserId,
          case_type: newCaseType,
          priority: newCasePriority,
          details: newCaseDetails
        })
      });

      if (response.ok) {
        setCaseDialogOpen(false);
        setNewCaseType('');
        setNewCasePriority('');
        setNewCaseUserId('');
        setNewCaseDetails('');
        loadComplianceData();
      }
    } catch (error) {
      console.error('Error creating compliance case:', error);
    }
  };

  const handleUpdateCaseStatus = async (caseId: string, newStatus: string) => {
    try {
      const response = await fetch(`/api/v1/admin/compliance/cases/${caseId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          status: newStatus,
          notes: caseNotes
        })
      });

      if (response.ok) {
        loadComplianceData();
      }
    } catch (error) {
      console.error('Error updating case status:', error);
    }
  };

  const handleKycDecision = async (reviewId: string, decision: string, notes: string) => {
    try {
      const response = await fetch(`/api/v1/admin/kyc/reviews/${reviewId}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          decision,
          notes
        })
      });

      if (response.ok) {
        setKycDialogOpen(false);
        loadKycReviews();
      }
    } catch (error) {
      console.error('Error making KYC decision:', error);
    }
  };

  const handleAmlInvestigation = async (alertId: string, action: string, notes: string) => {
    try {
      const response = await fetch(`/api/v1/admin/aml/alerts/${alertId}/investigate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          action,
          notes
        })
      });

      if (response.ok) {
        setAmlDialogOpen(false);
        loadAmlAlerts();
      }
    } catch (error) {
      console.error('Error investigating AML alert:', error);
    }
  };

  const generateComplianceReport = async (reportType: string, period: string) => {
    try {
      const response = await fetch('/api/v1/admin/compliance/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify({
          report_type: reportType,
          period
        })
      });

      if (response.ok) {
        loadComplianceReports();
      }
    } catch (error) {
      console.error('Error generating compliance report:', error);
    }
  };

  const getCaseStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN': return 'error';
      case 'IN_PROGRESS': return 'warning';
      case 'RESOLVED': return 'success';
      case 'CLOSED': return 'default';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH': return 'error';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'info';
      default: return 'default';
    }
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

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Compliance Management
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            startIcon={<AssignmentIcon />}
            onClick={() => setCaseDialogOpen(true)}
          >
            New Case
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => generateComplianceReport('MONTHLY', '2024-01')}
          >
            Generate Report
          </Button>
        </Box>
      </Box>

      {/* Main Content */}
      <Card>
        <CardContent>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab 
              label={
                <Badge badgeContent={complianceCases.filter(c => c.status === 'OPEN').length} color="error">
                  Compliance Cases
                </Badge>
              } 
            />
            <Tab 
              label={
                <Badge badgeContent={kycReviews.filter(k => k.status === 'PENDING').length} color="warning">
                  KYC Reviews
                </Badge>
              } 
            />
            <Tab 
              label={
                <Badge badgeContent={amlAlerts.filter(a => a.status === 'OPEN').length} color="error">
                  AML Alerts
                </Badge>
              } 
            />
            <Tab label="Reports" />
          </Tabs>

          {/* Compliance Cases Tab */}
          {selectedTab === 0 && (
            <Box sx={{ mt: 2 }}>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Case ID</TableCell>
                      <TableCell>User ID</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Priority</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Assigned To</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell>Due Date</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {complianceCases.map((case_) => (
                      <TableRow key={case_.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {case_.id.slice(0, 8)}...
                          </Typography>
                        </TableCell>
                        <TableCell>{case_.user_id}</TableCell>
                        <TableCell>
                          <Chip label={case_.case_type} size="small" />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={case_.priority}
                            color={getPriorityColor(case_.priority) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={case_.status}
                            color={getCaseStatusColor(case_.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{case_.assigned_to}</TableCell>
                        <TableCell>
                          {format(new Date(case_.created_at), 'MMM dd, yyyy')}
                        </TableCell>
                        <TableCell>
                          {case_.due_date ? (
                            <Typography
                              color={new Date(case_.due_date) < new Date() ? 'error' : 'textPrimary'}
                            >
                              {format(new Date(case_.due_date), 'MMM dd, yyyy')}
                            </Typography>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <Tooltip title="View Details">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedCase(case_);
                                  // Open case details dialog
                                }}
                              >
                                <VisibilityIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Edit">
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              <Box display="flex" justifyContent="center" mt={2}>
                <Pagination
                  count={totalPages}
                  page={page}
                  onChange={(e, newPage) => setPage(newPage)}
                  color="primary"
                />
              </Box>
            </Box>
          )}

          {/* KYC Reviews Tab */}
          {selectedTab === 1 && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                {kycReviews.map((review) => (
                  <Grid item xs={12} md={6} lg={4} key={review.id}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                          <Typography variant="h6">
                            KYC Level {review.kyc_level}
                          </Typography>
                          <Chip
                            label={review.status}
                            color={review.status === 'PENDING' ? 'warning' : 'default'}
                            size="small"
                          />
                        </Box>
                        
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          User: {review.user_email}
                        </Typography>
                        
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          Submitted: {format(new Date(review.submitted_at), 'MMM dd, yyyy')}
                        </Typography>
                        
                        <Box mt={2}>
                          <Typography variant="subtitle2" gutterBottom>
                            Documents:
                          </Typography>
                          {review.documents.map((doc, index) => (
                            <Chip
                              key={index}
                              label={doc.type}
                              size="small"
                              color={doc.status === 'VERIFIED' ? 'success' : 'default'}
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Box>
                        
                        <Box mt={2}>
                          <Typography variant="subtitle2" gutterBottom>
                            Risk Score: {(review.risk_assessment.score * 100).toFixed(0)}%
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={review.risk_assessment.score * 100}
                            color={review.risk_assessment.score > 0.7 ? 'error' : 'success'}
                          />
                        </Box>
                        
                        <Box display="flex" gap={1} mt={2}>
                          <Button
                            size="small"
                            variant="contained"
                            color="success"
                            onClick={() => {
                              setSelectedKyc(review);
                              setKycDialogOpen(true);
                            }}
                          >
                            Review
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => {
                              // View documents
                            }}
                          >
                            Documents
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* AML Alerts Tab */}
          {selectedTab === 2 && (
            <Box sx={{ mt: 2 }}>
              <List>
                {amlAlerts.map((alert) => (
                  <ListItem key={alert.id}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: getSeverityColor(alert.severity) + '.main' }}>
                        <FlagIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={2}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {alert.alert_type}
                          </Typography>
                          <Chip
                            label={alert.severity}
                            color={getSeverityColor(alert.severity) as any}
                            size="small"
                          />
                          <Chip
                            label={alert.status}
                            color={alert.status === 'OPEN' ? 'error' : 'success'}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            User: {alert.user_id}
                          </Typography>
                          <Typography variant="body2">
                            {alert.description}
                          </Typography>
                          {alert.amount && (
                            <Typography variant="body2">
                              Amount: {alert.amount} {alert.currency}
                            </Typography>
                          )}
                          <Typography variant="body2" color="textSecondary">
                            {format(new Date(alert.created_at), 'MMM dd, yyyy HH:mm')}
                          </Typography>
                        </Box>
                      }
                    />
                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        variant="contained"
                        color="warning"
                        onClick={() => {
                          setSelectedAml(alert);
                          setAmlDialogOpen(true);
                        }}
                      >
                        Investigate
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          // View transaction details
                        }}
                      >
                        Details
                      </Button>
                    </Box>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Reports Tab */}
          {selectedTab === 3 && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <Typography variant="h6" gutterBottom>
                    Compliance Reports
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Report Type</TableCell>
                          <TableCell>Period</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Generated</TableCell>
                          <TableCell>Summary</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {complianceReports.map((report) => (
                          <TableRow key={report.id}>
                            <TableCell>{report.report_type}</TableCell>
                            <TableCell>{report.period}</TableCell>
                            <TableCell>
                              <Chip
                                label={report.status}
                                color={report.status === 'COMPLETED' ? 'success' : 'warning'}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>
                              {format(new Date(report.generated_at), 'MMM dd, yyyy')}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                Total: {report.summary.total_cases} | 
                                Resolved: {report.summary.resolved_cases} | 
                                Pending: {report.summary.pending_cases}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              {report.file_url && (
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<DownloadIcon />}
                                  href={report.file_url}
                                  target="_blank"
                                >
                                  Download
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Generate New Report
                      </Typography>
                      <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Report Type</InputLabel>
                        <Select label="Report Type">
                          <MenuItem value="MONTHLY_COMPLIANCE">Monthly Compliance</MenuItem>
                          <MenuItem value="KYC_SUMMARY">KYC Summary</MenuItem>
                          <MenuItem value="AML_ALERTS">AML Alerts</MenuItem>
                          <MenuItem value="REGULATORY_FILING">Regulatory Filing</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Period</InputLabel>
                        <Select label="Period">
                          <MenuItem value="2024-01">January 2024</MenuItem>
                          <MenuItem value="2024-02">February 2024</MenuItem>
                          <MenuItem value="2024-03">March 2024</MenuItem>
                          <MenuItem value="Q1-2024">Q1 2024</MenuItem>
                        </Select>
                      </FormControl>
                      <Button
                        fullWidth
                        variant="contained"
                        onClick={() => generateComplianceReport('MONTHLY_COMPLIANCE', '2024-01')}
                      >
                        Generate Report
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Create Case Dialog */}
      <Dialog open={caseDialogOpen} onClose={() => setCaseDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Compliance Case</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="User ID"
            value={newCaseUserId}
            onChange={(e) => setNewCaseUserId(e.target.value)}
            sx={{ mt: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Case Type</InputLabel>
            <Select
              value={newCaseType}
              onChange={(e) => setNewCaseType(e.target.value)}
              label="Case Type"
            >
              <MenuItem value="KYC_REVIEW">KYC Review</MenuItem>
              <MenuItem value="AML_INVESTIGATION">AML Investigation</MenuItem>
              <MenuItem value="SUSPICIOUS_ACTIVITY">Suspicious Activity</MenuItem>
              <MenuItem value="REGULATORY_INQUIRY">Regulatory Inquiry</MenuItem>
              <MenuItem value="USER_COMPLAINT">User Complaint</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={newCasePriority}
              onChange={(e) => setNewCasePriority(e.target.value)}
              label="Priority"
            >
              <MenuItem value="LOW">Low</MenuItem>
              <MenuItem value="MEDIUM">Medium</MenuItem>
              <MenuItem value="HIGH">High</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Case Details"
            value={newCaseDetails}
            onChange={(e) => setNewCaseDetails(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCaseDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateCase} variant="contained">
            Create Case
          </Button>
        </DialogActions>
      </Dialog>

      {/* KYC Review Dialog */}
      <Dialog open={kycDialogOpen} onClose={() => setKycDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>KYC Review: {selectedKyc?.user_email}</DialogTitle>
        <DialogContent>
          {selectedKyc && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Documents Review
              </Typography>
              <Grid container spacing={2}>
                {selectedKyc.documents.map((doc, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle1">{doc.type}</Typography>
                        <Typography variant="body2" color="textSecondary">
                          Status: {doc.status}
                        </Typography>
                        {doc.notes && (
                          <Typography variant="body2">
                            Notes: {doc.notes}
                          </Typography>
                        )}
                        <Button
                          size="small"
                          variant="outlined"
                          sx={{ mt: 1 }}
                          href={doc.url}
                          target="_blank"
                        >
                          View Document
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              
              <Box mt={3}>
                <Typography variant="h6" gutterBottom>
                  Risk Assessment
                </Typography>
                <Typography variant="body2">
                  Risk Score: {(selectedKyc.risk_assessment.score * 100).toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={selectedKyc.risk_assessment.score * 100}
                  color={selectedKyc.risk_assessment.score > 0.7 ? 'error' : 'success'}
                  sx={{ mt: 1, mb: 2 }}
                />
                <Typography variant="body2">
                  Risk Factors: {selectedKyc.risk_assessment.factors.join(', ')}
                </Typography>
              </Box>
              
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Review Notes"
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setKycDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => handleKycDecision(selectedKyc?.id || '', 'REJECTED', '')}
            color="error"
          >
            Reject
          </Button>
          <Button
            onClick={() => handleKycDecision(selectedKyc?.id || '', 'APPROVED', '')}
            variant="contained"
            color="success"
          >
            Approve
          </Button>
        </DialogActions>
      </Dialog>

      {/* AML Investigation Dialog */}
      <Dialog open={amlDialogOpen} onClose={() => setAmlDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>AML Investigation: {selectedAml?.alert_type}</DialogTitle>
        <DialogContent>
          {selectedAml && (
            <Box>
              <Typography variant="body1" gutterBottom>
                {selectedAml.description}
              </Typography>
              
              {selectedAml.amount && (
                <Typography variant="body2" gutterBottom>
                  Amount: {selectedAml.amount} {selectedAml.currency}
                </Typography>
              )}
              
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Investigation Notes"
                sx={{ mt: 2 }}
              />
              
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Action</InputLabel>
                <Select label="Action">
                  <MenuItem value="CLEAR">Clear Alert</MenuItem>
                  <MenuItem value="ESCALATE">Escalate</MenuItem>
                  <MenuItem value="FREEZE_ACCOUNT">Freeze Account</MenuItem>
                  <MenuItem value="REQUEST_DOCUMENTS">Request Documents</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAmlDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => handleAmlInvestigation(selectedAml?.id || '', 'CLEAR', '')}
            variant="contained"
          >
            Submit Investigation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ComplianceManagement;