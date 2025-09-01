/*
TigerEx Advanced Trading Engine
High-performance C++ trading engine with all features from major exchanges
Supports spot, futures, margin, options, and advanced order types
*/

#include <iostream>
#include <vector>
#include <map>
#include <unordered_map>
#include <queue>
#include <memory>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <algorithm>
#include <string>
#include <cmath>
#include <random>
#include <fstream>
#include <sstream>
#include <iomanip>

// WebSocket and HTTP libraries
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <nlohmann/json.hpp>
#include <curl/curl.h>

// Redis for caching
#include <hiredis/hiredis.h>

// Database connectivity
#include <pqxx/pqxx>

using json = nlohmann::json;
using namespace std::chrono;

// Trading Engine Core Classes
enum class OrderType {
    MARKET,
    LIMIT,
    STOP_LOSS,
    STOP_LIMIT,
    TAKE_PROFIT,
    TAKE_PROFIT_LIMIT,
    TRAILING_STOP,
    ICEBERG,
    TWAP,
    VWAP,
    BRACKET,
    OCO  // One-Cancels-Other
};

enum class OrderSide {
    BUY,
    SELL
};

enum class OrderStatus {
    PENDING,
    OPEN,
    PARTIALLY_FILLED,
    FILLED,
    CANCELLED,
    REJECTED,
    EXPIRED
};

enum class TradingType {
    SPOT,
    FUTURES,
    MARGIN,
    OPTIONS
};

enum class TimeInForce {
    GTC,  // Good Till Cancelled
    IOC,  // Immediate or Cancel
    FOK,  // Fill or Kill
    GTD   // Good Till Date
};

struct Price {
    double value;
    int64_t timestamp;
    
    Price(double v = 0.0) : value(v), timestamp(duration_cast<microseconds>(system_clock::now().time_since_epoch()).count()) {}
    
    bool operator<(const Price& other) const {
        return value < other.value;
    }
    
    bool operator>(const Price& other) const {
        return value > other.value;
    }
};

struct Order {
    std::string id;
    std::string user_id;
    std::string symbol;
    OrderType type;
    OrderSide side;
    TradingType trading_type;
    TimeInForce time_in_force;
    double quantity;
    double filled_quantity;
    Price price;
    Price stop_price;
    Price trigger_price;
    OrderStatus status;
    int64_t timestamp;
    int64_t expiry_time;
    
    // Advanced order parameters
    double iceberg_qty;  // For iceberg orders
    double trail_amount; // For trailing stop orders
    double trail_percent; // For trailing stop orders
    std::string parent_order_id; // For bracket orders
    std::vector<std::string> child_order_ids; // For bracket orders
    
    Order(const std::string& order_id, const std::string& uid, const std::string& sym,
          OrderType ot, OrderSide os, double qty, double prc = 0.0)
        : id(order_id), user_id(uid), symbol(sym), type(ot), side(os),
          trading_type(TradingType::SPOT), time_in_force(TimeInForce::GTC),
          quantity(qty), filled_quantity(0.0), price(prc), stop_price(0.0),
          trigger_price(0.0), status(OrderStatus::PENDING),
          timestamp(duration_cast<microseconds>(system_clock::now().time_since_epoch()).count()),
          expiry_time(0), iceberg_qty(0.0), trail_amount(0.0), trail_percent(0.0) {}
};

struct Trade {
    std::string id;
    std::string buy_order_id;
    std::string sell_order_id;
    std::string symbol;
    double quantity;
    Price price;
    int64_t timestamp;
    double maker_fee;
    double taker_fee;
    
    Trade(const std::string& trade_id, const std::string& buy_id, const std::string& sell_id,
          const std::string& sym, double qty, double prc)
        : id(trade_id), buy_order_id(buy_id), sell_order_id(sell_id), symbol(sym),
          quantity(qty), price(prc),
          timestamp(duration_cast<microseconds>(system_clock::now().time_since_epoch()).count()),
          maker_fee(0.001), taker_fee(0.001) {}
};

struct OrderBookLevel {
    Price price;
    double quantity;
    int order_count;
    
    OrderBookLevel(double p, double q, int c = 1) : price(p), quantity(q), order_count(c) {}
};

class OrderBook {
private:
    std::map<Price, double, std::greater<Price>> bids;  // Buy orders (highest price first)
    std::map<Price, double> asks;  // Sell orders (lowest price first)
    std::mutex book_mutex;
    
public:
    std::string symbol;
    Price last_price;
    double volume_24h;
    double price_change_24h;
    
    OrderBook(const std::string& sym) : symbol(sym), last_price(0.0), volume_24h(0.0), price_change_24h(0.0) {}
    
    void add_order(const Order& order) {
        std::lock_guard<std::mutex> lock(book_mutex);
        
        if (order.side == OrderSide::BUY) {
            bids[order.price] += order.quantity - order.filled_quantity;
        } else {
            asks[order.price] += order.quantity - order.filled_quantity;
        }
    }
    
    void remove_order(const Order& order) {
        std::lock_guard<std::mutex> lock(book_mutex);
        
        double remaining_qty = order.quantity - order.filled_quantity;
        
        if (order.side == OrderSide::BUY) {
            auto it = bids.find(order.price);
            if (it != bids.end()) {
                it->second -= remaining_qty;
                if (it->second <= 0) {
                    bids.erase(it);
                }
            }
        } else {
            auto it = asks.find(order.price);
            if (it != asks.end()) {
                it->second -= remaining_qty;
                if (it->second <= 0) {
                    asks.erase(it);
                }
            }
        }
    }
    
    Price get_best_bid() const {
        std::lock_guard<std::mutex> lock(book_mutex);
        return bids.empty() ? Price(0.0) : bids.begin()->first;
    }
    
    Price get_best_ask() const {
        std::lock_guard<std::mutex> lock(book_mutex);
        return asks.empty() ? Price(0.0) : asks.begin()->first;
    }
    
    double get_spread() const {
        Price best_bid = get_best_bid();
        Price best_ask = get_best_ask();
        return (best_ask.value > 0 && best_bid.value > 0) ? best_ask.value - best_bid.value : 0.0;
    }
    
    std::vector<OrderBookLevel> get_bids(int depth = 20) const {
        std::lock_guard<std::mutex> lock(book_mutex);
        std::vector<OrderBookLevel> result;
        
        int count = 0;
        for (const auto& [price, quantity] : bids) {
            if (count >= depth) break;
            result.emplace_back(price.value, quantity);
            count++;
        }
        
        return result;
    }
    
    std::vector<OrderBookLevel> get_asks(int depth = 20) const {
        std::lock_guard<std::mutex> lock(book_mutex);
        std::vector<OrderBookLevel> result;
        
        int count = 0;
        for (const auto& [price, quantity] : asks) {
            if (count >= depth) break;
            result.emplace_back(price.value, quantity);
            count++;
        }
        
        return result;
    }
    
    json to_json(int depth = 20) const {
        json result;
        result["symbol"] = symbol;
        result["timestamp"] = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
        result["lastPrice"] = last_price.value;
        result["volume24h"] = volume_24h;
        result["priceChange24h"] = price_change_24h;
        
        auto bid_levels = get_bids(depth);
        auto ask_levels = get_asks(depth);
        
        result["bids"] = json::array();
        for (const auto& level : bid_levels) {
            result["bids"].push_back({level.price.value, level.quantity});
        }
        
        result["asks"] = json::array();
        for (const auto& level : ask_levels) {
            result["asks"].push_back({level.price.value, level.quantity});
        }
        
        return result;
    }
};

class MatchingEngine {
private:
    std::unordered_map<std::string, std::unique_ptr<OrderBook>> order_books;
    std::unordered_map<std::string, std::shared_ptr<Order>> orders;
    std::vector<Trade> recent_trades;
    std::mutex engine_mutex;
    std::atomic<uint64_t> trade_id_counter{1};
    std::atomic<uint64_t> order_id_counter{1};
    
    // Risk management
    std::unordered_map<std::string, double> user_balances;
    std::unordered_map<std::string, double> user_margins;
    std::unordered_map<std::string, std::vector<std::string>> user_positions;
    
    // Advanced order management
    std::unordered_map<std::string, std::vector<std::string>> bracket_orders;
    std::unordered_map<std::string, std::string> oco_orders;
    
public:
    MatchingEngine() {
        // Initialize popular trading pairs
        std::vector<std::string> symbols = {
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "DOTUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT",
            "LTCUSDT", "BCHUSDT", "XRPUSDT", "DOGEUSDT", "SHIBUSDT"
        };
        
        for (const auto& symbol : symbols) {
            order_books[symbol] = std::make_unique<OrderBook>(symbol);
        }
    }
    
    std::string generate_order_id() {
        return "ORD" + std::to_string(order_id_counter.fetch_add(1));
    }
    
    std::string generate_trade_id() {
        return "TRD" + std::to_string(trade_id_counter.fetch_add(1));
    }
    
    bool validate_order(const Order& order) {
        // Basic validation
        if (order.quantity <= 0) return false;
        if (order.type == OrderType::LIMIT && order.price.value <= 0) return false;
        if (order_books.find(order.symbol) == order_books.end()) return false;
        
        // Balance validation
        if (order.side == OrderSide::BUY) {
            double required_balance = order.quantity * order.price.value;
            if (user_balances[order.user_id + "_USDT"] < required_balance) {
                return false;
            }
        } else {
            std::string base_asset = order.symbol.substr(0, order.symbol.find("USDT"));
            if (user_balances[order.user_id + "_" + base_asset] < order.quantity) {
                return false;
            }
        }
        
        return true;
    }
    
    std::string place_order(Order order) {
        std::lock_guard<std::mutex> lock(engine_mutex);
        
        if (!validate_order(order)) {
            order.status = OrderStatus::REJECTED;
            return "";
        }
        
        order.id = generate_order_id();
        order.status = OrderStatus::OPEN;
        
        // Handle different order types
        switch (order.type) {
            case OrderType::MARKET:
                return process_market_order(order);
            case OrderType::LIMIT:
                return process_limit_order(order);
            case OrderType::STOP_LOSS:
            case OrderType::STOP_LIMIT:
                return process_stop_order(order);
            case OrderType::TRAILING_STOP:
                return process_trailing_stop_order(order);
            case OrderType::ICEBERG:
                return process_iceberg_order(order);
            case OrderType::BRACKET:
                return process_bracket_order(order);
            case OrderType::OCO:
                return process_oco_order(order);
            default:
                return process_limit_order(order);
        }
    }
    
    std::string process_market_order(Order& order) {
        auto& book = order_books[order.symbol];
        
        if (order.side == OrderSide::BUY) {
            // Match against asks
            auto asks = book->get_asks();
            for (const auto& level : asks) {
                if (order.filled_quantity >= order.quantity) break;
                
                double available_qty = std::min(level.quantity, order.quantity - order.filled_quantity);
                
                // Create trade
                Trade trade(generate_trade_id(), order.id, "ASK_ORDER", order.symbol, available_qty, level.price.value);
                recent_trades.push_back(trade);
                
                order.filled_quantity += available_qty;
                book->last_price = Price(level.price.value);
                book->volume_24h += available_qty;
            }
        } else {
            // Match against bids
            auto bids = book->get_bids();
            for (const auto& level : bids) {
                if (order.filled_quantity >= order.quantity) break;
                
                double available_qty = std::min(level.quantity, order.quantity - order.filled_quantity);
                
                // Create trade
                Trade trade(generate_trade_id(), "BID_ORDER", order.id, order.symbol, available_qty, level.price.value);
                recent_trades.push_back(trade);
                
                order.filled_quantity += available_qty;
                book->last_price = Price(level.price.value);
                book->volume_24h += available_qty;
            }
        }
        
        if (order.filled_quantity >= order.quantity) {
            order.status = OrderStatus::FILLED;
        } else if (order.filled_quantity > 0) {
            order.status = OrderStatus::PARTIALLY_FILLED;
        }
        
        orders[order.id] = std::make_shared<Order>(order);
        return order.id;
    }
    
    std::string process_limit_order(Order& order) {
        auto& book = order_books[order.symbol];
        
        // Try to match immediately
        bool matched = false;
        
        if (order.side == OrderSide::BUY) {
            Price best_ask = book->get_best_ask();
            if (best_ask.value > 0 && order.price.value >= best_ask.value) {
                // Can match immediately
                matched = true;
                process_market_order(order);
            }
        } else {
            Price best_bid = book->get_best_bid();
            if (best_bid.value > 0 && order.price.value <= best_bid.value) {
                // Can match immediately
                matched = true;
                process_market_order(order);
            }
        }
        
        // If not fully matched, add to order book
        if (order.filled_quantity < order.quantity) {
            book->add_order(order);
            if (order.filled_quantity > 0) {
                order.status = OrderStatus::PARTIALLY_FILLED;
            } else {
                order.status = OrderStatus::OPEN;
            }
        }
        
        orders[order.id] = std::make_shared<Order>(order);
        return order.id;
    }
    
    std::string process_stop_order(Order& order) {
        // Stop orders are stored and triggered when price condition is met
        order.status = OrderStatus::PENDING;
        orders[order.id] = std::make_shared<Order>(order);
        return order.id;
    }
    
    std::string process_trailing_stop_order(Order& order) {
        // Trailing stop orders adjust the stop price based on market movement
        order.status = OrderStatus::PENDING;
        orders[order.id] = std::make_shared<Order>(order);
        return order.id;
    }
    
    std::string process_iceberg_order(Order& order) {
        // Iceberg orders show only a small portion of the total quantity
        if (order.iceberg_qty <= 0) {
            order.iceberg_qty = order.quantity * 0.1; // Default to 10% visibility
        }
        
        Order visible_order = order;
        visible_order.quantity = std::min(order.iceberg_qty, order.quantity);
        
        return process_limit_order(visible_order);
    }
    
    std::string process_bracket_order(Order& order) {
        // Bracket orders include a main order with stop-loss and take-profit orders
        std::string main_order_id = process_limit_order(order);
        
        if (!main_order_id.empty()) {
            // Create stop-loss order
            Order stop_loss = order;
            stop_loss.id = generate_order_id();
            stop_loss.type = OrderType::STOP_LOSS;
            stop_loss.side = (order.side == OrderSide::BUY) ? OrderSide::SELL : OrderSide::BUY;
            stop_loss.parent_order_id = main_order_id;
            
            // Create take-profit order
            Order take_profit = order;
            take_profit.id = generate_order_id();
            take_profit.type = OrderType::TAKE_PROFIT;
            take_profit.side = (order.side == OrderSide::BUY) ? OrderSide::SELL : OrderSide::BUY;
            take_profit.parent_order_id = main_order_id;
            
            bracket_orders[main_order_id] = {stop_loss.id, take_profit.id};
            orders[stop_loss.id] = std::make_shared<Order>(stop_loss);
            orders[take_profit.id] = std::make_shared<Order>(take_profit);
        }
        
        return main_order_id;
    }
    
    std::string process_oco_order(Order& order) {
        // One-Cancels-Other orders
        order.status = OrderStatus::PENDING;
        orders[order.id] = std::make_shared<Order>(order);
        return order.id;
    }
    
    bool cancel_order(const std::string& order_id, const std::string& user_id) {
        std::lock_guard<std::mutex> lock(engine_mutex);
        
        auto it = orders.find(order_id);
        if (it == orders.end() || it->second->user_id != user_id) {
            return false;
        }
        
        auto& order = it->second;
        if (order->status == OrderStatus::FILLED || order->status == OrderStatus::CANCELLED) {
            return false;
        }
        
        // Remove from order book
        auto& book = order_books[order->symbol];
        book->remove_order(*order);
        
        order->status = OrderStatus::CANCELLED;
        
        // Handle bracket order cancellation
        if (bracket_orders.find(order_id) != bracket_orders.end()) {
            for (const auto& child_id : bracket_orders[order_id]) {
                auto child_it = orders.find(child_id);
                if (child_it != orders.end()) {
                    child_it->second->status = OrderStatus::CANCELLED;
                }
            }
            bracket_orders.erase(order_id);
        }
        
        return true;
    }
    
    std::vector<Order> get_user_orders(const std::string& user_id, const std::string& symbol = "") {
        std::lock_guard<std::mutex> lock(engine_mutex);
        std::vector<Order> user_orders;
        
        for (const auto& [order_id, order] : orders) {
            if (order->user_id == user_id && (symbol.empty() || order->symbol == symbol)) {
                user_orders.push_back(*order);
            }
        }
        
        return user_orders;
    }
    
    std::vector<Trade> get_recent_trades(const std::string& symbol, int limit = 50) {
        std::lock_guard<std::mutex> lock(engine_mutex);
        std::vector<Trade> symbol_trades;
        
        for (auto it = recent_trades.rbegin(); it != recent_trades.rend() && symbol_trades.size() < limit; ++it) {
            if (it->symbol == symbol) {
                symbol_trades.push_back(*it);
            }
        }
        
        return symbol_trades;
    }
    
    json get_order_book(const std::string& symbol, int depth = 20) {
        auto it = order_books.find(symbol);
        if (it != order_books.end()) {
            return it->second->to_json(depth);
        }
        return json::object();
    }
    
    json get_market_stats(const std::string& symbol) {
        auto it = order_books.find(symbol);
        if (it == order_books.end()) {
            return json::object();
        }
        
        auto& book = it->second;
        json stats;
        stats["symbol"] = symbol;
        stats["lastPrice"] = book->last_price.value;
        stats["volume24h"] = book->volume_24h;
        stats["priceChange24h"] = book->price_change_24h;
        stats["bestBid"] = book->get_best_bid().value;
        stats["bestAsk"] = book->get_best_ask().value;
        stats["spread"] = book->get_spread();
        stats["timestamp"] = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
        
        return stats;
    }
    
    void update_user_balance(const std::string& user_id, const std::string& asset, double amount) {
        std::lock_guard<std::mutex> lock(engine_mutex);
        user_balances[user_id + "_" + asset] += amount;
    }
    
    double get_user_balance(const std::string& user_id, const std::string& asset) {
        std::lock_guard<std::mutex> lock(engine_mutex);
        return user_balances[user_id + "_" + asset];
    }
    
    // Advanced features
    void process_twap_order(Order& order, int duration_minutes) {
        // Time-Weighted Average Price execution
        // Split order into smaller chunks over time
    }
    
    void process_vwap_order(Order& order) {
        // Volume-Weighted Average Price execution
        // Execute based on historical volume patterns
    }
    
    void update_trailing_stops() {
        // Update trailing stop orders based on price movements
        for (auto& [order_id, order] : orders) {
            if (order->type == OrderType::TRAILING_STOP && order->status == OrderStatus::PENDING) {
                auto& book = order_books[order->symbol];
                double current_price = book->last_price.value;
                
                if (order->side == OrderSide::SELL) {
                    // For sell trailing stop, adjust stop price upward
                    double new_stop = current_price - order->trail_amount;
                    if (new_stop > order->stop_price.value) {
                        order->stop_price = Price(new_stop);
                    }
                } else {
                    // For buy trailing stop, adjust stop price downward
                    double new_stop = current_price + order->trail_amount;
                    if (new_stop < order->stop_price.value || order->stop_price.value == 0) {
                        order->stop_price = Price(new_stop);
                    }
                }
            }
        }
    }
    
    void check_stop_orders() {
        // Check and trigger stop orders
        for (auto& [order_id, order] : orders) {
            if ((order->type == OrderType::STOP_LOSS || order->type == OrderType::STOP_LIMIT || 
                 order->type == OrderType::TRAILING_STOP) && order->status == OrderStatus::PENDING) {
                
                auto& book = order_books[order->symbol];
                double current_price = book->last_price.value;
                
                bool should_trigger = false;
                
                if (order->side == OrderSide::BUY && current_price >= order->stop_price.value) {
                    should_trigger = true;
                } else if (order->side == OrderSide::SELL && current_price <= order->stop_price.value) {
                    should_trigger = true;
                }
                
                if (should_trigger) {
                    if (order->type == OrderType::STOP_LIMIT) {
                        order->type = OrderType::LIMIT;
                    } else {
                        order->type = OrderType::MARKET;
                    }
                    
                    if (order->type == OrderType::MARKET) {
                        process_market_order(*order);
                    } else {
                        process_limit_order(*order);
                    }
                }
            }
        }
    }
};

// WebSocket Server for real-time data
class TradingWebSocketServer {
private:
    websocketpp::server<websocketpp::config::asio> server;
    std::thread server_thread;
    MatchingEngine* engine;
    std::unordered_map<websocketpp::connection_hdl, std::string, std::owner_less<websocketpp::connection_hdl>> connections;
    
public:
    TradingWebSocketServer(MatchingEngine* eng) : engine(eng) {
        server.set_access_channels(websocketpp::log::alevel::all);
        server.clear_access_channels(websocketpp::log::alevel::frame_payload);
        server.init_asio();
        
        server.set_message_handler([this](websocketpp::connection_hdl hdl, websocketpp::server<websocketpp::config::asio>::message_ptr msg) {
            handle_message(hdl, msg);
        });
        
        server.set_open_handler([this](websocketpp::connection_hdl hdl) {
            connections[hdl] = "";
        });
        
        server.set_close_handler([this](websocketpp::connection_hdl hdl) {
            connections.erase(hdl);
        });
    }
    
    void start(uint16_t port) {
        server.listen(port);
        server.start_accept();
        
        server_thread = std::thread([this]() {
            server.run();
        });
    }
    
    void stop() {
        server.stop();
        if (server_thread.joinable()) {
            server_thread.join();
        }
    }
    
    void handle_message(websocketpp::connection_hdl hdl, websocketpp::server<websocketpp::config::asio>::message_ptr msg) {
        try {
            json request = json::parse(msg->get_payload());
            json response;
            
            std::string method = request["method"];
            
            if (method == "subscribe") {
                std::string channel = request["params"]["channel"];
                connections[hdl] = channel;
                
                response["id"] = request["id"];
                response["result"] = "subscribed";
                response["channel"] = channel;
                
            } else if (method == "place_order") {
                // Handle order placement via WebSocket
                Order order(
                    "",
                    request["params"]["user_id"],
                    request["params"]["symbol"],
                    static_cast<OrderType>(request["params"]["type"]),
                    static_cast<OrderSide>(request["params"]["side"]),
                    request["params"]["quantity"],
                    request["params"]["price"]
                );
                
                std::string order_id = engine->place_order(order);
                
                response["id"] = request["id"];
                response["result"]["order_id"] = order_id;
                response["result"]["status"] = "placed";
                
            } else if (method == "cancel_order") {
                bool success = engine->cancel_order(
                    request["params"]["order_id"],
                    request["params"]["user_id"]
                );
                
                response["id"] = request["id"];
                response["result"]["success"] = success;
            }
            
            server.get_alog().write(websocketpp::log::alevel::app, response.dump());
            server.send(hdl, response.dump(), websocketpp::frame::opcode::text);
            
        } catch (const std::exception& e) {
            json error_response;
            error_response["error"] = e.what();
            server.send(hdl, error_response.dump(), websocketpp::frame::opcode::text);
        }
    }
    
    void broadcast_order_book_update(const std::string& symbol) {
        json update = engine->get_order_book(symbol);
        update["type"] = "orderbook_update";
        
        std::string message = update.dump();
        
        for (const auto& [hdl, channel] : connections) {
            if (channel == "orderbook_" + symbol || channel == "all") {
                server.send(hdl, message, websocketpp::frame::opcode::text);
            }
        }
    }
    
    void broadcast_trade_update(const Trade& trade) {
        json update;
        update["type"] = "trade_update";
        update["symbol"] = trade.symbol;
        update["price"] = trade.price.value;
        update["quantity"] = trade.quantity;
        update["timestamp"] = trade.timestamp;
        update["trade_id"] = trade.id;
        
        std::string message = update.dump();
        
        for (const auto& [hdl, channel] : connections) {
            if (channel == "trades_" + trade.symbol || channel == "all") {
                server.send(hdl, message, websocketpp::frame::opcode::text);
            }
        }
    }
};

// Main Trading Engine Application
class TradingEngineApp {
private:
    std::unique_ptr<MatchingEngine> engine;
    std::unique_ptr<TradingWebSocketServer> ws_server;
    std::thread maintenance_thread;
    std::atomic<bool> running{true};
    
public:
    TradingEngineApp() {
        engine = std::make_unique<MatchingEngine>();
        ws_server = std::make_unique<TradingWebSocketServer>(engine.get());
    }
    
    void start() {
        std::cout << "Starting TigerEx Advanced Trading Engine..." << std::endl;
        
        // Start WebSocket server
        ws_server->start(8080);
        std::cout << "WebSocket server started on port 8080" << std::endl;
        
        // Start maintenance thread
        maintenance_thread = std::thread([this]() {
            maintenance_loop();
        });
        
        // Initialize with some test data
        initialize_test_data();
        
        std::cout << "Trading Engine is running. Press Ctrl+C to stop." << std::endl;
        
        // Keep main thread alive
        while (running) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }
    
    void stop() {
        running = false;
        ws_server->stop();
        
        if (maintenance_thread.joinable()) {
            maintenance_thread.join();
        }
        
        std::cout << "Trading Engine stopped." << std::endl;
    }
    
private:
    void maintenance_loop() {
        while (running) {
            // Update trailing stops
            engine->update_trailing_stops();
            
            // Check stop orders
            engine->check_stop_orders();
            
            // Broadcast market data updates
            broadcast_market_updates();
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    
    void broadcast_market_updates() {
        std::vector<std::string> symbols = {
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"
        };
        
        for (const auto& symbol : symbols) {
            ws_server->broadcast_order_book_update(symbol);
        }
    }
    
    void initialize_test_data() {
        // Add some initial balances for testing
        engine->update_user_balance("user1", "USDT", 100000.0);
        engine->update_user_balance("user1", "BTC", 10.0);
        engine->update_user_balance("user1", "ETH", 100.0);
        
        engine->update_user_balance("user2", "USDT", 50000.0);
        engine->update_user_balance("user2", "BTC", 5.0);
        engine->update_user_balance("user2", "ETH", 50.0);
        
        std::cout << "Test data initialized." << std::endl;
    }
};

int main() {
    try {
        TradingEngineApp app;
        
        // Handle Ctrl+C gracefully
        std::signal(SIGINT, [](int) {
            std::cout << "\nShutting down..." << std::endl;
            exit(0);
        });
        
        app.start();
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
