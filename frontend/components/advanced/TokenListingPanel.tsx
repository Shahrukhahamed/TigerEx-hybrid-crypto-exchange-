import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlusIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
  ArrowUpTrayIcon,
  CurrencyDollarIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  BeakerIcon,
  ChartBarIcon,
  LinkIcon,
  UserGroupIcon,
  DocumentCheckIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

interface TokenInfo {
  symbol: string;
  name: string;
  contractAddress: string;
  decimals: number;
  totalSupply: string;
  tokenType: 'ERC20' | 'BEP20' | 'TRC20' | 'SPL' | 'NATIVE' | 'CUSTOM_EVM' | 'CUSTOM_WEB3';
  blockchain: string;
  website: string;
  whitepaperUrl: string;
  socialLinks: Record<string, string>;
  description: string;
  useCase: string;
  teamInfo: Record<string, any>;
  tokenomics: Record<string, any>;
  kycVerified: boolean;
  isMintable: boolean;
  isBurnable: boolean;
  isPausable: boolean;
}

interface ListingApplication {
  id: string;
  tokenInfo: TokenInfo;
  listingType: 'CEX_ONLY' | 'DEX_ONLY' | 'HYBRID';
  requestedPairs: string[];
  listingFee: number;
  marketMakerCommitment?: Record<string, any>;
  marketingPlan?: Record<string, any>;
  status: 'PENDING' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'LISTED';
  submittedAt: string;
  reviewedAt?: string;
  listingDate?: string;
  rejectionReason?: string;
}

const TokenListingPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'submit' | 'applications' | 'listed'>('submit');
  const [applications, setApplications] = useState<ListingApplication[]>([]);
  const [listedTokens, setListedTokens] = useState<ListingApplication[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSubmissionForm, setShowSubmissionForm] = useState(false);

  // Form state
  const [tokenInfo, setTokenInfo] = useState<Partial<TokenInfo>>({
    tokenType: 'ERC20',
    blockchain: 'ethereum',
    socialLinks: {},
    teamInfo: {},
    tokenomics: {},
    kycVerified: false,
    isMintable: false,
    isBurnable: false,
    isPausable: false,
  });
  const [listingType, setListingType] = useState<'CEX_ONLY' | 'DEX_ONLY' | 'HYBRID'>('HYBRID');
  const [requestedPairs, setRequestedPairs] = useState<string[]>(['USDT']);

  useEffect(() => {
    fetchApplications();
    fetchListedTokens();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await fetch('/api/v1/tokens/applications');
      const data = await response.json();
      setApplications(data);
    } catch (error) {
      console.error('Error fetching applications:', error);
    }
  };

  const fetchListedTokens = async () => {
    try {
      const response = await fetch('/api/v1/tokens/listed');
      const data = await response.json();
      setListedTokens(data);
    } catch (error) {
      console.error('Error fetching listed tokens:', error);
    }
  };

  const validateContract = async () => {
    if (!tokenInfo.contractAddress || !tokenInfo.blockchain) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/tokens/validate-contract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_address: tokenInfo.contractAddress,
          blockchain: tokenInfo.blockchain,
        }),
      });
      const data = await response.json();
      
      if (data.is_valid && data.token_info) {
        setTokenInfo(prev => ({
          ...prev,
          ...data.token_info,
        }));
      }
    } catch (error) {
      console.error('Error validating contract:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitApplication = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/tokens/submit-listing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token_info: tokenInfo,
          listing_type: listingType,
          requested_pairs: requestedPairs,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`Application submitted successfully! ID: ${data.application_id}`);
        setShowSubmissionForm(false);
        fetchApplications();
        // Reset form
        setTokenInfo({
          tokenType: 'ERC20',
          blockchain: 'ethereum',
          socialLinks: {},
          teamInfo: {},
          tokenomics: {},
          kycVerified: false,
          isMintable: false,
          isBurnable: false,
          isPausable: false,
        });
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error submitting application:', error);
      alert('Error submitting application');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'UNDER_REVIEW':
        return <EyeIcon className="h-5 w-5 text-blue-500" />;
      case 'APPROVED':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'REJECTED':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'LISTED':
        return <CheckCircleIcon className="h-5 w-5 text-emerald-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'UNDER_REVIEW':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'APPROVED':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'REJECTED':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'LISTED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Token Listing Center</h1>
          <p className="text-gray-300">Submit your token for listing on TigerEx CEX and DEX platforms</p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8 bg-black/20 backdrop-blur-lg rounded-xl p-1">
          {[
            { id: 'submit', label: 'Submit Application', icon: PlusIcon },
            { id: 'applications', label: 'My Applications', icon: DocumentTextIcon },
            { id: 'listed', label: 'Listed Tokens', icon: CheckCircleIcon },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-orange-500 text-white shadow-lg'
                  : 'text-gray-300 hover:text-white hover:bg-white/10'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'submit' && (
            <motion.div
              key="submit"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {!showSubmissionForm ? (
                <div className="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 p-8 text-center">
                  <div className="max-w-2xl mx-auto">
                    <div className="mb-6">
                      <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-500/20 rounded-full mb-4">
                        <PlusIcon className="h-8 w-8 text-orange-400" />
                      </div>
                      <h2 className="text-2xl font-bold text-white mb-2">List Your Token</h2>
                      <p className="text-gray-300">
                        Get your token listed on TigerEx's CEX and DEX platforms with our streamlined application process
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                      <div className="bg-white/5 rounded-lg p-6">
                        <ShieldCheckIcon className="h-8 w-8 text-green-400 mx-auto mb-3" />
                        <h3 className="font-semibold text-white mb-2">Secure & Compliant</h3>
                        <p className="text-gray-400 text-sm">Full KYC/AML compliance and security audits</p>
                      </div>
                      <div className="bg-white/5 rounded-lg p-6">
                        <GlobeAltIcon className="h-8 w-8 text-blue-400 mx-auto mb-3" />
                        <h3 className="font-semibold text-white mb-2">Multi-Chain Support</h3>
                        <p className="text-gray-400 text-sm">Support for 10+ blockchain networks</p>
                      </div>
                      <div className="bg-white/5 rounded-lg p-6">
                        <ChartBarIcon className="h-8 w-8 text-purple-400 mx-auto mb-3" />
                        <h3 className="font-semibold text-white mb-2">High Liquidity</h3>
                        <p className="text-gray-400 text-sm">Access to shared liquidity from top exchanges</p>
                      </div>
                    </div>

                    <button
                      onClick={() => setShowSubmissionForm(true)}
                      className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-lg font-medium transition-colors"
                    >
                      Start Application
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 p-8">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-white mb-2">Token Listing Application</h2>
                    <p className="text-gray-300">Please provide detailed information about your token</p>
                  </div>

                  <div className="space-y-8">
                    {/* Basic Token Information */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <BeakerIcon className="h-5 w-5 mr-2 text-orange-400" />
                        Basic Token Information
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-gray-300 text-sm font-medium mb-2">Token Symbol</label>
                          <input
                            type="text"
                            value={tokenInfo.symbol || ''}
                            onChange={(e) => setTokenInfo(prev => ({ ...prev, symbol: e.target.value }))}
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400"
                            placeholder="e.g., TIGER"
                          />
                        </div>
                        <div>
                          <label className="block text-gray-300 text-sm font-medium mb-2">Token Name</label>
                          <input
                            type="text"
                            value={tokenInfo.name || ''}
                            onChange={(e) => setTokenInfo(prev => ({ ...prev, name: e.target.value }))}
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400"
                            placeholder="e.g., TigerEx Token"
                          />
                        </div>
                        <div>
                          <label className="block text-gray-300 text-sm font-medium mb-2">Blockchain</label>
                          <select
                            value={tokenInfo.blockchain || 'ethereum'}
                            onChange={(e) => setTokenInfo(prev => ({ ...prev, blockchain: e.target.value }))}
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-orange-400"
                          >
                            <option value="ethereum">Ethereum</option>
                            <option value="bsc">BSC</option>
                            <option value="polygon">Polygon</option>
                            <option value="arbitrum">Arbitrum</option>
                            <option value="optimism">Optimism</option>
                            <option value="avalanche">Avalanche</option>
                            <option value="solana">Solana</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-gray-300 text-sm font-medium mb-2">Token Type</label>
                          <select
                            value={tokenInfo.tokenType || 'ERC20'}
                            onChange={(e) => setTokenInfo(prev => ({ ...prev, tokenType: e.target.value as any }))}
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-orange-400"
                          >
                            <option value="ERC20">ERC20</option>
                            <option value="BEP20">BEP20</option>
                            <option value="TRC20">TRC20</option>
                            <option value="SPL">SPL (Solana)</option>
                            <option value="CUSTOM_EVM">Custom EVM</option>
                            <option value="CUSTOM_WEB3">Custom Web3</option>
                          </select>
                        </div>
                        <div className="md:col-span-2">
                          <label className="block text-gray-300 text-sm font-medium mb-2">Contract Address</label>
                          <div className="flex space-x-2">
                            <input
                              type="text"
                              value={tokenInfo.contractAddress || ''}
                              onChange={(e) => setTokenInfo(prev => ({ ...prev, contractAddress: e.target.value }))}
                              className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400"
                              placeholder="0x..."
                            />
                            <button
                              onClick={validateContract}
                              disabled={loading}
                              className="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                            >
                              {loading ? 'Validating...' : 'Validate'}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Submit Button */}
                    <div className="flex justify-between pt-6 border-t border-white/10">
                      <button
                        onClick={() => setShowSubmissionForm(false)}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={submitApplication}
                        disabled={loading || !tokenInfo.symbol || !tokenInfo.name}
                        className="bg-orange-500 hover:bg-orange-600 disabled:bg-orange-500/50 text-white px-8 py-3 rounded-lg font-medium transition-colors"
                      >
                        {loading ? 'Submitting...' : 'Submit Application'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'applications' && (
            <motion.div
              key="applications"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
                <div className="p-6 border-b border-white/10">
                  <h2 className="text-xl font-semibold text-white">My Applications</h2>
                  <p className="text-gray-300 mt-1">Track the status of your token listing applications</p>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-white/5">
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Token
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Submitted
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Fee
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {applications.map((app) => (
                        <tr key={app.id} className="hover:bg-white/5 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10">
                                <div className="h-10 w-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                                  <span className="text-orange-400 font-medium text-sm">
                                    {app.tokenInfo.symbol?.substring(0, 2)}
                                  </span>
                                </div>
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-white">{app.tokenInfo.symbol}</div>
                                <div className="text-sm text-gray-400">{app.tokenInfo.name}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {app.listingType.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(app.status)}`}>
                              {getStatusIcon(app.status)}
                              <span className="ml-1">{app.status.replace('_', ' ')}</span>
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            {new Date(app.submittedAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            ${app.listingFee.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button className="text-orange-400 hover:text-orange-300 transition-colors">
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'listed' && (
            <motion.div
              key="listed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="bg-black/20 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
                <div className="p-6 border-b border-white/10">
                  <h2 className="text-xl font-semibold text-white">Listed Tokens</h2>
                  <p className="text-gray-300 mt-1">Tokens currently listed on TigerEx</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                  {listedTokens.map((token) => (
                    <div key={token.id} className="bg-white/5 rounded-lg p-6 hover:bg-white/10 transition-colors">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="h-12 w-12 rounded-full bg-orange-500/20 flex items-center justify-center">
                            <span className="text-orange-400 font-bold">
                              {token.tokenInfo.symbol?.substring(0, 2)}
                            </span>
                          </div>
                          <div>
                            <h3 className="text-white font-semibold">{token.tokenInfo.symbol}</h3>
                            <p className="text-gray-400 text-sm">{token.tokenInfo.name}</p>
                          </div>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                          Listed
                        </span>
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Blockchain:</span>
                          <span className="text-white capitalize">{token.tokenInfo.blockchain}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Type:</span>
                          <span className="text-white">{token.listingType.replace('_', ' ')}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Listed:</span>
                          <span className="text-white">
                            {token.listingDate ? new Date(token.listingDate).toLocaleDateString() : 'N/A'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex space-x-2">
                        {token.tokenInfo.website && (
                          <a
                            href={token.tokenInfo.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 px-3 py-2 rounded-lg text-sm font-medium text-center transition-colors"
                          >
                            Website
                          </a>
                        )}
                        <button className="flex-1 bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 px-3 py-2 rounded-lg text-sm font-medium transition-colors">
                          Trade
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default TokenListingPanel;