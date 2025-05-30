#include <iostream>
#include <memory>
#include <thread>
#include <vector>
#include <queue>
#include <map>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <chrono>
#include <algorithm>
#include <unordered_map>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace std::chrono;

// Order types and structures
enum class OrderType {
    MARKET,
    LIMIT,
    STOP_LOSS,
    STOP_LIMIT,
    TAKE_PROFIT,
    TAKE_PROFIT_LIMIT,
    TRAILING_STOP,
    ICEBERG,
    OCO,  // One-Cancels-Other
    BRACKET
};

enum class OrderSide {
    BUY,
    SELL
};

enum class OrderStatus {
    NEW,
    PARTIALLY_FILLED,
    FILLED,
    CANCELED,
    REJECTED,
    EXPIRED
};

enum class TimeInForce {
    GTC,  // Good Till Canceled
    IOC,  // Immediate or Cancel
    FOK,  // Fill or Kill
    GTD   // Good Till Date
};

struct Order {
    uint64_t id;
    std::string symbol;
    OrderSide side;
    OrderType type;
    TimeInForce timeInForce;
    double quantity;
    double price;
    double stopPrice;
    double filledQuantity;
    OrderStatus status;
    uint64_t timestamp;
    std::string clientOrderId;
    uint64_t userId;
    double icebergQty;
    uint64_t expireTime;
    
    Order(uint64_t id, const std::string& symbol, OrderSide side, OrderType type,
          double quantity, double price = 0.0, TimeInForce tif = TimeInForce::GTC)
        : id(id), symbol(symbol), side(side), type(type), timeInForce(tif),
          quantity(quantity), price(price), stopPrice(0.0), filledQuantity(0.0),
          status(OrderStatus::NEW), timestamp(duration_cast<milliseconds>(
              system_clock::now().time_since_epoch()).count()),
          userId(0), icebergQty(0.0), expireTime(0) {}
};

struct Trade {
    uint64_t id;
    std::string symbol;
    uint64_t buyOrderId;
    uint64_t sellOrderId;
    uint64_t buyerId;
    uint64_t sellerId;
    double price;
    double quantity;
    uint64_t timestamp;
    double fee;
    std::string feeAsset;
};

// Advanced order book with multiple price levels
class OrderBook {
private:
    std::map<double, std::queue<std::shared_ptr<Order>>, std::greater<double>> bids;
    std::map<double, std::queue<std::shared_ptr<Order>>, std::less<double>> asks;
    std::mutex bookMutex;
    std::string symbol;
    
public:
    OrderBook(const std::string& symbol) : symbol(symbol) {}
    
    void addOrder(std::shared_ptr<Order> order) {
        std::lock_guard<std::mutex> lock(bookMutex);
        
        if (order->side == OrderSide::BUY) {
            bids[order->price].push(order);
        } else {
            asks[order->price].push(order);
        }
    }
    
    void removeOrder(uint64_t orderId) {
        std::lock_guard<std::mutex> lock(bookMutex);
        // Implementation for order removal
    }
    
    std::vector<Trade> matchOrders() {
        std::lock_guard<std::mutex> lock(bookMutex);
        std::vector<Trade> trades;
        
        while (!bids.empty() && !asks.empty()) {
            auto& topBid = bids.rbegin()->second.front();
            auto& topAsk = asks.begin()->second.front();
            
            if (topBid->price >= topAsk->price) {
                double tradePrice = topAsk->price;
                double tradeQuantity = std::min(
                    topBid->quantity - topBid->filledQuantity,
                    topAsk->quantity - topAsk->filledQuantity
                );
                
                Trade trade;
                trade.id = generateTradeId();
                trade.symbol = symbol;
                trade.buyOrderId = topBid->id;
                trade.sellOrderId = topAsk->id;
                trade.buyerId = topBid->userId;
                trade.sellerId = topAsk->userId;
                trade.price = tradePrice;
                trade.quantity = tradeQuantity;
                trade.timestamp = duration_cast<milliseconds>(
                    system_clock::now().time_since_epoch()).count();
                trade.fee = tradeQuantity * tradePrice * 0.001; // 0.1% fee
                trade.feeAsset = "USDT";
                
                trades.push_back(trade);
                
                topBid->filledQuantity += tradeQuantity;
                topAsk->filledQuantity += tradeQuantity;
                
                if (topBid->filledQuantity >= topBid->quantity) {
                    topBid->status = OrderStatus::FILLED;
                    bids.rbegin()->second.pop();
                    if (bids.rbegin()->second.empty()) {
                        bids.erase(std::prev(bids.end()));
                    }
                }
                
                if (topAsk->filledQuantity >= topAsk->quantity) {
                    topAsk->status = OrderStatus::FILLED;
                    asks.begin()->second.pop();
                    if (asks.begin()->second.empty()) {
                        asks.erase(asks.begin());
                    }
                }
            } else {
                break;
            }
        }
        
        return trades;
    }
    
    json getDepth(int limit = 20) {
        std::lock_guard<std::mutex> lock(bookMutex);
        json depth;
        json bidArray = json::array();
        json askArray = json::array();
        
        int count = 0;
        for (auto it = bids.rbegin(); it != bids.rend() && count < limit; ++it, ++count) {
            double totalQuantity = 0.0;
            auto tempQueue = it->second;
            while (!tempQueue.empty()) {
                totalQuantity += (tempQueue.front()->quantity - tempQueue.front()->filledQuantity);
                tempQueue.pop();
            }
            bidArray.push_back({std::to_string(it->first), std::to_string(totalQuantity)});
        }
        
        count = 0;
        for (auto it = asks.begin(); it != asks.end() && count < limit; ++it, ++count) {
            double totalQuantity = 0.0;
            auto tempQueue = it->second;
            while (!tempQueue.empty()) {
                totalQuantity += (tempQueue.front()->quantity - tempQueue.front()->filledQuantity);
                tempQueue.pop();
            }
            askArray.push_back({std::to_string(it->first), std::to_string(totalQuantity)});
        }
        
        depth["bids"] = bidArray;
        depth["asks"] = askArray;
        depth["lastUpdateId"] = duration_cast<milliseconds>(
            system_clock::now().time_since_epoch()).count();
        
        return depth;
    }
    
private:
    uint64_t generateTradeId() {
        static std::atomic<uint64_t> counter{1};
        return counter++;
    }
};

// High-performance matching engine
class MatchingEngine {
private:
    std::unordered_map<std::string, std::unique_ptr<OrderBook>> orderBooks;
    std::mutex engineMutex;
    std::atomic<bool> running{true};
    std::vector<std::thread> workerThreads;
    std::queue<std::shared_ptr<Order>> orderQueue;
    std::mutex queueMutex;
    std::condition_variable queueCondition;
    
public:
    MatchingEngine() {
        // Initialize order books for major trading pairs
        initializeOrderBooks();
        
        // Start worker threads
        for (int i = 0; i < std::thread::hardware_concurrency(); ++i) {
            workerThreads.emplace_back(&MatchingEngine::processOrders, this);
        }
    }
    
    ~MatchingEngine() {
        running = false;
        queueCondition.notify_all();
        for (auto& thread : workerThreads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
    }
    
    void submitOrder(std::shared_ptr<Order> order) {
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            orderQueue.push(order);
        }
        queueCondition.notify_one();
    }
    
    json getOrderBookDepth(const std::string& symbol, int limit = 20) {
        std::lock_guard<std::mutex> lock(engineMutex);
        auto it = orderBooks.find(symbol);
        if (it != orderBooks.end()) {
            return it->second->getDepth(limit);
        }
        return json::object();
    }
    
    void addTradingPair(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(engineMutex);
        orderBooks[symbol] = std::make_unique<OrderBook>(symbol);
    }
    
private:
    void initializeOrderBooks() {
        // Major trading pairs similar to Binance, KuCoin, OKX, Bybit
        std::vector<std::string> symbols = {
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT",
            "XRPUSDT", "LTCUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
            "UNIUSDT", "VETUSDT", "FILUSDT", "TRXUSDT", "ETCUSDT",
            "EOSUSDT", "XMRUSDT", "AAVEUSDT", "ATOMUSDT", "MKRUSDT",
            "COMPUSDT", "YFIUSDT", "SUSHIUSDT", "SNXUSDT", "CRVUSDT",
            "BTCBUSD", "ETHBUSD", "BNBBUSD", "ADABUSD", "DOTBUSD"
        };
        
        for (const auto& symbol : symbols) {
            orderBooks[symbol] = std::make_unique<OrderBook>(symbol);
        }
    }
    
    void processOrders() {
        while (running) {
            std::unique_lock<std::mutex> lock(queueMutex);
            queueCondition.wait(lock, [this] { return !orderQueue.empty() || !running; });
            
            if (!running) break;
            
            auto order = orderQueue.front();
            orderQueue.pop();
            lock.unlock();
            
            processOrder(order);
        }
    }
    
    void processOrder(std::shared_ptr<Order> order) {
        std::lock_guard<std::mutex> lock(engineMutex);
        auto it = orderBooks.find(order->symbol);
        if (it != orderBooks.end()) {
            // Handle different order types
            switch (order->type) {
                case OrderType::MARKET:
                    processMarketOrder(order, it->second.get());
                    break;
                case OrderType::LIMIT:
                    processLimitOrder(order, it->second.get());
                    break;
                case OrderType::STOP_LOSS:
                case OrderType::STOP_LIMIT:
                    processStopOrder(order, it->second.get());
                    break;
                case OrderType::ICEBERG:
                    processIcebergOrder(order, it->second.get());
                    break;
                default:
                    processLimitOrder(order, it->second.get());
                    break;
            }
        }
    }
    
    void processMarketOrder(std::shared_ptr<Order> order, OrderBook* book) {
        // Market order implementation
        auto trades = book->matchOrders();
        broadcastTrades(trades);
    }
    
    void processLimitOrder(std::shared_ptr<Order> order, OrderBook* book) {
        book->addOrder(order);
        auto trades = book->matchOrders();
        broadcastTrades(trades);
    }
    
    void processStopOrder(std::shared_ptr<Order> order, OrderBook* book) {
        // Stop order implementation
        // Check if stop price is triggered
        book->addOrder(order);
    }
    
    void processIcebergOrder(std::shared_ptr<Order> order, OrderBook* book) {
        // Iceberg order implementation
        // Only show small portion of the order
        if (order->icebergQty > 0 && order->icebergQty < order->quantity) {
            auto visibleOrder = std::make_shared<Order>(*order);
            visibleOrder->quantity = order->icebergQty;
            book->addOrder(visibleOrder);
        } else {
            book->addOrder(order);
        }
    }
    
    void broadcastTrades(const std::vector<Trade>& trades) {
        for (const auto& trade : trades) {
            json tradeData;
            tradeData["id"] = trade.id;
            tradeData["symbol"] = trade.symbol;
            tradeData["price"] = std::to_string(trade.price);
            tradeData["quantity"] = std::to_string(trade.quantity);
            tradeData["timestamp"] = trade.timestamp;
            tradeData["buyOrderId"] = trade.buyOrderId;
            tradeData["sellOrderId"] = trade.sellOrderId;
            
            // Broadcast to WebSocket clients
            broadcastToClients(tradeData);
        }
    }
    
    void broadcastToClients(const json& data) {
        // WebSocket broadcast implementation
        std::cout << "Broadcasting trade: " << data.dump() << std::endl;
    }
};

// WebSocket server for real-time data
class WebSocketServer {
private:
    websocketpp::server<websocketpp::config::asio> server;
    std::thread serverThread;
    MatchingEngine* engine;
    
public:
    WebSocketServer(MatchingEngine* engine) : engine(engine) {
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
            
            if (request["method"] == "depth") {
                std::string symbol = request["params"]["symbol"];
                int limit = request["params"].value("limit", 20);
                response = engine->getOrderBookDepth(symbol, limit);
                response["id"] = request["id"];
            }
            
            server.get_alog().write(websocketpp::log::alevel::app, response.dump());
            server.send(hdl, response.dump(), websocketpp::frame::opcode::text);
        } catch (const std::exception& e) {
            server.get_elog().write(websocketpp::log::elevel::rerror, 
                                   "Message handling error: " + std::string(e.what()));
        }
    }
};

// Risk management integration
class RiskManager {
private:
    std::unordered_map<uint64_t, double> userBalances;
    std::unordered_map<uint64_t, double> userExposure;
    std::mutex riskMutex;
    
public:
    bool validateOrder(const Order& order) {
        std::lock_guard<std::mutex> lock(riskMutex);
        
        // Check user balance
        auto balanceIt = userBalances.find(order.userId);
        if (balanceIt == userBalances.end() || balanceIt->second < order.quantity * order.price) {
            return false;
        }
        
        // Check position limits
        auto exposureIt = userExposure.find(order.userId);
        if (exposureIt != userExposure.end()) {
            double newExposure = exposureIt->second + (order.quantity * order.price);
            if (newExposure > getMaxExposure(order.userId)) {
                return false;
            }
        }
        
        return true;
    }
    
    void updateUserBalance(uint64_t userId, double balance) {
        std::lock_guard<std::mutex> lock(riskMutex);
        userBalances[userId] = balance;
    }
    
private:
    double getMaxExposure(uint64_t userId) {
        // Return maximum exposure based on user tier
        return 1000000.0; // $1M default
    }
};

int main() {
    std::cout << "Starting TigerEx Matching Engine..." << std::endl;
    
    // Initialize components
    auto engine = std::make_unique<MatchingEngine>();
    auto riskManager = std::make_unique<RiskManager>();
    auto wsServer = std::make_unique<WebSocketServer>(engine.get());
    
    // Start WebSocket server
    wsServer->start(8080);
    
    std::cout << "TigerEx Matching Engine started successfully!" << std::endl;
    std::cout << "WebSocket server listening on port 8080" << std::endl;
    
    // Keep the main thread alive
    std::this_thread::sleep_for(std::chrono::hours(24));
    
    return 0;
}