using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;
using System.ComponentModel.DataAnnotations;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using StackExchange.Redis;
using Confluent.Kafka;

namespace TigerEx.InstitutionalTrading.Controllers
{
    /// <summary>
    /// TigerEx Institutional Trading Controller
    /// Handles OTC trading, prime brokerage, custody services, and institutional-grade features
    /// Built with C# .NET 8 for enterprise-level performance and security
    /// </summary>
    [ApiController]
    [Route("api/v1/institutional")]
    [Authorize(Roles = "Institution,PrimeBroker,OTCDealer")]
    public class InstitutionalTradingController : ControllerBase
    {
        private readonly ILogger<InstitutionalTradingController> _logger;
        private readonly IInstitutionalTradingService _tradingService;
        private readonly IOTCTradingService _otcService;
        private readonly IPrimeBrokerageService _primeService;
        private readonly ICustodyService _custodyService;
        private readonly ILiquidityProviderService _liquidityService;
        private readonly IComplianceService _complianceService;
        private readonly IRiskManagementService _riskService;

        public InstitutionalTradingController(
            ILogger<InstitutionalTradingController> logger,
            IInstitutionalTradingService tradingService,
            IOTCTradingService otcService,
            IPrimeBrokerageService primeService,
            ICustodyService custodyService,
            ILiquidityProviderService liquidityService,
            IComplianceService complianceService,
            IRiskManagementService riskService)
        {
            _logger = logger;
            _tradingService = tradingService;
            _otcService = otcService;
            _primeService = primeService;
            _custodyService = custodyService;
            _liquidityService = liquidityService;
            _complianceService = complianceService;
            _riskService = riskService;
        }

        /// <summary>
        /// Get institutional account information
        /// </summary>
        [HttpGet("account")]
        public async Task<ActionResult<InstitutionalAccountResponse>> GetAccountInfo()
        {
            try
            {
                var userId = GetCurrentUserId();
                var account = await _tradingService.GetInstitutionalAccountAsync(userId);
                return Ok(account);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving institutional account info");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Create OTC trade request
        /// </summary>
        [HttpPost("otc/request")]
        public async Task<ActionResult<OTCTradeResponse>> CreateOTCTradeRequest([FromBody] OTCTradeRequest request)
        {
            try
            {
                if (!ModelState.IsValid)
                    return BadRequest(ModelState);

                var userId = GetCurrentUserId();
                
                // Compliance check
                var complianceResult = await _complianceService.ValidateOTCTradeAsync(userId, request);
                if (!complianceResult.IsApproved)
                    return BadRequest(new { error = complianceResult.Reason });

                // Risk assessment
                var riskAssessment = await _riskService.AssessOTCTradeRiskAsync(userId, request);
                if (riskAssessment.RiskLevel > RiskLevel.High)
                    return BadRequest(new { error = "Trade exceeds risk limits" });

                var result = await _otcService.CreateTradeRequestAsync(userId, request);
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating OTC trade request");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get OTC trade quotes
        /// </summary>
        [HttpGet("otc/quotes")]
        public async Task<ActionResult<List<OTCQuote>>> GetOTCQuotes(
            [FromQuery] string symbol,
            [FromQuery] decimal quantity,
            [FromQuery] string side)
        {
            try
            {
                var userId = GetCurrentUserId();
                var quotes = await _otcService.GetQuotesAsync(userId, symbol, quantity, side);
                return Ok(quotes);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving OTC quotes");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Execute OTC trade
        /// </summary>
        [HttpPost("otc/execute")]
        public async Task<ActionResult<OTCExecutionResponse>> ExecuteOTCTrade([FromBody] OTCExecutionRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                
                // Final compliance and risk checks
                var finalChecks = await _complianceService.FinalOTCValidationAsync(userId, request);
                if (!finalChecks.IsApproved)
                    return BadRequest(new { error = finalChecks.Reason });

                var result = await _otcService.ExecuteTradeAsync(userId, request);
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error executing OTC trade");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get prime brokerage services
        /// </summary>
        [HttpGet("prime-brokerage")]
        public async Task<ActionResult<PrimeBrokerageResponse>> GetPrimeBrokerageServices()
        {
            try
            {
                var userId = GetCurrentUserId();
                var services = await _primeService.GetServicesAsync(userId);
                return Ok(services);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving prime brokerage services");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Create prime brokerage order
        /// </summary>
        [HttpPost("prime-brokerage/order")]
        public async Task<ActionResult<PrimeBrokerageOrderResponse>> CreatePrimeBrokerageOrder([FromBody] PrimeBrokerageOrderRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                var result = await _primeService.CreateOrderAsync(userId, request);
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating prime brokerage order");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get custody services information
        /// </summary>
        [HttpGet("custody")]
        public async Task<ActionResult<CustodyResponse>> GetCustodyServices()
        {
            try
            {
                var userId = GetCurrentUserId();
                var custody = await _custodyService.GetCustodyInfoAsync(userId);
                return Ok(custody);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving custody services");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Request custody withdrawal
        /// </summary>
        [HttpPost("custody/withdraw")]
        public async Task<ActionResult<CustodyWithdrawalResponse>> RequestCustodyWithdrawal([FromBody] CustodyWithdrawalRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                
                // Multi-signature approval required for custody withdrawals
                var approvalResult = await _custodyService.InitiateWithdrawalApprovalAsync(userId, request);
                return Ok(approvalResult);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error requesting custody withdrawal");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Provide liquidity to institutional pools
        /// </summary>
        [HttpPost("liquidity/provide")]
        public async Task<ActionResult<LiquidityProvisionResponse>> ProvideLiquidity([FromBody] LiquidityProvisionRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                var result = await _liquidityService.ProvideLiquidityAsync(userId, request);
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error providing liquidity");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get institutional trading analytics
        /// </summary>
        [HttpGet("analytics")]
        public async Task<ActionResult<InstitutionalAnalyticsResponse>> GetAnalytics(
            [FromQuery] DateTime? startDate,
            [FromQuery] DateTime? endDate,
            [FromQuery] string? symbol)
        {
            try
            {
                var userId = GetCurrentUserId();
                var analytics = await _tradingService.GetAnalyticsAsync(userId, startDate, endDate, symbol);
                return Ok(analytics);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving analytics");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get institutional fee structure
        /// </summary>
        [HttpGet("fees")]
        public async Task<ActionResult<InstitutionalFeeStructure>> GetFeeStructure()
        {
            try
            {
                var userId = GetCurrentUserId();
                var fees = await _tradingService.GetFeeStructureAsync(userId);
                return Ok(fees);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving fee structure");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Create block trade
        /// </summary>
        [HttpPost("block-trade")]
        public async Task<ActionResult<BlockTradeResponse>> CreateBlockTrade([FromBody] BlockTradeRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                
                // Block trades require special handling and approval
                var result = await _tradingService.CreateBlockTradeAsync(userId, request);
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating block trade");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get market making opportunities
        /// </summary>
        [HttpGet("market-making")]
        public async Task<ActionResult<MarketMakingOpportunities>> GetMarketMakingOpportunities()
        {
            try
            {
                var userId = GetCurrentUserId();
                var opportunities = await _liquidityService.GetMarketMakingOpportunitiesAsync(userId);
                return Ok(opportunities);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving market making opportunities");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Create algorithmic trading strategy
        /// </summary>
        [HttpPost("algo-trading/strategy")]
        public async Task<ActionResult<AlgoTradingStrategyResponse>> CreateAlgoStrategy([FromBody] AlgoTradingStrategyRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                var result = await _tradingService.CreateAlgoStrategyAsync(userId, request);
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating algo trading strategy");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        /// <summary>
        /// Get compliance reports
        /// </summary>
        [HttpGet("compliance/reports")]
        public async Task<ActionResult<ComplianceReportsResponse>> GetComplianceReports(
            [FromQuery] DateTime startDate,
            [FromQuery] DateTime endDate,
            [FromQuery] string? reportType)
        {
            try
            {
                var userId = GetCurrentUserId();
                var reports = await _complianceService.GetReportsAsync(userId, startDate, endDate, reportType);
                return Ok(reports);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving compliance reports");
                return StatusCode(500, new { error = "Internal server error" });
            }
        }

        private long GetCurrentUserId()
        {
            var userIdClaim = User.FindFirst("user_id")?.Value;
            return long.Parse(userIdClaim ?? "0");
        }
    }

    // Service Interfaces
    public interface IInstitutionalTradingService
    {
        Task<InstitutionalAccountResponse> GetInstitutionalAccountAsync(long userId);
        Task<InstitutionalAnalyticsResponse> GetAnalyticsAsync(long userId, DateTime? startDate, DateTime? endDate, string? symbol);
        Task<InstitutionalFeeStructure> GetFeeStructureAsync(long userId);
        Task<BlockTradeResponse> CreateBlockTradeAsync(long userId, BlockTradeRequest request);
        Task<AlgoTradingStrategyResponse> CreateAlgoStrategyAsync(long userId, AlgoTradingStrategyRequest request);
    }

    public interface IOTCTradingService
    {
        Task<OTCTradeResponse> CreateTradeRequestAsync(long userId, OTCTradeRequest request);
        Task<List<OTCQuote>> GetQuotesAsync(long userId, string symbol, decimal quantity, string side);
        Task<OTCExecutionResponse> ExecuteTradeAsync(long userId, OTCExecutionRequest request);
    }

    public interface IPrimeBrokerageService
    {
        Task<PrimeBrokerageResponse> GetServicesAsync(long userId);
        Task<PrimeBrokerageOrderResponse> CreateOrderAsync(long userId, PrimeBrokerageOrderRequest request);
    }

    public interface ICustodyService
    {
        Task<CustodyResponse> GetCustodyInfoAsync(long userId);
        Task<CustodyWithdrawalResponse> InitiateWithdrawalApprovalAsync(long userId, CustodyWithdrawalRequest request);
    }

    public interface ILiquidityProviderService
    {
        Task<LiquidityProvisionResponse> ProvideLiquidityAsync(long userId, LiquidityProvisionRequest request);
        Task<MarketMakingOpportunities> GetMarketMakingOpportunitiesAsync(long userId);
    }

    public interface IComplianceService
    {
        Task<ComplianceResult> ValidateOTCTradeAsync(long userId, OTCTradeRequest request);
        Task<ComplianceResult> FinalOTCValidationAsync(long userId, OTCExecutionRequest request);
        Task<ComplianceReportsResponse> GetReportsAsync(long userId, DateTime startDate, DateTime endDate, string? reportType);
    }

    public interface IRiskManagementService
    {
        Task<RiskAssessment> AssessOTCTradeRiskAsync(long userId, OTCTradeRequest request);
    }

    // Data Models
    public class InstitutionalAccountResponse
    {
        public long UserId { get; set; }
        public string AccountType { get; set; } = string.Empty;
        public string TierLevel { get; set; } = string.Empty;
        public decimal TotalBalance { get; set; }
        public decimal AvailableBalance { get; set; }
        public decimal MarginUsed { get; set; }
        public decimal CreditLimit { get; set; }
        public List<InstitutionalBalance> Balances { get; set; } = new();
        public InstitutionalFeeStructure FeeStructure { get; set; } = new();
        public List<string> AvailableServices { get; set; } = new();
        public DateTime LastActivity { get; set; }
    }

    public class InstitutionalBalance
    {
        public string Asset { get; set; } = string.Empty;
        public decimal Available { get; set; }
        public decimal Locked { get; set; }
        public decimal InCustody { get; set; }
        public decimal Staked { get; set; }
        public decimal Borrowed { get; set; }
    }

    public class InstitutionalFeeStructure
    {
        public decimal SpotTradingFee { get; set; }
        public decimal FuturesTradingFee { get; set; }
        public decimal OTCTradingFee { get; set; }
        public decimal CustodyFee { get; set; }
        public decimal WithdrawalFee { get; set; }
        public decimal PrimeBrokerageFee { get; set; }
        public bool VolumeDiscounts { get; set; }
        public Dictionary<string, decimal> CustomFees { get; set; } = new();
    }

    public class OTCTradeRequest
    {
        [Required]
        public string Symbol { get; set; } = string.Empty;
        
        [Required]
        [Range(0.000001, double.MaxValue)]
        public decimal Quantity { get; set; }
        
        [Required]
        public string Side { get; set; } = string.Empty; // BUY, SELL
        
        public decimal? TargetPrice { get; set; }
        public DateTime? ExpiryTime { get; set; }
        public string? Notes { get; set; }
        public bool IsBlockTrade { get; set; }
        public string? CounterpartyPreference { get; set; }
    }

    public class OTCTradeResponse
    {
        public string RequestId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime? ExpiryTime { get; set; }
        public List<OTCQuote> Quotes { get; set; } = new();
    }

    public class OTCQuote
    {
        public string QuoteId { get; set; } = string.Empty;
        public string DealerId { get; set; } = string.Empty;
        public string DealerName { get; set; } = string.Empty;
        public decimal Price { get; set; }
        public decimal Quantity { get; set; }
        public DateTime ValidUntil { get; set; }
        public decimal Spread { get; set; }
        public string Currency { get; set; } = string.Empty;
        public bool IsIndicative { get; set; }
    }

    public class OTCExecutionRequest
    {
        [Required]
        public string QuoteId { get; set; } = string.Empty;
        
        [Required]
        public string RequestId { get; set; } = string.Empty;
        
        public decimal? PartialQuantity { get; set; }
        public string? ExecutionInstructions { get; set; }
    }

    public class OTCExecutionResponse
    {
        public string ExecutionId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public decimal ExecutedQuantity { get; set; }
        public decimal ExecutedPrice { get; set; }
        public decimal TotalValue { get; set; }
        public decimal Fee { get; set; }
        public DateTime ExecutedAt { get; set; }
        public string SettlementInstructions { get; set; } = string.Empty;
    }

    public class PrimeBrokerageResponse
    {
        public List<string> AvailableExchanges { get; set; } = new();
        public List<string> SupportedAssets { get; set; } = new();
        public decimal CreditLimit { get; set; }
        public decimal UsedCredit { get; set; }
        public List<PrimeBrokerageAccount> Accounts { get; set; } = new();
        public PrimeBrokerageSettings Settings { get; set; } = new();
    }

    public class PrimeBrokerageAccount
    {
        public string Exchange { get; set; } = string.Empty;
        public string AccountId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public List<InstitutionalBalance> Balances { get; set; } = new();
        public DateTime LastSync { get; set; }
    }

    public class PrimeBrokerageSettings
    {
        public bool AutoHedging { get; set; }
        public bool CrossMarginEnabled { get; set; }
        public decimal RiskLimit { get; set; }
        public string DefaultExchange { get; set; } = string.Empty;
        public Dictionary<string, object> CustomSettings { get; set; } = new();
    }

    public class PrimeBrokerageOrderRequest
    {
        [Required]
        public string Symbol { get; set; } = string.Empty;
        
        [Required]
        public string Side { get; set; } = string.Empty;
        
        [Required]
        public string Type { get; set; } = string.Empty;
        
        [Required]
        public decimal Quantity { get; set; }
        
        public decimal? Price { get; set; }
        public string? TargetExchange { get; set; }
        public bool SmartRouting { get; set; } = true;
        public string? TimeInForce { get; set; }
        public Dictionary<string, object> AdvancedOptions { get; set; } = new();
    }

    public class PrimeBrokerageOrderResponse
    {
        public string OrderId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public List<PrimeBrokerageExecution> Executions { get; set; } = new();
        public DateTime CreatedAt { get; set; }
    }

    public class PrimeBrokerageExecution
    {
        public string Exchange { get; set; } = string.Empty;
        public decimal Quantity { get; set; }
        public decimal Price { get; set; }
        public decimal Fee { get; set; }
        public DateTime ExecutedAt { get; set; }
    }

    public class CustodyResponse
    {
        public decimal TotalAssetsUnderCustody { get; set; }
        public List<CustodyAsset> Assets { get; set; } = new();
        public CustodySettings Settings { get; set; } = new();
        public List<CustodyTransaction> RecentTransactions { get; set; } = new();
    }

    public class CustodyAsset
    {
        public string Asset { get; set; } = string.Empty;
        public decimal Quantity { get; set; }
        public decimal UsdValue { get; set; }
        public string StorageType { get; set; } = string.Empty; // HOT, COLD, WARM
        public string InsuranceCoverage { get; set; } = string.Empty;
        public DateTime LastAudit { get; set; }
    }

    public class CustodySettings
    {
        public bool MultiSigRequired { get; set; }
        public int RequiredSignatures { get; set; }
        public List<string> AuthorizedSigners { get; set; } = new();
        public decimal DailyWithdrawalLimit { get; set; }
        public bool WhitelistEnabled { get; set; }
        public List<string> WhitelistedAddresses { get; set; } = new();
    }

    public class CustodyTransaction
    {
        public string TransactionId { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        public string Asset { get; set; } = string.Empty;
        public decimal Amount { get; set; }
        public string Status { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public List<string> Signatures { get; set; } = new();
    }

    public class CustodyWithdrawalRequest
    {
        [Required]
        public string Asset { get; set; } = string.Empty;
        
        [Required]
        public decimal Amount { get; set; }
        
        [Required]
        public string DestinationAddress { get; set; } = string.Empty;
        
        public string? Memo { get; set; }
        public string? Purpose { get; set; }
        public bool UrgentProcessing { get; set; }
    }

    public class CustodyWithdrawalResponse
    {
        public string WithdrawalId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public int RequiredSignatures { get; set; }
        public int CurrentSignatures { get; set; }
        public List<string> PendingSigners { get; set; } = new();
        public DateTime EstimatedCompletion { get; set; }
    }

    public class LiquidityProvisionRequest
    {
        [Required]
        public string Symbol { get; set; } = string.Empty;
        
        [Required]
        public decimal Amount { get; set; }
        
        public string? PoolType { get; set; }
        public decimal? MinReturn { get; set; }
        public int? LockupPeriod { get; set; }
    }

    public class LiquidityProvisionResponse
    {
        public string ProvisionId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public decimal EstimatedReturn { get; set; }
        public decimal LiquidityTokens { get; set; }
        public DateTime MaturityDate { get; set; }
    }

    public class MarketMakingOpportunities
    {
        public List<MarketMakingOpportunity> Opportunities { get; set; } = new();
        public decimal TotalPotentialReturn { get; set; }
        public DateTime LastUpdated { get; set; }
    }

    public class MarketMakingOpportunity
    {
        public string Symbol { get; set; } = string.Empty;
        public decimal Spread { get; set; }
        public decimal Volume24h { get; set; }
        public decimal EstimatedReturn { get; set; }
        public string RiskLevel { get; set; } = string.Empty;
        public decimal RequiredCapital { get; set; }
    }

    public class BlockTradeRequest
    {
        [Required]
        public string Symbol { get; set; } = string.Empty;
        
        [Required]
        public decimal Quantity { get; set; }
        
        [Required]
        public string Side { get; set; } = string.Empty;
        
        public decimal? Price { get; set; }
        public string? ExecutionStrategy { get; set; }
        public int? MaxSlices { get; set; }
        public TimeSpan? ExecutionTimeframe { get; set; }
    }

    public class BlockTradeResponse
    {
        public string BlockTradeId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public List<BlockTradeSlice> Slices { get; set; } = new();
        public decimal TotalExecuted { get; set; }
        public decimal AveragePrice { get; set; }
    }

    public class BlockTradeSlice
    {
        public string SliceId { get; set; } = string.Empty;
        public decimal Quantity { get; set; }
        public decimal? Price { get; set; }
        public string Status { get; set; } = string.Empty;
        public DateTime ScheduledTime { get; set; }
    }

    public class AlgoTradingStrategyRequest
    {
        [Required]
        public string StrategyType { get; set; } = string.Empty;
        
        [Required]
        public string Symbol { get; set; } = string.Empty;
        
        [Required]
        public Dictionary<string, object> Parameters { get; set; } = new();
        
        public decimal? MaxPosition { get; set; }
        public decimal? RiskLimit { get; set; }
        public bool BacktestRequired { get; set; }
    }

    public class AlgoTradingStrategyResponse
    {
        public string StrategyId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public Dictionary<string, object> BacktestResults { get; set; } = new();
        public DateTime CreatedAt { get; set; }
        public DateTime? ActivationTime { get; set; }
    }

    public class InstitutionalAnalyticsResponse
    {
        public decimal TotalVolume { get; set; }
        public decimal TotalPnL { get; set; }
        public int TotalTrades { get; set; }
        public decimal AverageTradeSize { get; set; }
        public decimal SharpeRatio { get; set; }
        public decimal MaxDrawdown { get; set; }
        public List<AnalyticsDataPoint> VolumeData { get; set; } = new();
        public List<AnalyticsDataPoint> PnLData { get; set; } = new();
        public Dictionary<string, decimal> AssetBreakdown { get; set; } = new();
    }

    public class AnalyticsDataPoint
    {
        public DateTime Timestamp { get; set; }
        public decimal Value { get; set; }
    }

    public class ComplianceResult
    {
        public bool IsApproved { get; set; }
        public string Reason { get; set; } = string.Empty;
        public List<string> RequiredActions { get; set; } = new();
        public DateTime ValidUntil { get; set; }
    }

    public class RiskAssessment
    {
        public RiskLevel RiskLevel { get; set; }
        public decimal RiskScore { get; set; }
        public List<string> RiskFactors { get; set; } = new();
        public Dictionary<string, decimal> Limits { get; set; } = new();
    }

    public class ComplianceReportsResponse
    {
        public List<ComplianceReport> Reports { get; set; } = new();
        public DateTime GeneratedAt { get; set; }
    }

    public class ComplianceReport
    {
        public string ReportId { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        public DateTime Period { get; set; }
        public string Status { get; set; } = string.Empty;
        public string DownloadUrl { get; set; } = string.Empty;
    }

    public enum RiskLevel
    {
        Low = 1,
        Medium = 2,
        High = 3,
        Critical = 4
    }
}