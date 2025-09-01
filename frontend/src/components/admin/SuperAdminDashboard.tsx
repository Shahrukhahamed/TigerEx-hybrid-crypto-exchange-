'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import {
  Users,
  TrendingUp,
  Shield,
  Settings,
  AlertTriangle,
  DollarSign,
  Activity,
  Globe,
  Zap,
  Database,
  Server,
  Lock,
  UserCheck,
  FileText,
  BarChart3,
  PieChart,
  Wallet,
  Coins,
  Building,
  Network,
  Bot,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  ArrowUp,
  ArrowDown,
  Plus,
  Edit,
  Trash2,
  Download,
  Upload,
  Search,
  Filter,
  RefreshCw,
  Bell,
  MessageSquare,
  Calendar,
  MapPin,
  Phone,
  Mail,
  ExternalLink
} from 'lucide-react'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

interface AdminUser {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  role: string
  is_active: boolean
  last_login_at: string
  created_at: string
}

interface KYCApplication {
  id: number
  user_id: number
  status: string
  tier_requested: number
  first_name: string
  last_name: string
  country_of_residence: string
  created_at: string
}

interface TokenListing {
  id: number
  token_name: string
  token_symbol: string
  blockchain: string
  status: string
  applicant_name: string
  created_at: string
}

interface WhiteLabelExchange {
  id: number
  exchange_name: string
  domain_name: string
  status: string
  client_id: number
  features_enabled: string[]
  created_at: string
}

interface SystemStats {
  total_admin_users: number
  active_admin_users: number
  pending_kyc_applications: number
  pending_token_listings: number
  active_white_label_exchanges: number
  integrated_blockchains: number
}

export function SuperAdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null)
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([])
  const [kycApplications, setKycApplications] = useState<KYCApplication[]>([])
  const [tokenListings, setTokenListings] = useState<TokenListing[]>([])
  const [whiteLabelExchanges, setWhiteLabelExchanges] = useState<WhiteLabelExchange[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFilter, setSelectedFilter] = useState('all')

  // Mock data for demonstration
  useEffect(() => {
    // Simulate API calls
    setTimeout(() => {
      setSystemStats({
        total_admin_users: 25,
        active_admin_users: 23,
        pending_kyc_applications: 156,
        pending_token_listings: 12,
        active_white_label_exchanges: 8,
        integrated_blockchains: 15
      })

      setAdminUsers([
        {
          id: 1,
          email: 'super@tigerex.com',
          username: 'superadmin',
          first_name: 'Super',
          last_name: 'Admin',
          role: 'Super Administrator',
          is_active: true,
          last_login_at: '2024-01-15T10:30:00Z',
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 2,
          email: 'kyc@tigerex.com',
          username: 'kycadmin',
          first_name: 'KYC',
          last_name: 'Manager',
          role: 'KYC Administrator',
          is_active: true,
          last_login_at: '2024-01-15T09:15:00Z',
          created_at: '2024-01-02T00:00:00Z'
        }
      ])

      setKycApplications([
        {
          id: 1,
          user_id: 1001,
          status: 'pending',
          tier_requested: 2,
          first_name: 'John',
          last_name: 'Doe',
          country_of_residence: 'United States',
          created_at: '2024-01-15T08:00:00Z'
        }
      ])

      setTokenListings([
        {
          id: 1,
          token_name: 'DeFi Token',
          token_symbol: 'DEFI',
          blockchain: 'ethereum',
          status: 'submitted',
          applicant_name: 'DeFi Protocol Inc.',
          created_at: '2024-01-14T12:00:00Z'
        }
      ])

      setWhiteLabelExchanges([
        {
          id: 1,
          exchange_name: 'CryptoTrade Pro',
          domain_name: 'cryptotradepro.com',
          status: 'active',
          client_id: 2001,
          features_enabled: ['spot_trading', 'futures_trading', 'staking'],
          created_at: '2024-01-10T00:00:00Z'
        }
      ])

      setLoading(false)
    }, 1000)
  }, [])

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'users', label: 'Admin Users', icon: Users },
    { id: 'kyc', label: 'KYC Management', icon: UserCheck },
    { id: 'tokens', label: 'Token Listings', icon: Coins },
    { id: 'whitelabel', label: 'White Label', icon: Building },
    { id: 'blockchain', label: 'Blockchain', icon: Network },
    { id: 'ai', label: 'AI Maintenance', icon: Bot },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'settings', label: 'Settings', icon: Settings }
  ]

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Admin Users"
          value={systemStats?.total_admin_users || 0}
          change="+2"
          changeType="positive"
          icon={Users}
          color="blue"
        />
        <StatsCard
          title="Pending KYC"
          value={systemStats?.pending_kyc_applications || 0}
          change="+15"
          changeType="neutral"
          icon={UserCheck}
          color="yellow"
        />
        <StatsCard
          title="Token Listings"
          value={systemStats?.pending_token_listings || 0}
          change="+3"
          changeType="positive"
          icon={Coins}
          color="green"
        />
        <StatsCard
          title="White Label Exchanges"
          value={systemStats?.active_white_label_exchanges || 0}
          change="+1"
          changeType="positive"
          icon={Building}
          color="purple"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="User Growth" type="line" />
        <ChartCard title="Trading Volume" type="bar" />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivityCard />
        <SystemHealthCard />
      </div>
    </div>
  )

  const renderAdminUsers = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Admin Users Management</h2>
        <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Admin User
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex gap-4 mb-6">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search admin users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg"
            />
          </div>
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            <option value="all">All Roles</option>
            <option value="super_admin">Super Admin</option>
            <option value="kyc_admin">KYC Admin</option>
            <option value="support_admin">Support Admin</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-white">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3">User</th>
                <th className="text-left py-3">Role</th>
                <th className="text-left py-3">Status</th>
                <th className="text-left py-3">Last Login</th>
                <th className="text-left py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {adminUsers.map((user) => (
                <tr key={user.id} className="border-b border-gray-700">
                  <td className="py-3">
                    <div>
                      <div className="font-medium">{user.first_name} {user.last_name}</div>
                      <div className="text-gray-400 text-sm">{user.email}</div>
                    </div>
                  </td>
                  <td className="py-3">
                    <span className="bg-blue-500 text-white px-2 py-1 rounded text-sm">
                      {user.role}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-sm ${
                      user.is_active ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="py-3 text-gray-400">
                    {new Date(user.last_login_at).toLocaleDateString()}
                  </td>
                  <td className="py-3">
                    <div className="flex gap-2">
                      <button className="text-blue-400 hover:text-blue-300">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="text-red-400 hover:text-red-300">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )

  const renderKYCManagement = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">KYC Applications Management</h2>
        <div className="flex gap-2">
          <button className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg">
            Bulk Approve
          </button>
          <button className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg">
            Bulk Reject
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-yellow-400 text-2xl font-bold">156</div>
          <div className="text-gray-400">Pending Review</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-green-400 text-2xl font-bold">1,234</div>
          <div className="text-gray-400">Approved</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-red-400 text-2xl font-bold">89</div>
          <div className="text-gray-400">Rejected</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-blue-400 text-2xl font-bold">23</div>
          <div className="text-gray-400">Under Review</div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-white">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3">Applicant</th>
                <th className="text-left py-3">Tier</th>
                <th className="text-left py-3">Country</th>
                <th className="text-left py-3">Status</th>
                <th className="text-left py-3">Submitted</th>
                <th className="text-left py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {kycApplications.map((application) => (
                <tr key={application.id} className="border-b border-gray-700">
                  <td className="py-3">
                    <div className="font-medium">{application.first_name} {application.last_name}</div>
                    <div className="text-gray-400 text-sm">ID: {application.user_id}</div>
                  </td>
                  <td className="py-3">
                    <span className="bg-blue-500 text-white px-2 py-1 rounded text-sm">
                      Tier {application.tier_requested}
                    </span>
                  </td>
                  <td className="py-3">{application.country_of_residence}</td>
                  <td className="py-3">
                    <span className="bg-yellow-500 text-white px-2 py-1 rounded text-sm">
                      {application.status}
                    </span>
                  </td>
                  <td className="py-3 text-gray-400">
                    {new Date(application.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3">
                    <div className="flex gap-2">
                      <button className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">
                        Approve
                      </button>
                      <button className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm">
                        Reject
                      </button>
                      <button className="text-blue-400 hover:text-blue-300">
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )

  const renderTokenListings = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Token Listing Management</h2>
        <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Manual Token Listing
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-white">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3">Token</th>
                <th className="text-left py-3">Blockchain</th>
                <th className="text-left py-3">Applicant</th>
                <th className="text-left py-3">Status</th>
                <th className="text-left py-3">Submitted</th>
                <th className="text-left py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tokenListings.map((listing) => (
                <tr key={listing.id} className="border-b border-gray-700">
                  <td className="py-3">
                    <div className="font-medium">{listing.token_name}</div>
                    <div className="text-gray-400 text-sm">{listing.token_symbol}</div>
                  </td>
                  <td className="py-3">
                    <span className="bg-purple-500 text-white px-2 py-1 rounded text-sm">
                      {listing.blockchain}
                    </span>
                  </td>
                  <td className="py-3">{listing.applicant_name}</td>
                  <td className="py-3">
                    <span className="bg-yellow-500 text-white px-2 py-1 rounded text-sm">
                      {listing.status}
                    </span>
                  </td>
                  <td className="py-3 text-gray-400">
                    {new Date(listing.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3">
                    <div className="flex gap-2">
                      <button className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">
                        Approve
                      </button>
                      <button className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm">
                        Reject
                      </button>
                      <button className="text-blue-400 hover:text-blue-300">
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )

  const renderWhiteLabel = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">White Label Exchange Management</h2>
        <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Create White Label Exchange
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {whiteLabelExchanges.map((exchange) => (
          <div key={exchange.id} className="bg-gray-800 rounded-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{exchange.exchange_name}</h3>
                <p className="text-gray-400 text-sm">{exchange.domain_name}</p>
              </div>
              <span className={`px-2 py-1 rounded text-sm ${
                exchange.status === 'active' ? 'bg-green-500 text-white' : 'bg-yellow-500 text-white'
              }`}>
                {exchange.status}
              </span>
            </div>
            
            <div className="space-y-2 mb-4">
              <div className="text-sm text-gray-400">Features Enabled:</div>
              <div className="flex flex-wrap gap-1">
                {exchange.features_enabled.map((feature) => (
                  <span key={feature} className="bg-blue-500 text-white px-2 py-1 rounded text-xs">
                    {feature.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 rounded text-sm">
                Configure
              </button>
              <button className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded text-sm">
                View
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  const renderBlockchain = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Blockchain Integration Management</h2>
        <div className="flex gap-2">
          <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Custom Blockchain
          </button>
          <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
            <Network className="w-4 h-4" />
            Deploy Block Explorer
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <BlockchainCard
          name="Ethereum"
          type="EVM"
          status="active"
          chainId={1}
          rpcUrl="https://mainnet.infura.io/v3/..."
          explorerUrl="https://etherscan.io"
        />
        <BlockchainCard
          name="Binance Smart Chain"
          type="EVM"
          status="active"
          chainId={56}
          rpcUrl="https://bsc-dataseed.binance.org/"
          explorerUrl="https://bscscan.com"
        />
        <BlockchainCard
          name="Polygon"
          type="EVM"
          status="active"
          chainId={137}
          rpcUrl="https://polygon-rpc.com/"
          explorerUrl="https://polygonscan.com"
        />
      </div>
    </div>
  )

  const renderAIMaintenance = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">AI-Based Maintenance System</h2>
        <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Bot className="w-4 h-4" />
          Run AI Analysis
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <AITaskCard
          title="Performance Optimization"
          status="running"
          progress={75}
          lastRun="2 hours ago"
          recommendations={3}
        />
        <AITaskCard
          title="Security Scan"
          status="completed"
          progress={100}
          lastRun="1 hour ago"
          recommendations={1}
        />
        <AITaskCard
          title="Database Optimization"
          status="pending"
          progress={0}
          lastRun="6 hours ago"
          recommendations={0}
        />
        <AITaskCard
          title="Load Balancing"
          status="running"
          progress={45}
          lastRun="30 minutes ago"
          recommendations={2}
        />
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">AI Recommendations</h3>
        <div className="space-y-4">
          <AIRecommendation
            type="performance"
            title="Optimize Database Queries"
            description="AI detected slow queries in the trading engine. Recommend adding indexes to improve performance by 40%."
            priority="high"
            estimatedImpact="40% performance improvement"
          />
          <AIRecommendation
            type="security"
            title="Update Security Protocols"
            description="New security vulnerability detected. Recommend updating authentication middleware."
            priority="critical"
            estimatedImpact="Enhanced security"
          />
        </div>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading Super Admin Dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">TigerEx Super Admin</h1>
              <p className="text-gray-400 text-sm">Comprehensive Exchange Management</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-gray-400 hover:text-white">
              <Bell className="w-5 h-5" />
            </button>
            <button className="text-gray-400 hover:text-white">
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">SA</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-800 min-h-screen border-r border-gray-700">
          <nav className="p-4">
            <div className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-orange-500 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                </button>
              ))}
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'users' && renderAdminUsers()}
          {activeTab === 'kyc' && renderKYCManagement()}
          {activeTab === 'tokens' && renderTokenListings()}
          {activeTab === 'whitelabel' && renderWhiteLabel()}
          {activeTab === 'blockchain' && renderBlockchain()}
          {activeTab === 'ai' && renderAIMaintenance()}
        </main>
      </div>
    </div>
  )
}

// Helper Components
function StatsCard({ title, value, change, changeType, icon: Icon, color }: any) {
  const colorClasses = {
    blue: 'bg-blue-500',
    yellow: 'bg-yellow-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    red: 'bg-red-500'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          <div className="flex items-center gap-1 mt-1">
            {changeType === 'positive' ? (
              <ArrowUp className="w-4 h-4 text-green-400" />
            ) : changeType === 'negative' ? (
              <ArrowDown className="w-4 h-4 text-red-400" />
            ) : null}
            <span className={`text-sm ${
              changeType === 'positive' ? 'text-green-400' : 
              changeType === 'negative' ? 'text-red-400' : 'text-gray-400'
            }`}>
              {change}
            </span>
          </div>
        </div>
        <div className={`w-12 h-12 ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  )
}

function ChartCard({ title, type }: { title: string; type: 'line' | 'bar' }) {
  const data = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: title,
        data: [12, 19, 3, 5, 2, 3],
        borderColor: 'rgb(249, 115, 22)',
        backgroundColor: 'rgba(249, 115, 22, 0.2)',
      },
    ],
  }

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'white'
        }
      },
      title: {
        display: true,
        text: title,
        color: 'white'
      },
    },
    scales: {
      x: {
        ticks: {
          color: 'white'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      y: {
        ticks: {
          color: 'white'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {type === 'line' ? (
        <Line data={data} options={options} />
      ) : (
        <Bar data={data} options={options} />
      )}
    </div>
  )
}

function RecentActivityCard() {
  const activities = [
    { id: 1, action: 'KYC Application Approved', user: 'John Doe', time: '2 minutes ago' },
    { id: 2, action: 'Token Listing Submitted', user: 'DeFi Protocol', time: '5 minutes ago' },
    { id: 3, action: 'White Label Exchange Created', user: 'CryptoTrade Pro', time: '10 minutes ago' },
  ]

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
      <div className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-center gap-3">
            <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
            <div className="flex-1">
              <p className="text-white text-sm">{activity.action}</p>
              <p className="text-gray-400 text-xs">{activity.user} • {activity.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function SystemHealthCard() {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-400">API Response Time</span>
          <span className="text-green-400">5ms</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Database Performance</span>
          <span className="text-green-400">Excellent</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Server Uptime</span>
          <span className="text-green-400">99.99%</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Active Connections</span>
          <span className="text-blue-400">1,234</span>
        </div>
      </div>
    </div>
  )
}

function BlockchainCard({ name, type, status, chainId, rpcUrl, explorerUrl }: any) {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{name}</h3>
          <p className="text-gray-400 text-sm">Chain ID: {chainId}</p>
        </div>
        <span className={`px-2 py-1 rounded text-sm ${
          status === 'active' ? 'bg-green-500 text-white' : 'bg-yellow-500 text-white'
        }`}>
          {status}
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="text-sm">
          <span className="text-gray-400">Type: </span>
          <span className="text-white">{type}</span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">RPC: </span>
          <span className="text-white text-xs">{rpcUrl.substring(0, 30)}...</span>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 rounded text-sm">
          Configure
        </button>
        <button className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded text-sm">
          Monitor
        </button>
      </div>
    </div>
  )
}

function AITaskCard({ title, status, progress, lastRun, recommendations }: any) {
  const statusColors = {
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    pending: 'bg-yellow-500',
    failed: 'bg-red-500'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-white font-medium">{title}</h3>
        <span className={`px-2 py-1 rounded text-xs text-white ${statusColors[status]}`}>
          {status}
        </span>
      </div>
      
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-400">Progress</span>
          <span className="text-white">{progress}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-orange-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Last Run:</span>
          <span className="text-white">{lastRun}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Recommendations:</span>
          <span className="text-orange-400">{recommendations}</span>
        </div>
      </div>
    </div>
  )
}

function AIRecommendation({ type, title, description, priority, estimatedImpact }: any) {
  const priorityColors = {
    low: 'bg-green-500',
    medium: 'bg-yellow-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500'
  }

  const typeIcons = {
    performance: TrendingUp,
    security: Shield,
    optimization: Zap,
    maintenance: Settings
  }

  const Icon = typeIcons[type] || Settings

  return (
    <div className="bg-gray-700 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h4 className="text-white font-medium">{title}</h4>
            <span className={`px-2 py-1 rounded text-xs text-white ${priorityColors[priority]}`}>
              {priority}
            </span>
          </div>
          <p className="text-gray-300 text-sm mb-3">{description}</p>
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Impact: {estimatedImpact}</span>
            <div className="flex gap-2">
              <button className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">
                Apply
              </button>
              <button className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm">
                Dismiss
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
