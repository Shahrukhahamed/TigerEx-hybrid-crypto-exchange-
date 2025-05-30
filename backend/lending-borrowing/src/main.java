/*
TigerEx Lending & Borrowing Service
Advanced lending platform with features from Binance, Bybit, OKX
Supports flexible savings, fixed savings, crypto loans, margin lending, and DeFi integration
*/

package com.tigerex.lending;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;

import javax.persistence.*;
import javax.validation.constraints.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SpringBootApplication
@EnableScheduling
public class LendingBorrowingApplication {
    public static void main(String[] args) {
        SpringApplication.run(LendingBorrowingApplication.class, args);
    }
}

// Enums
enum ProductType {
    FLEXIBLE_SAVINGS,
    FIXED_SAVINGS,
    ACTIVITY_SAVINGS,
    DUAL_INVESTMENT,
    STRUCTURED_PRODUCT,
    CRYPTO_LOAN,
    MARGIN_LOAN,
    FLASH_LOAN,
    LIQUIDITY_FARMING,
    STAKING,
    DEFI_STAKING,
    AUTO_INVEST,
    LAUNCHPOOL,
    SIMPLE_EARN,
    BNB_VAULT,
    ETH_STAKING,
    DOT_SLOT_AUCTION,
    MINING_POOL
}

enum LoanStatus {
    PENDING,
    ACTIVE,
    REPAID,
    LIQUIDATED,
    DEFAULTED,
    CANCELLED
}

enum CollateralStatus {
    ACTIVE,
    LIQUIDATING,
    LIQUIDATED,
    RELEASED
}

enum InterestType {
    SIMPLE,
    COMPOUND,
    VARIABLE,
    FIXED
}

enum RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    VERY_HIGH
}

// Entities
@Entity
@Table(name = "lending_products")
class LendingProduct {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String productId;
    
    @Column(nullable = false)
    private String name;
    
    @Column(nullable = false)
    private String description;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ProductType type;
    
    @Column(nullable = false)
    private String asset;
    
    @Column(nullable = false, precision = 10, scale = 6)
    private BigDecimal minAmount;
    
    @Column(precision = 15, scale = 6)
    private BigDecimal maxAmount;
    
    @Column(nullable = false, precision = 8, scale = 6)
    private BigDecimal interestRate;
    
    @Column(precision = 8, scale = 6)
    private BigDecimal maxInterestRate;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private InterestType interestType;
    
    @Column(nullable = false)
    private Integer duration; // in days
    
    @Column
    private Integer lockPeriod; // in days
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private RiskLevel riskLevel;
    
    @Column(nullable = false)
    private Boolean isActive;
    
    @Column(nullable = false)
    private Boolean isFlexible;
    
    @Column(precision = 15, scale = 6)
    private BigDecimal totalCap;
    
    @Column(precision = 15, scale = 6)
    private BigDecimal currentAmount;
    
    @Column
    private String features; // JSON string
    
    @Column
    private String requirements; // JSON string
    
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    @Column(nullable = false)
    private LocalDateTime updatedAt;
    
    // Constructors, getters, setters
    public LendingProduct() {}
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public ProductType getType() { return type; }
    public void setType(ProductType type) { this.type = type; }
    
    public String getAsset() { return asset; }
    public void setAsset(String asset) { this.asset = asset; }
    
    public BigDecimal getMinAmount() { return minAmount; }
    public void setMinAmount(BigDecimal minAmount) { this.minAmount = minAmount; }
    
    public BigDecimal getMaxAmount() { return maxAmount; }
    public void setMaxAmount(BigDecimal maxAmount) { this.maxAmount = maxAmount; }
    
    public BigDecimal getInterestRate() { return interestRate; }
    public void setInterestRate(BigDecimal interestRate) { this.interestRate = interestRate; }
    
    public BigDecimal getMaxInterestRate() { return maxInterestRate; }
    public void setMaxInterestRate(BigDecimal maxInterestRate) { this.maxInterestRate = maxInterestRate; }
    
    public InterestType getInterestType() { return interestType; }
    public void setInterestType(InterestType interestType) { this.interestType = interestType; }
    
    public Integer getDuration() { return duration; }
    public void setDuration(Integer duration) { this.duration = duration; }
    
    public Integer getLockPeriod() { return lockPeriod; }
    public void setLockPeriod(Integer lockPeriod) { this.lockPeriod = lockPeriod; }
    
    public RiskLevel getRiskLevel() { return riskLevel; }
    public void setRiskLevel(RiskLevel riskLevel) { this.riskLevel = riskLevel; }
    
    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }
    
    public Boolean getIsFlexible() { return isFlexible; }
    public void setIsFlexible(Boolean isFlexible) { this.isFlexible = isFlexible; }
    
    public BigDecimal getTotalCap() { return totalCap; }
    public void setTotalCap(BigDecimal totalCap) { this.totalCap = totalCap; }
    
    public BigDecimal getCurrentAmount() { return currentAmount; }
    public void setCurrentAmount(BigDecimal currentAmount) { this.currentAmount = currentAmount; }
    
    public String getFeatures() { return features; }
    public void setFeatures(String features) { this.features = features; }
    
    public String getRequirements() { return requirements; }
    public void setRequirements(String requirements) { this.requirements = requirements; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}

@Entity
@Table(name = "user_positions")
class UserPosition {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String positionId;
    
    @Column(nullable = false)
    private String userId;
    
    @Column(nullable = false)
    private String productId;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal principal;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal currentAmount;
    
    @Column(nullable = false, precision = 8, scale = 6)
    private BigDecimal interestRate;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal accruedInterest;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal totalEarnings;
    
    @Column(nullable = false)
    private LocalDateTime startDate;
    
    @Column
    private LocalDateTime endDate;
    
    @Column
    private LocalDateTime lastInterestDate;
    
    @Column(nullable = false)
    private Boolean isActive;
    
    @Column(nullable = false)
    private Boolean isAutoRenew;
    
    @Column
    private String metadata; // JSON string
    
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    @Column(nullable = false)
    private LocalDateTime updatedAt;
    
    // Constructors, getters, setters
    public UserPosition() {}
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getPositionId() { return positionId; }
    public void setPositionId(String positionId) { this.positionId = positionId; }
    
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    
    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }
    
    public BigDecimal getPrincipal() { return principal; }
    public void setPrincipal(BigDecimal principal) { this.principal = principal; }
    
    public BigDecimal getCurrentAmount() { return currentAmount; }
    public void setCurrentAmount(BigDecimal currentAmount) { this.currentAmount = currentAmount; }
    
    public BigDecimal getInterestRate() { return interestRate; }
    public void setInterestRate(BigDecimal interestRate) { this.interestRate = interestRate; }
    
    public BigDecimal getAccruedInterest() { return accruedInterest; }
    public void setAccruedInterest(BigDecimal accruedInterest) { this.accruedInterest = accruedInterest; }
    
    public BigDecimal getTotalEarnings() { return totalEarnings; }
    public void setTotalEarnings(BigDecimal totalEarnings) { this.totalEarnings = totalEarnings; }
    
    public LocalDateTime getStartDate() { return startDate; }
    public void setStartDate(LocalDateTime startDate) { this.startDate = startDate; }
    
    public LocalDateTime getEndDate() { return endDate; }
    public void setEndDate(LocalDateTime endDate) { this.endDate = endDate; }
    
    public LocalDateTime getLastInterestDate() { return lastInterestDate; }
    public void setLastInterestDate(LocalDateTime lastInterestDate) { this.lastInterestDate = lastInterestDate; }
    
    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }
    
    public Boolean getIsAutoRenew() { return isAutoRenew; }
    public void setIsAutoRenew(Boolean isAutoRenew) { this.isAutoRenew = isAutoRenew; }
    
    public String getMetadata() { return metadata; }
    public void setMetadata(String metadata) { this.metadata = metadata; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}

@Entity
@Table(name = "loans")
class Loan {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String loanId;
    
    @Column(nullable = false)
    private String userId;
    
    @Column(nullable = false)
    private String loanAsset;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal loanAmount;
    
    @Column(nullable = false)
    private String collateralAsset;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal collateralAmount;
    
    @Column(nullable = false, precision = 8, scale = 6)
    private BigDecimal interestRate;
    
    @Column(nullable = false, precision = 5, scale = 4)
    private BigDecimal ltv; // Loan-to-Value ratio
    
    @Column(nullable = false, precision = 5, scale = 4)
    private BigDecimal liquidationThreshold;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal outstandingAmount;
    
    @Column(nullable = false, precision = 15, scale = 6)
    private BigDecimal accruedInterest;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private LoanStatus status;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CollateralStatus collateralStatus;
    
    @Column(nullable = false)
    private LocalDateTime startDate;
    
    @Column
    private LocalDateTime dueDate;
    
    @Column
    private LocalDateTime lastInterestDate;
    
    @Column
    private LocalDateTime repaidDate;
    
    @Column
    private LocalDateTime liquidationDate;
    
    @Column
    private String repaymentSchedule; // JSON string
    
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    @Column(nullable = false)
    private LocalDateTime updatedAt;
    
    // Constructors, getters, setters
    public Loan() {}
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getLoanId() { return loanId; }
    public void setLoanId(String loanId) { this.loanId = loanId; }
    
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    
    public String getLoanAsset() { return loanAsset; }
    public void setLoanAsset(String loanAsset) { this.loanAsset = loanAsset; }
    
    public BigDecimal getLoanAmount() { return loanAmount; }
    public void setLoanAmount(BigDecimal loanAmount) { this.loanAmount = loanAmount; }
    
    public String getCollateralAsset() { return collateralAsset; }
    public void setCollateralAsset(String collateralAsset) { this.collateralAsset = collateralAsset; }
    
    public BigDecimal getCollateralAmount() { return collateralAmount; }
    public void setCollateralAmount(BigDecimal collateralAmount) { this.collateralAmount = collateralAmount; }
    
    public BigDecimal getInterestRate() { return interestRate; }
    public void setInterestRate(BigDecimal interestRate) { this.interestRate = interestRate; }
    
    public BigDecimal getLtv() { return ltv; }
    public void setLtv(BigDecimal ltv) { this.ltv = ltv; }
    
    public BigDecimal getLiquidationThreshold() { return liquidationThreshold; }
    public void setLiquidationThreshold(BigDecimal liquidationThreshold) { this.liquidationThreshold = liquidationThreshold; }
    
    public BigDecimal getOutstandingAmount() { return outstandingAmount; }
    public void setOutstandingAmount(BigDecimal outstandingAmount) { this.outstandingAmount = outstandingAmount; }
    
    public BigDecimal getAccruedInterest() { return accruedInterest; }
    public void setAccruedInterest(BigDecimal accruedInterest) { this.accruedInterest = accruedInterest; }
    
    public LoanStatus getStatus() { return status; }
    public void setStatus(LoanStatus status) { this.status = status; }
    
    public CollateralStatus getCollateralStatus() { return collateralStatus; }
    public void setCollateralStatus(CollateralStatus collateralStatus) { this.collateralStatus = collateralStatus; }
    
    public LocalDateTime getStartDate() { return startDate; }
    public void setStartDate(LocalDateTime startDate) { this.startDate = startDate; }
    
    public LocalDateTime getDueDate() { return dueDate; }
    public void setDueDate(LocalDateTime dueDate) { this.dueDate = dueDate; }
    
    public LocalDateTime getLastInterestDate() { return lastInterestDate; }
    public void setLastInterestDate(LocalDateTime lastInterestDate) { this.lastInterestDate = lastInterestDate; }
    
    public LocalDateTime getRepaidDate() { return repaidDate; }
    public void setRepaidDate(LocalDateTime repaidDate) { this.repaidDate = repaidDate; }
    
    public LocalDateTime getLiquidationDate() { return liquidationDate; }
    public void setLiquidationDate(LocalDateTime liquidationDate) { this.liquidationDate = liquidationDate; }
    
    public String getRepaymentSchedule() { return repaymentSchedule; }
    public void setRepaymentSchedule(String repaymentSchedule) { this.repaymentSchedule = repaymentSchedule; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}

// Repositories
interface LendingProductRepository extends JpaRepository<LendingProduct, Long> {
    List<LendingProduct> findByIsActiveTrue();
    List<LendingProduct> findByTypeAndIsActiveTrue(ProductType type);
    List<LendingProduct> findByAssetAndIsActiveTrue(String asset);
    Optional<LendingProduct> findByProductId(String productId);
    
    @Query("SELECT p FROM LendingProduct p WHERE p.isActive = true AND p.currentAmount < p.totalCap")
    List<LendingProduct> findAvailableProducts();
}

interface UserPositionRepository extends JpaRepository<UserPosition, Long> {
    List<UserPosition> findByUserIdAndIsActiveTrue(String userId);
    List<UserPosition> findByProductIdAndIsActiveTrue(String productId);
    Optional<UserPosition> findByPositionId(String positionId);
    
    @Query("SELECT SUM(p.currentAmount) FROM UserPosition p WHERE p.productId = :productId AND p.isActive = true")
    BigDecimal getTotalAmountByProduct(@Param("productId") String productId);
    
    @Query("SELECT p FROM UserPosition p WHERE p.isActive = true AND p.endDate <= :date")
    List<UserPosition> findMaturedPositions(@Param("date") LocalDateTime date);
}

interface LoanRepository extends JpaRepository<Loan, Long> {
    List<Loan> findByUserIdAndStatus(String userId, LoanStatus status);
    List<Loan> findByStatus(LoanStatus status);
    Optional<Loan> findByLoanId(String loanId);
    
    @Query("SELECT l FROM Loan l WHERE l.status = 'ACTIVE' AND l.ltv >= l.liquidationThreshold")
    List<Loan> findLoansForLiquidation();
    
    @Query("SELECT SUM(l.outstandingAmount) FROM Loan l WHERE l.userId = :userId AND l.status = 'ACTIVE'")
    BigDecimal getTotalOutstandingByUser(@Param("userId") String userId);
}

// DTOs
class SubscribeProductRequest {
    @NotBlank
    private String productId;
    
    @NotNull
    @DecimalMin("0.000001")
    private BigDecimal amount;
    
    private Boolean autoRenew = false;
    
    // Getters and setters
    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }
    
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    
    public Boolean getAutoRenew() { return autoRenew; }
    public void setAutoRenew(Boolean autoRenew) { this.autoRenew = autoRenew; }
}

class LoanRequest {
    @NotBlank
    private String loanAsset;
    
    @NotNull
    @DecimalMin("0.000001")
    private BigDecimal loanAmount;
    
    @NotBlank
    private String collateralAsset;
    
    @NotNull
    @DecimalMin("0.000001")
    private BigDecimal collateralAmount;
    
    private Integer termDays;
    
    // Getters and setters
    public String getLoanAsset() { return loanAsset; }
    public void setLoanAsset(String loanAsset) { this.loanAsset = loanAsset; }
    
    public BigDecimal getLoanAmount() { return loanAmount; }
    public void setLoanAmount(BigDecimal loanAmount) { this.loanAmount = loanAmount; }
    
    public String getCollateralAsset() { return collateralAsset; }
    public void setCollateralAsset(String collateralAsset) { this.collateralAsset = collateralAsset; }
    
    public BigDecimal getCollateralAmount() { return collateralAmount; }
    public void setCollateralAmount(BigDecimal collateralAmount) { this.collateralAmount = collateralAmount; }
    
    public Integer getTermDays() { return termDays; }
    public void setTermDays(Integer termDays) { this.termDays = termDays; }
}

class RepaymentRequest {
    @NotBlank
    private String loanId;
    
    @NotNull
    @DecimalMin("0.000001")
    private BigDecimal amount;
    
    private Boolean isFullRepayment = false;
    
    // Getters and setters
    public String getLoanId() { return loanId; }
    public void setLoanId(String loanId) { this.loanId = loanId; }
    
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    
    public Boolean getIsFullRepayment() { return isFullRepayment; }
    public void setIsFullRepayment(Boolean isFullRepayment) { this.isFullRepayment = isFullRepayment; }
}

// Services
@Service
@Transactional
class LendingService {
    private static final Logger logger = LoggerFactory.getLogger(LendingService.class);
    
    @Autowired
    private LendingProductRepository productRepository;
    
    @Autowired
    private UserPositionRepository positionRepository;
    
    @Autowired
    private LoanRepository loanRepository;
    
    @Autowired
    private InterestCalculationService interestService;
    
    @Autowired
    private RiskManagementService riskService;
    
    @Autowired
    private PriceService priceService;
    
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;
    
    @Autowired
    private JedisPool jedisPool;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    public List<LendingProduct> getAvailableProducts() {
        return productRepository.findAvailableProducts();
    }
    
    public List<LendingProduct> getProductsByType(ProductType type) {
        return productRepository.findByTypeAndIsActiveTrue(type);
    }
    
    public List<LendingProduct> getProductsByAsset(String asset) {
        return productRepository.findByAssetAndIsActiveTrue(asset);
    }
    
    public String subscribeToProduct(String userId, SubscribeProductRequest request) {
        // Validate product
        LendingProduct product = productRepository.findByProductId(request.getProductId())
            .orElseThrow(() -> new RuntimeException("Product not found"));
        
        if (!product.getIsActive()) {
            throw new RuntimeException("Product is not active");
        }
        
        // Check amount limits
        if (request.getAmount().compareTo(product.getMinAmount()) < 0) {
            throw new RuntimeException("Amount below minimum");
        }
        
        if (product.getMaxAmount() != null && request.getAmount().compareTo(product.getMaxAmount()) > 0) {
            throw new RuntimeException("Amount exceeds maximum");
        }
        
        // Check capacity
        BigDecimal currentTotal = positionRepository.getTotalAmountByProduct(product.getProductId());
        if (currentTotal == null) currentTotal = BigDecimal.ZERO;
        
        if (product.getTotalCap() != null && 
            currentTotal.add(request.getAmount()).compareTo(product.getTotalCap()) > 0) {
            throw new RuntimeException("Product capacity exceeded");
        }
        
        // Check user balance
        if (!hasUserBalance(userId, product.getAsset(), request.getAmount())) {
            throw new RuntimeException("Insufficient balance");
        }
        
        // Create position
        UserPosition position = new UserPosition();
        position.setPositionId(generatePositionId());
        position.setUserId(userId);
        position.setProductId(product.getProductId());
        position.setPrincipal(request.getAmount());
        position.setCurrentAmount(request.getAmount());
        position.setInterestRate(product.getInterestRate());
        position.setAccruedInterest(BigDecimal.ZERO);
        position.setTotalEarnings(BigDecimal.ZERO);
        position.setStartDate(LocalDateTime.now());
        position.setLastInterestDate(LocalDateTime.now());
        position.setIsActive(true);
        position.setIsAutoRenew(request.getAutoRenew());
        position.setCreatedAt(LocalDateTime.now());
        position.setUpdatedAt(LocalDateTime.now());
        
        if (product.getDuration() != null && product.getDuration() > 0) {
            position.setEndDate(LocalDateTime.now().plusDays(product.getDuration()));
        }
        
        positionRepository.save(position);
        
        // Update product current amount
        product.setCurrentAmount(currentTotal.add(request.getAmount()));
        productRepository.save(product);
        
        // Lock user funds
        lockUserFunds(userId, product.getAsset(), request.getAmount());
        
        // Publish event
        publishEvent("position.created", position);
        
        logger.info("User {} subscribed to product {} with amount {}", 
                   userId, product.getProductId(), request.getAmount());
        
        return position.getPositionId();
    }
    
    public void redeemPosition(String userId, String positionId, BigDecimal amount) {
        UserPosition position = positionRepository.findByPositionId(positionId)
            .orElseThrow(() -> new RuntimeException("Position not found"));
        
        if (!position.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized access");
        }
        
        if (!position.getIsActive()) {
            throw new RuntimeException("Position is not active");
        }
        
        LendingProduct product = productRepository.findByProductId(position.getProductId())
            .orElseThrow(() -> new RuntimeException("Product not found"));
        
        // Check if flexible redemption is allowed
        if (!product.getIsFlexible() && position.getEndDate() != null && 
            LocalDateTime.now().isBefore(position.getEndDate())) {
            throw new RuntimeException("Early redemption not allowed");
        }
        
        // Calculate current value with accrued interest
        BigDecimal currentValue = interestService.calculateCurrentValue(position);
        
        if (amount == null || amount.compareTo(currentValue) >= 0) {
            // Full redemption
            amount = currentValue;
            position.setIsActive(false);
        } else {
            // Partial redemption
            if (amount.compareTo(position.getCurrentAmount()) > 0) {
                throw new RuntimeException("Redemption amount exceeds position value");
            }
            
            BigDecimal remainingAmount = currentValue.subtract(amount);
            position.setCurrentAmount(remainingAmount);
            position.setPrincipal(remainingAmount);
        }
        
        position.setUpdatedAt(LocalDateTime.now());
        positionRepository.save(position);
        
        // Update product current amount
        BigDecimal currentTotal = positionRepository.getTotalAmountByProduct(product.getProductId());
        product.setCurrentAmount(currentTotal);
        productRepository.save(product);
        
        // Release funds to user
        releaseUserFunds(userId, product.getAsset(), amount);
        
        // Publish event
        publishEvent("position.redeemed", position);
        
        logger.info("User {} redeemed position {} amount {}", userId, positionId, amount);
    }
    
    public String createLoan(String userId, LoanRequest request) {
        // Validate loan parameters
        if (!riskService.isLoanAllowed(userId, request)) {
            throw new RuntimeException("Loan not allowed due to risk assessment");
        }
        
        // Get current prices
        BigDecimal loanAssetPrice = priceService.getPrice(request.getLoanAsset());
        BigDecimal collateralAssetPrice = priceService.getPrice(request.getCollateralAsset());
        
        // Calculate LTV
        BigDecimal loanValue = request.getLoanAmount().multiply(loanAssetPrice);
        BigDecimal collateralValue = request.getCollateralAmount().multiply(collateralAssetPrice);
        BigDecimal ltv = loanValue.divide(collateralValue, 4, RoundingMode.HALF_UP);
        
        // Check LTV limits
        BigDecimal maxLtv = riskService.getMaxLtv(request.getLoanAsset(), request.getCollateralAsset());
        if (ltv.compareTo(maxLtv) > 0) {
            throw new RuntimeException("LTV exceeds maximum allowed");
        }
        
        // Check user collateral balance
        if (!hasUserBalance(userId, request.getCollateralAsset(), request.getCollateralAmount())) {
            throw new RuntimeException("Insufficient collateral balance");
        }
        
        // Create loan
        Loan loan = new Loan();
        loan.setLoanId(generateLoanId());
        loan.setUserId(userId);
        loan.setLoanAsset(request.getLoanAsset());
        loan.setLoanAmount(request.getLoanAmount());
        loan.setCollateralAsset(request.getCollateralAsset());
        loan.setCollateralAmount(request.getCollateralAmount());
        loan.setInterestRate(riskService.getLoanInterestRate(request.getLoanAsset(), ltv));
        loan.setLtv(ltv);
        loan.setLiquidationThreshold(riskService.getLiquidationThreshold(request.getCollateralAsset()));
        loan.setOutstandingAmount(request.getLoanAmount());
        loan.setAccruedInterest(BigDecimal.ZERO);
        loan.setStatus(LoanStatus.ACTIVE);
        loan.setCollateralStatus(CollateralStatus.ACTIVE);
        loan.setStartDate(LocalDateTime.now());
        loan.setLastInterestDate(LocalDateTime.now());
        loan.setCreatedAt(LocalDateTime.now());
        loan.setUpdatedAt(LocalDateTime.now());
        
        if (request.getTermDays() != null) {
            loan.setDueDate(LocalDateTime.now().plusDays(request.getTermDays()));
        }
        
        loanRepository.save(loan);
        
        // Lock collateral
        lockUserFunds(userId, request.getCollateralAsset(), request.getCollateralAmount());
        
        // Transfer loan amount to user
        releaseUserFunds(userId, request.getLoanAsset(), request.getLoanAmount());
        
        // Publish event
        publishEvent("loan.created", loan);
        
        logger.info("User {} created loan {} for {} {}", 
                   userId, loan.getLoanId(), request.getLoanAmount(), request.getLoanAsset());
        
        return loan.getLoanId();
    }
    
    public void repayLoan(String userId, RepaymentRequest request) {
        Loan loan = loanRepository.findByLoanId(request.getLoanId())
            .orElseThrow(() -> new RuntimeException("Loan not found"));
        
        if (!loan.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized access");
        }
        
        if (loan.getStatus() != LoanStatus.ACTIVE) {
            throw new RuntimeException("Loan is not active");
        }
        
        // Calculate current outstanding amount with interest
        BigDecimal currentOutstanding = interestService.calculateLoanOutstanding(loan);
        
        BigDecimal repaymentAmount = request.getAmount();
        if (request.getIsFullRepayment() || repaymentAmount.compareTo(currentOutstanding) >= 0) {
            // Full repayment
            repaymentAmount = currentOutstanding;
            loan.setStatus(LoanStatus.REPAID);
            loan.setRepaidDate(LocalDateTime.now());
            loan.setCollateralStatus(CollateralStatus.RELEASED);
            
            // Release collateral
            releaseUserFunds(userId, loan.getCollateralAsset(), loan.getCollateralAmount());
        } else {
            // Partial repayment
            loan.setOutstandingAmount(currentOutstanding.subtract(repaymentAmount));
        }
        
        // Check user balance for repayment
        if (!hasUserBalance(userId, loan.getLoanAsset(), repaymentAmount)) {
            throw new RuntimeException("Insufficient balance for repayment");
        }
        
        // Lock repayment funds
        lockUserFunds(userId, loan.getLoanAsset(), repaymentAmount);
        
        loan.setUpdatedAt(LocalDateTime.now());
        loanRepository.save(loan);
        
        // Publish event
        publishEvent("loan.repaid", loan);
        
        logger.info("User {} repaid loan {} amount {}", userId, request.getLoanId(), repaymentAmount);
    }
    
    public List<UserPosition> getUserPositions(String userId) {
        return positionRepository.findByUserIdAndIsActiveTrue(userId);
    }
    
    public List<Loan> getUserLoans(String userId) {
        return loanRepository.findByUserIdAndStatus(userId, LoanStatus.ACTIVE);
    }
    
    // Helper methods
    private boolean hasUserBalance(String userId, String asset, BigDecimal amount) {
        // Check user balance via balance service
        try (Jedis jedis = jedisPool.getResource()) {
            String balanceKey = "balance:" + userId + ":" + asset;
            String balanceStr = jedis.get(balanceKey);
            if (balanceStr != null) {
                BigDecimal balance = new BigDecimal(balanceStr);
                return balance.compareTo(amount) >= 0;
            }
        }
        return false;
    }
    
    private void lockUserFunds(String userId, String asset, BigDecimal amount) {
        // Lock user funds via balance service
        try (Jedis jedis = jedisPool.getResource()) {
            String balanceKey = "balance:" + userId + ":" + asset;
            String lockedKey = "locked:" + userId + ":" + asset;
            
            // Atomic operation to lock funds
            jedis.watch(balanceKey);
            String balanceStr = jedis.get(balanceKey);
            if (balanceStr != null) {
                BigDecimal balance = new BigDecimal(balanceStr);
                if (balance.compareTo(amount) >= 0) {
                    jedis.multi();
                    jedis.decrByFloat(balanceKey, amount.doubleValue());
                    jedis.incrByFloat(lockedKey, amount.doubleValue());
                    jedis.exec();
                }
            }
        }
    }
    
    private void releaseUserFunds(String userId, String asset, BigDecimal amount) {
        // Release funds to user via balance service
        try (Jedis jedis = jedisPool.getResource()) {
            String balanceKey = "balance:" + userId + ":" + asset;
            jedis.incrByFloat(balanceKey, amount.doubleValue());
        }
    }
    
    private String generatePositionId() {
        return "POS_" + System.currentTimeMillis() + "_" + UUID.randomUUID().toString().substring(0, 8);
    }
    
    private String generateLoanId() {
        return "LOAN_" + System.currentTimeMillis() + "_" + UUID.randomUUID().toString().substring(0, 8);
    }
    
    private void publishEvent(String eventType, Object data) {
        try {
            String message = objectMapper.writeValueAsString(Map.of(
                "eventType", eventType,
                "data", data,
                "timestamp", LocalDateTime.now()
            ));
            kafkaTemplate.send("lending-events", message);
        } catch (Exception e) {
            logger.error("Failed to publish event", e);
        }
    }
}

@Service
class InterestCalculationService {
    private static final Logger logger = LoggerFactory.getLogger(InterestCalculationService.class);
    
    public BigDecimal calculateCurrentValue(UserPosition position) {
        LocalDateTime now = LocalDateTime.now();
        long daysBetween = ChronoUnit.DAYS.between(position.getLastInterestDate(), now);
        
        if (daysBetween <= 0) {
            return position.getCurrentAmount();
        }
        
        BigDecimal dailyRate = position.getInterestRate().divide(BigDecimal.valueOf(365), 10, RoundingMode.HALF_UP);
        BigDecimal interest = position.getCurrentAmount()
            .multiply(dailyRate)
            .multiply(BigDecimal.valueOf(daysBetween));
        
        return position.getCurrentAmount().add(interest);
    }
    
    public BigDecimal calculateLoanOutstanding(Loan loan) {
        LocalDateTime now = LocalDateTime.now();
        long daysBetween = ChronoUnit.DAYS.between(loan.getLastInterestDate(), now);
        
        if (daysBetween <= 0) {
            return loan.getOutstandingAmount();
        }
        
        BigDecimal dailyRate = loan.getInterestRate().divide(BigDecimal.valueOf(365), 10, RoundingMode.HALF_UP);
        BigDecimal interest = loan.getOutstandingAmount()
            .multiply(dailyRate)
            .multiply(BigDecimal.valueOf(daysBetween));
        
        return loan.getOutstandingAmount().add(interest);
    }
    
    @Scheduled(fixedRate = 3600000) // Run every hour
    public void updateAccruedInterest() {
        logger.info("Starting accrued interest update");
        
        // Update positions
        List<UserPosition> activePositions = positionRepository.findByUserIdAndIsActiveTrue("");
        for (UserPosition position : activePositions) {
            BigDecimal currentValue = calculateCurrentValue(position);
            BigDecimal newInterest = currentValue.subtract(position.getCurrentAmount());
            
            if (newInterest.compareTo(BigDecimal.ZERO) > 0) {
                position.setAccruedInterest(position.getAccruedInterest().add(newInterest));
                position.setCurrentAmount(currentValue);
                position.setTotalEarnings(position.getTotalEarnings().add(newInterest));
                position.setLastInterestDate(LocalDateTime.now());
                position.setUpdatedAt(LocalDateTime.now());
                
                positionRepository.save(position);
            }
        }
        
        // Update loans
        List<Loan> activeLoans = loanRepository.findByStatus(LoanStatus.ACTIVE);
        for (Loan loan : activeLoans) {
            BigDecimal currentOutstanding = calculateLoanOutstanding(loan);
            BigDecimal newInterest = currentOutstanding.subtract(loan.getOutstandingAmount());
            
            if (newInterest.compareTo(BigDecimal.ZERO) > 0) {
                loan.setAccruedInterest(loan.getAccruedInterest().add(newInterest));
                loan.setOutstandingAmount(currentOutstanding);
                loan.setLastInterestDate(LocalDateTime.now());
                loan.setUpdatedAt(LocalDateTime.now());
                
                loanRepository.save(loan);
            }
        }
        
        logger.info("Completed accrued interest update");
    }
}

@Service
class RiskManagementService {
    private static final Logger logger = LoggerFactory.getLogger(RiskManagementService.class);
    
    @Autowired
    private LoanRepository loanRepository;
    
    @Autowired
    private PriceService priceService;
    
    private final Map<String, BigDecimal> maxLtvMap = new ConcurrentHashMap<>();
    private final Map<String, BigDecimal> liquidationThresholds = new ConcurrentHashMap<>();
    
    public RiskManagementService() {
        // Initialize risk parameters
        maxLtvMap.put("BTC", new BigDecimal("0.65"));
        maxLtvMap.put("ETH", new BigDecimal("0.70"));
        maxLtvMap.put("BNB", new BigDecimal("0.60"));
        maxLtvMap.put("USDT", new BigDecimal("0.90"));
        maxLtvMap.put("USDC", new BigDecimal("0.90"));
        
        liquidationThresholds.put("BTC", new BigDecimal("0.80"));
        liquidationThresholds.put("ETH", new BigDecimal("0.85"));
        liquidationThresholds.put("BNB", new BigDecimal("0.75"));
        liquidationThresholds.put("USDT", new BigDecimal("0.95"));
        liquidationThresholds.put("USDC", new BigDecimal("0.95"));
    }
    
    public boolean isLoanAllowed(String userId, LoanRequest request) {
        // Check user's total outstanding loans
        BigDecimal totalOutstanding = loanRepository.getTotalOutstandingByUser(userId);
        if (totalOutstanding == null) totalOutstanding = BigDecimal.ZERO;
        
        // Maximum loan limit per user (example: $1M)
        BigDecimal maxLoanLimit = new BigDecimal("1000000");
        BigDecimal loanValue = request.getLoanAmount().multiply(priceService.getPrice(request.getLoanAsset()));
        
        return totalOutstanding.add(loanValue).compareTo(maxLoanLimit) <= 0;
    }
    
    public BigDecimal getMaxLtv(String loanAsset, String collateralAsset) {
        return maxLtvMap.getOrDefault(collateralAsset, new BigDecimal("0.50"));
    }
    
    public BigDecimal getLiquidationThreshold(String collateralAsset) {
        return liquidationThresholds.getOrDefault(collateralAsset, new BigDecimal("0.75"));
    }
    
    public BigDecimal getLoanInterestRate(String loanAsset, BigDecimal ltv) {
        // Base rate + risk premium based on LTV
        BigDecimal baseRate = new BigDecimal("0.05"); // 5% base rate
        BigDecimal riskPremium = ltv.multiply(new BigDecimal("0.10")); // Up to 10% risk premium
        
        return baseRate.add(riskPremium);
    }
    
    @Scheduled(fixedRate = 300000) // Run every 5 minutes
    public void checkLiquidations() {
        logger.info("Starting liquidation check");
        
        List<Loan> loansForLiquidation = loanRepository.findLoansForLiquidation();
        
        for (Loan loan : loansForLiquidation) {
            try {
                // Recalculate current LTV
                BigDecimal loanValue = loan.getOutstandingAmount().multiply(priceService.getPrice(loan.getLoanAsset()));
                BigDecimal collateralValue = loan.getCollateralAmount().multiply(priceService.getPrice(loan.getCollateralAsset()));
                BigDecimal currentLtv = loanValue.divide(collateralValue, 4, RoundingMode.HALF_UP);
                
                if (currentLtv.compareTo(loan.getLiquidationThreshold()) >= 0) {
                    liquidateLoan(loan);
                }
            } catch (Exception e) {
                logger.error("Error checking liquidation for loan {}", loan.getLoanId(), e);
            }
        }
        
        logger.info("Completed liquidation check");
    }
    
    private void liquidateLoan(Loan loan) {
        logger.info("Liquidating loan {}", loan.getLoanId());
        
        loan.setStatus(LoanStatus.LIQUIDATED);
        loan.setCollateralStatus(CollateralStatus.LIQUIDATED);
        loan.setLiquidationDate(LocalDateTime.now());
        loan.setUpdatedAt(LocalDateTime.now());
        
        loanRepository.save(loan);
        
        // Trigger collateral liquidation process
        // This would involve selling the collateral to repay the loan
    }
}

@Service
class PriceService {
    private final Map<String, BigDecimal> priceCache = new ConcurrentHashMap<>();
    
    public BigDecimal getPrice(String asset) {
        // In a real implementation, this would fetch from price feeds
        return priceCache.getOrDefault(asset, BigDecimal.ONE);
    }
    
    @Scheduled(fixedRate = 10000) // Update every 10 seconds
    public void updatePrices() {
        // Mock price updates
        priceCache.put("BTC", new BigDecimal("45000"));
        priceCache.put("ETH", new BigDecimal("3000"));
        priceCache.put("BNB", new BigDecimal("300"));
        priceCache.put("USDT", BigDecimal.ONE);
        priceCache.put("USDC", BigDecimal.ONE);
    }
}

// Controllers
@RestController
@RequestMapping("/api/v1/lending")
class LendingController {
    
    @Autowired
    private LendingService lendingService;
    
    @GetMapping("/products")
    public List<LendingProduct> getProducts(
            @RequestParam(required = false) ProductType type,
            @RequestParam(required = false) String asset) {
        
        if (type != null) {
            return lendingService.getProductsByType(type);
        } else if (asset != null) {
            return lendingService.getProductsByAsset(asset);
        } else {
            return lendingService.getAvailableProducts();
        }
    }
    
    @PostMapping("/subscribe")
    public Map<String, String> subscribeToProduct(
            @RequestHeader("User-Id") String userId,
            @RequestBody SubscribeProductRequest request) {
        
        String positionId = lendingService.subscribeToProduct(userId, request);
        return Map.of("positionId", positionId);
    }
    
    @PostMapping("/redeem")
    public Map<String, String> redeemPosition(
            @RequestHeader("User-Id") String userId,
            @RequestParam String positionId,
            @RequestParam(required = false) BigDecimal amount) {
        
        lendingService.redeemPosition(userId, positionId, amount);
        return Map.of("status", "success");
    }
    
    @GetMapping("/positions")
    public List<UserPosition> getUserPositions(@RequestHeader("User-Id") String userId) {
        return lendingService.getUserPositions(userId);
    }
    
    @PostMapping("/loans")
    public Map<String, String> createLoan(
            @RequestHeader("User-Id") String userId,
            @RequestBody LoanRequest request) {
        
        String loanId = lendingService.createLoan(userId, request);
        return Map.of("loanId", loanId);
    }
    
    @PostMapping("/loans/repay")
    public Map<String, String> repayLoan(
            @RequestHeader("User-Id") String userId,
            @RequestBody RepaymentRequest request) {
        
        lendingService.repayLoan(userId, request);
        return Map.of("status", "success");
    }
    
    @GetMapping("/loans")
    public List<Loan> getUserLoans(@RequestHeader("User-Id") String userId) {
        return lendingService.getUserLoans(userId);
    }
}

// Configuration
@Configuration
class LendingConfiguration {
    
    @Bean
    public JedisPool jedisPool() {
        return new JedisPool("localhost", 6379);
    }
    
    @Bean
    public KafkaTemplate<String, String> kafkaTemplate() {
        // Kafka configuration
        return new KafkaTemplate<>(null); // Simplified for example
    }
}