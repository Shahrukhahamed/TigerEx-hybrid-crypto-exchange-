#include <iostream>
#include <memory>
#include <thread>
#include <vector>
#include <queue>
#include <map>
#include <unordered_map>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <chrono>
#include <algorithm>
#include <cmath>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <nlohmann/json.hpp>
#include <curl/curl.h>

using json = nlohmann::json;
using namespace std::chrono;

// Futures contract specifications
struct FuturesContract {
    std::string symbol;           // BTCUSDT_PERP, ETHUSDT_240329
    std::string baseAsset;        // BTC, ETH
    std::string quoteAsset;       // USDT
    std::string contractType;     // PERPETUAL, QUARTERLY, MONTHLY
    double contractSize;          // 1.0 for crypto futures
    double tickSize;              // 0.01
    double minQuantity;           // 0.001
    double maxQuantity;           // 1000000
    double maxLeverage;           // 125x
    double maintenanceMarginRate; // 0.5%
    double initialMarginRate;     // 1.0%
    uint64_t expiryTime;          // 0 for perpetual
    bool isActive;
    double fundingRate;           // Current funding rate
    uint64_t nextFundingTime;     // Next funding time
    double markPrice;             // Mark price for liquidation
    double indexPrice;            // Index price from spot markets
};

// Position management
struct FuturesPosition {
    uint64_t userId;
    std::string symbol;
    std::string side;             // LONG, SHORT
    double size;                  // Position size
    double entryPrice;            // Average entry price
    double markPrice;             // Current mark price
    double liquidationPrice;      // Liquidation price
    double unrealizedPnl;         // Unrealized P&L
    double realizedPnl;           // Realized P&L
    double marginUsed;            // Margin used for position
    double maintenanceMargin;     // Maintenance margin requirement
    double leverage;              // Position leverage
    std::string marginType;       // ISOLATED, CROSS
    uint64_t createdAt;
    uint64_t updatedAt;
};

// Order types specific to futures
enum class FuturesOrderType {
    MARKET,
    LIMIT,
    STOP,
    STOP_MARKET,
    TAKE_PROFIT,
    TAKE_PROFIT_MARKET,
    TRAILING_STOP_MARKET
};

// Advanced order for futures
struct FuturesOrder {
    uint64_t id;
    uint64_t userId;
    std::string symbol;
    std::string side;             // BUY, SELL
    FuturesOrderType type;
    std::string positionSide;     // LONG, SHORT, BOTH
    double quantity;
    double price;
    double stopPrice;
    double activationPrice;       // For trailing stop
    double callbackRate;          // For trailing stop
    bool reduceOnly;              // Close position only
    bool closePosition;           // Close entire position
    std::string timeInForce;      // GTC, IOC, FOK, GTX
    std::string workingType;      // MARK_PRICE, CONTRACT_PRICE
    double filledQuantity;
    double avgFillPrice;
    std::string status;           // NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED
    uint64_t createdAt;
    uint64_t updatedAt;
};

// Margin and risk management
struct MarginAccount {
    uint64_t userId;
    double totalWalletBalance;    // Total balance
    double totalUnrealizedPnl;    // Total unrealized P&L
    double totalMarginBalance;    // Wallet balance + unrealized P&L
    double totalPositionInitialMargin; // Initial margin for positions
    double totalOpenOrderInitialMargin; // Initial margin for open orders
    double totalCrossWalletBalance;     // Cross wallet balance
    double totalCrossUnPnl;            // Cross unrealized P&L
    double availableBalance;           // Available for new positions
    double maxWithdrawAmount;          // Maximum withdrawable amount
    std::vector<FuturesPosition> positions;
    std::vector<FuturesOrder> openOrders;
};

// Liquidation engine
class LiquidationEngine {
private:
    std::mutex liquidationMutex;
    std::queue<FuturesPosition> liquidationQueue;
    std::condition_variable liquidationCondition;
    std::atomic<bool> running{true};
    std::thread liquidationThread;

public:
    LiquidationEngine() {
        liquidationThread = std::thread(&LiquidationEngine::processLiquidations, this);
    }

    ~LiquidationEngine() {
        running = false;
        liquidationCondition.notify_all();
        if (liquidationThread.joinable()) {
            liquidationThread.join();
        }
    }

    void addToLiquidationQueue(const FuturesPosition& position) {
        {
            std::lock_guard<std::mutex> lock(liquidationMutex);
            liquidationQueue.push(position);
        }
        liquidationCondition.notify_one();
    }

private:
    void processLiquidations() {
        while (running) {
            std::unique_lock<std::mutex> lock(liquidationMutex);
            liquidationCondition.wait(lock, [this] { 
                return !liquidationQueue.empty() || !running; 
            });

            if (!running) break;

            auto position = liquidationQueue.front();
            liquidationQueue.pop();
            lock.unlock();

            executeLiquidation(position);
        }
    }

    void executeLiquidation(const FuturesPosition& position) {
        std::cout << "Executing liquidation for user " << position.userId 
                  << " symbol " << position.symbol 
                  << " size " << position.size << std::endl;

        // Create liquidation order
        FuturesOrder liquidationOrder;
        liquidationOrder.userId = position.userId;
        liquidationOrder.symbol = position.symbol;
        liquidationOrder.side = (position.side == "LONG") ? "SELL" : "BUY";
        liquidationOrder.type = FuturesOrderType::MARKET;
        liquidationOrder.quantity = std::abs(position.size);
        liquidationOrder.reduceOnly = true;
        liquidationOrder.status = "NEW";
        liquidationOrder.createdAt = duration_cast<milliseconds>(
            system_clock::now().time_since_epoch()).count();

        // Send to matching engine for execution
        sendLiquidationOrder(liquidationOrder);
    }

    void sendLiquidationOrder(const FuturesOrder& order) {
        // Implementation to send order to matching engine
        // This would typically use message queue or direct API call
    }
};

// Funding rate calculation
class FundingRateCalculator {
private:
    std::unordered_map<std::string, double> fundingRates;
    std::unordered_map<std::string, std::vector<double>> priceHistory;
    std::mutex calculationMutex;

public:
    double calculateFundingRate(const std::string& symbol, 
                               double markPrice, 
                               double indexPrice) {
        std::lock_guard<std::mutex> lock(calculationMutex);
        
        // Premium calculation
        double premium = (markPrice - indexPrice) / indexPrice;
        
        // Interest rate (typically 0.01% for crypto)
        double interestRate = 0.0001;
        
        // Funding rate = Premium + clamp(Interest Rate - Premium, -0.05%, 0.05%)
        double clampedValue = std::max(-0.0005, std::min(0.0005, interestRate - premium));
        double fundingRate = premium + clampedValue;
        
        // Store for historical tracking
        fundingRates[symbol] = fundingRate;
        
        return fundingRate;
    }

    double getFundingRate(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(calculationMutex);
        auto it = fundingRates.find(symbol);
        return (it != fundingRates.end()) ? it->second : 0.0;
    }
};

// Mark price calculation
class MarkPriceCalculator {
private:
    std::unordered_map<std::string, double> markPrices;
    std::unordered_map<std::string, double> indexPrices;
    std::mutex priceMutex;

public:
    double calculateMarkPrice(const std::string& symbol, 
                             double indexPrice, 
                             double fundingRate,
                             uint64_t timeToFunding) {
        std::lock_guard<std::mutex> lock(priceMutex);
        
        // Mark Price = Index Price * (1 + Funding Rate * Time Factor)
        double timeFactor = static_cast<double>(timeToFunding) / (8 * 3600 * 1000); // 8 hours in ms
        double markPrice = indexPrice * (1 + fundingRate * timeFactor);
        
        markPrices[symbol] = markPrice;
        indexPrices[symbol] = indexPrice;
        
        return markPrice;
    }

    double getMarkPrice(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(priceMutex);
        auto it = markPrices.find(symbol);
        return (it != markPrices.end()) ? it->second : 0.0;
    }

    double getIndexPrice(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(priceMutex);
        auto it = indexPrices.find(symbol);
        return (it != indexPrices.end()) ? it->second : 0.0;
    }
};

// Position risk calculator
class PositionRiskCalculator {
public:
    static double calculateLiquidationPrice(const FuturesPosition& position,
                                           double maintenanceMarginRate,
                                           double walletBalance) {
        if (position.size == 0) return 0.0;

        double side = (position.side == "LONG") ? 1.0 : -1.0;
        double marginUsed = position.marginUsed;
        double unrealizedPnl = position.unrealizedPnl;
        
        // Liquidation Price = Entry Price - (Wallet Balance + Unrealized PnL - Maintenance Margin) / Position Size
        double liquidationPrice = position.entryPrice - side * 
            (walletBalance + unrealizedPnl - marginUsed * maintenanceMarginRate) / position.size;
        
        return liquidationPrice;
    }

    static double calculateUnrealizedPnl(const FuturesPosition& position, double markPrice) {
        if (position.size == 0) return 0.0;
        
        double side = (position.side == "LONG") ? 1.0 : -1.0;
        return side * position.size * (markPrice - position.entryPrice);
    }

    static double calculateMarginRatio(const FuturesPosition& position, 
                                     double markPrice,
                                     double walletBalance) {
        double unrealizedPnl = calculateUnrealizedPnl(position, markPrice);
        double marginBalance = walletBalance + unrealizedPnl;
        
        if (position.marginUsed == 0) return std::numeric_limits<double>::infinity();
        
        return marginBalance / position.marginUsed;
    }
};

// Main futures trading engine
class FuturesTradingEngine {
private:
    std::unordered_map<std::string, FuturesContract> contracts;
    std::unordered_map<uint64_t, MarginAccount> accounts;
    std::unordered_map<std::string, std::vector<FuturesPosition>> positions;
    std::unique_ptr<LiquidationEngine> liquidationEngine;
    std::unique_ptr<FundingRateCalculator> fundingCalculator;
    std::unique_ptr<MarkPriceCalculator> markPriceCalculator;
    std::mutex engineMutex;
    std::atomic<bool> running{true};

public:
    FuturesTradingEngine() {
        liquidationEngine = std::make_unique<LiquidationEngine>();
        fundingCalculator = std::make_unique<FundingRateCalculator>();
        markPriceCalculator = std::make_unique<MarkPriceCalculator>();
        
        initializeContracts();
        startBackgroundTasks();
    }

    void initializeContracts() {
        // Initialize popular futures contracts
        std::vector<std::string> symbols = {
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT",
            "XRPUSDT", "LTCUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT"
        };

        for (const auto& symbol : symbols) {
            FuturesContract contract;
            contract.symbol = symbol + "_PERP";
            contract.baseAsset = symbol.substr(0, symbol.find("USDT"));
            contract.quoteAsset = "USDT";
            contract.contractType = "PERPETUAL";
            contract.contractSize = 1.0;
            contract.tickSize = 0.01;
            contract.minQuantity = 0.001;
            contract.maxQuantity = 1000000.0;
            contract.maxLeverage = 125.0;
            contract.maintenanceMarginRate = 0.005; // 0.5%
            contract.initialMarginRate = 0.01;      // 1.0%
            contract.expiryTime = 0; // Perpetual
            contract.isActive = true;
            contract.fundingRate = 0.0001; // 0.01%
            contract.nextFundingTime = duration_cast<milliseconds>(
                system_clock::now().time_since_epoch()).count() + 8 * 3600 * 1000; // 8 hours

            contracts[contract.symbol] = contract;
        }
    }

    void startBackgroundTasks() {
        // Start funding rate updates
        std::thread([this]() {
            while (running) {
                updateFundingRates();
                std::this_thread::sleep_for(std::chrono::minutes(1));
            }
        }).detach();

        // Start mark price updates
        std::thread([this]() {
            while (running) {
                updateMarkPrices();
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        }).detach();

        // Start position monitoring
        std::thread([this]() {
            while (running) {
                monitorPositions();
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        }).detach();
    }

    void updateFundingRates() {
        for (auto& [symbol, contract] : contracts) {
            if (contract.contractType == "PERPETUAL") {
                double indexPrice = getIndexPrice(symbol);
                double markPrice = markPriceCalculator->getMarkPrice(symbol);
                
                if (indexPrice > 0 && markPrice > 0) {
                    double fundingRate = fundingCalculator->calculateFundingRate(
                        symbol, markPrice, indexPrice);
                    contract.fundingRate = fundingRate;
                }
            }
        }
    }

    void updateMarkPrices() {
        for (auto& [symbol, contract] : contracts) {
            double indexPrice = getIndexPrice(symbol);
            if (indexPrice > 0) {
                uint64_t currentTime = duration_cast<milliseconds>(
                    system_clock::now().time_since_epoch()).count();
                uint64_t timeToFunding = contract.nextFundingTime - currentTime;
                
                double markPrice = markPriceCalculator->calculateMarkPrice(
                    symbol, indexPrice, contract.fundingRate, timeToFunding);
                contract.markPrice = markPrice;
            }
        }
    }

    void monitorPositions() {
        std::lock_guard<std::mutex> lock(engineMutex);
        
        for (auto& [userId, account] : accounts) {
            for (auto& position : account.positions) {
                if (position.size == 0) continue;
                
                auto contractIt = contracts.find(position.symbol);
                if (contractIt == contracts.end()) continue;
                
                double markPrice = contractIt->second.markPrice;
                if (markPrice <= 0) continue;
                
                // Update unrealized PnL
                position.unrealizedPnl = PositionRiskCalculator::calculateUnrealizedPnl(
                    position, markPrice);
                
                // Calculate margin ratio
                double marginRatio = PositionRiskCalculator::calculateMarginRatio(
                    position, markPrice, account.totalWalletBalance);
                
                // Check for liquidation
                if (marginRatio <= contractIt->second.maintenanceMarginRate) {
                    liquidationEngine->addToLiquidationQueue(position);
                }
                
                // Update liquidation price
                position.liquidationPrice = PositionRiskCalculator::calculateLiquidationPrice(
                    position, contractIt->second.maintenanceMarginRate, 
                    account.totalWalletBalance);
            }
        }
    }

    double getIndexPrice(const std::string& symbol) {
        // In a real implementation, this would fetch from multiple spot exchanges
        // and calculate a weighted average
        return 50000.0; // Placeholder
    }

    bool placeOrder(const FuturesOrder& order) {
        std::lock_guard<std::mutex> lock(engineMutex);
        
        // Validate contract
        auto contractIt = contracts.find(order.symbol);
        if (contractIt == contracts.end() || !contractIt->second.isActive) {
            return false;
        }
        
        // Validate user account
        auto accountIt = accounts.find(order.userId);
        if (accountIt == accounts.end()) {
            return false;
        }
        
        // Risk checks
        if (!validateOrderRisk(order, contractIt->second, accountIt->second)) {
            return false;
        }
        
        // Send to matching engine
        return sendOrderToMatchingEngine(order);
    }

private:
    bool validateOrderRisk(const FuturesOrder& order, 
                          const FuturesContract& contract,
                          const MarginAccount& account) {
        // Check leverage limits
        double requiredMargin = order.quantity * order.price / contract.maxLeverage;
        if (requiredMargin > account.availableBalance) {
            return false;
        }
        
        // Check position limits
        double totalPositionValue = 0;
        for (const auto& position : account.positions) {
            totalPositionValue += std::abs(position.size * position.markPrice);
        }
        
        // Add new order value
        totalPositionValue += order.quantity * order.price;
        
        // Check against maximum position limit (example: $10M)
        if (totalPositionValue > 10000000.0) {
            return false;
        }
        
        return true;
    }

    bool sendOrderToMatchingEngine(const FuturesOrder& order) {
        // Implementation to send order to matching engine
        // This would use message queue or direct API call
        std::cout << "Sending futures order to matching engine: " 
                  << order.symbol << " " << order.side << " " 
                  << order.quantity << std::endl;
        return true;
    }
};

// WebSocket server for real-time futures data
class FuturesWebSocketServer {
private:
    websocketpp::server<websocketpp::config::asio> server;
    std::thread serverThread;
    FuturesTradingEngine* engine;

public:
    FuturesWebSocketServer(FuturesTradingEngine* engine) : engine(engine) {
        server.set_access_channels(websocketpp::log::alevel::all);
        server.clear_access_channels(websocketpp::log::alevel::frame_payload);
        server.init_asio();
        
        server.set_message_handler([this](websocketpp::connection_hdl hdl, 
                                         websocketpp::server<websocketpp::config::asio>::message_ptr msg) {
            handleMessage(hdl, msg);
        });
    }

    void start(uint16_t port) {
        server.listen(port);
        server.start_accept();
        
        serverThread = std::thread([this]() {
            server.run();
        });
    }

    void stop() {
        server.stop();
        if (serverThread.joinable()) {
            serverThread.join();
        }
    }

private:
    void handleMessage(websocketpp::connection_hdl hdl, 
                      websocketpp::server<websocketpp::config::asio>::message_ptr msg) {
        try {
            json request = json::parse(msg->get_payload());
            json response;
            
            if (request["method"] == "subscribe") {
                std::string channel = request["params"]["channel"];
                // Handle subscription logic
                response["result"] = "subscribed";
                response["channel"] = channel;
            }
            
            server.send(hdl, response.dump(), websocketpp::frame::opcode::text);
        } catch (const std::exception& e) {
            server.get_elog().write(websocketpp::log::elevel::rerror, 
                                   "Message handling error: " + std::string(e.what()));
        }
    }
};

int main() {
    std::cout << "Starting TigerEx USD-M Futures Trading Engine..." << std::endl;
    
    // Initialize components
    auto engine = std::make_unique<FuturesTradingEngine>();
    auto wsServer = std::make_unique<FuturesWebSocketServer>(engine.get());
    
    // Start WebSocket server
    wsServer->start(8085);
    
    std::cout << "TigerEx USD-M Futures Trading Engine started successfully!" << std::endl;
    std::cout << "WebSocket server listening on port 8085" << std::endl;
    
    // Keep the main thread alive
    std::this_thread::sleep_for(std::chrono::hours(24));
    
    return 0;
}