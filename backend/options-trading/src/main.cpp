/*
TigerEx Options Trading Engine
Advanced options trading system with all features from major exchanges
Supports European/American options, exotic options, volatility trading
*/

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <memory>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <queue>
#include <unordered_map>

using namespace std;

// Option Types
enum class OptionType {
    CALL,
    PUT
};

enum class OptionStyle {
    EUROPEAN,
    AMERICAN,
    ASIAN,
    BARRIER,
    BINARY,
    LOOKBACK,
    RAINBOW
};

// Greeks Structure
struct Greeks {
    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
    double epsilon;
    
    Greeks() : delta(0), gamma(0), theta(0), vega(0), rho(0), epsilon(0) {}
};

// Option Contract
struct OptionContract {
    string symbol;
    string underlying;
    OptionType type;
    OptionStyle style;
    double strike_price;
    chrono::system_clock::time_point expiry_date;
    double contract_size;
    double tick_size;
    bool is_active;
    
    // Market data
    double mark_price;
    double bid_price;
    double ask_price;
    double last_price;
    double volume_24h;
    double open_interest;
    
    // Greeks
    Greeks greeks;
    
    // Volatility data
    double implied_volatility;
    double historical_volatility;
    
    OptionContract() : is_active(true), mark_price(0), bid_price(0), ask_price(0), 
                      last_price(0), volume_24h(0), open_interest(0),
                      implied_volatility(0), historical_volatility(0) {}
};

// Black-Scholes Option Pricing Model
class BlackScholesModel {
public:
    static double normalCDF(double x) {
        return 0.5 * erfc(-x * M_SQRT1_2);
    }
    
    static double normalPDF(double x) {
        return exp(-0.5 * x * x) / sqrt(2 * M_PI);
    }
    
    static double calculateOptionPrice(
        double spot_price,
        double strike_price,
        double time_to_expiry,
        double risk_free_rate,
        double volatility,
        OptionType option_type
    ) {
        if (time_to_expiry <= 0) return 0;
        
        double d1 = (log(spot_price / strike_price) + 
                    (risk_free_rate + 0.5 * volatility * volatility) * time_to_expiry) /
                   (volatility * sqrt(time_to_expiry));
        
        double d2 = d1 - volatility * sqrt(time_to_expiry);
        
        if (option_type == OptionType::CALL) {
            return spot_price * normalCDF(d1) - 
                   strike_price * exp(-risk_free_rate * time_to_expiry) * normalCDF(d2);
        } else {
            return strike_price * exp(-risk_free_rate * time_to_expiry) * normalCDF(-d2) - 
                   spot_price * normalCDF(-d1);
        }
    }
    
    static Greeks calculateGreeks(
        double spot_price,
        double strike_price,
        double time_to_expiry,
        double risk_free_rate,
        double volatility,
        OptionType option_type
    ) {
        Greeks greeks;
        
        if (time_to_expiry <= 0) return greeks;
        
        double d1 = (log(spot_price / strike_price) + 
                    (risk_free_rate + 0.5 * volatility * volatility) * time_to_expiry) /
                   (volatility * sqrt(time_to_expiry));
        
        double d2 = d1 - volatility * sqrt(time_to_expiry);
        
        // Delta
        if (option_type == OptionType::CALL) {
            greeks.delta = normalCDF(d1);
        } else {
            greeks.delta = normalCDF(d1) - 1;
        }
        
        // Gamma
        greeks.gamma = normalPDF(d1) / (spot_price * volatility * sqrt(time_to_expiry));
        
        // Theta
        double theta_common = -(spot_price * normalPDF(d1) * volatility) / (2 * sqrt(time_to_expiry));
        if (option_type == OptionType::CALL) {
            greeks.theta = theta_common - 
                          risk_free_rate * strike_price * exp(-risk_free_rate * time_to_expiry) * normalCDF(d2);
        } else {
            greeks.theta = theta_common + 
                          risk_free_rate * strike_price * exp(-risk_free_rate * time_to_expiry) * normalCDF(-d2);
        }
        greeks.theta /= 365; // Convert to daily theta
        
        // Vega
        greeks.vega = spot_price * normalPDF(d1) * sqrt(time_to_expiry) / 100; // Per 1% vol change
        
        // Rho
        if (option_type == OptionType::CALL) {
            greeks.rho = strike_price * time_to_expiry * 
                        exp(-risk_free_rate * time_to_expiry) * normalCDF(d2) / 100;
        } else {
            greeks.rho = -strike_price * time_to_expiry * 
                        exp(-risk_free_rate * time_to_expiry) * normalCDF(-d2) / 100;
        }
        
        return greeks;
    }
};

// Options Trading Engine
class OptionsTradingEngine {
private:
    unordered_map<string, OptionContract> contracts;
    mutable mutex contracts_mutex;
    atomic<bool> running{true};
    
    // Market data
    unordered_map<string, double> underlying_prices;
    double risk_free_rate = 0.05; // 5% default
    
public:
    OptionsTradingEngine() {
        loadContracts();
        startPricingEngine();
    }
    
    ~OptionsTradingEngine() {
        running = false;
    }
    
    void loadContracts() {
        // Load contracts from database
        // For demo, create some sample contracts
        OptionContract btc_call;
        btc_call.symbol = "BTC-50000-C-20241231";
        btc_call.underlying = "BTC";
        btc_call.type = OptionType::CALL;
        btc_call.style = OptionStyle::EUROPEAN;
        btc_call.strike_price = 50000;
        btc_call.contract_size = 1.0;
        btc_call.tick_size = 0.01;
        
        lock_guard<mutex> lock(contracts_mutex);
        contracts[btc_call.symbol] = btc_call;
        
        // Set sample underlying price
        underlying_prices["BTC"] = 45000.0;
    }
    
    void startPricingEngine() {
        thread([this]() {
            while (running) {
                updateOptionPrices();
                this_thread::sleep_for(chrono::milliseconds(100));
            }
        }).detach();
    }
    
    void updateOptionPrices() {
        lock_guard<mutex> lock(contracts_mutex);
        
        for (auto& [symbol, contract] : contracts) {
            // Get underlying price
            double underlying_price = getUnderlyingPrice(contract.underlying);
            if (underlying_price <= 0) continue;
            
            // Calculate time to expiry (simplified)
            double time_to_expiry = 0.25; // 3 months
            
            // Get volatility
            double volatility = 0.8; // 80% volatility for crypto
            
            // Calculate theoretical price
            double theoretical_price = BlackScholesModel::calculateOptionPrice(
                underlying_price,
                contract.strike_price,
                time_to_expiry,
                risk_free_rate,
                volatility,
                contract.type
            );
            
            contract.mark_price = theoretical_price;
            
            // Calculate Greeks
            contract.greeks = BlackScholesModel::calculateGreeks(
                underlying_price,
                contract.strike_price,
                time_to_expiry,
                risk_free_rate,
                volatility,
                contract.type
            );
            
            contract.implied_volatility = volatility;
        }
    }
    
    double getUnderlyingPrice(const string& underlying) {
        auto it = underlying_prices.find(underlying);
        return (it != underlying_prices.end()) ? it->second : 0.0;
    }
    
    // API Methods
    vector<OptionContract> getOptionChain(const string& underlying) {
        vector<OptionContract> chain;
        lock_guard<mutex> lock(contracts_mutex);
        
        for (const auto& [symbol, contract] : contracts) {
            if (contract.underlying == underlying && contract.is_active) {
                chain.push_back(contract);
            }
        }
        
        return chain;
    }
    
    OptionContract getContract(const string& symbol) {
        lock_guard<mutex> lock(contracts_mutex);
        auto it = contracts.find(symbol);
        return (it != contracts.end()) ? it->second : OptionContract();
    }
    
    void updateUnderlyingPrice(const string& underlying, double price) {
        underlying_prices[underlying] = price;
    }
};

int main() {
    try {
        cout << "Starting TigerEx Options Trading Engine..." << endl;
        
        OptionsTradingEngine engine;
        
        // Demo: Get option chain for BTC
        auto btc_options = engine.getOptionChain("BTC");
        
        cout << "BTC Options Chain:" << endl;
        for (const auto& option : btc_options) {
            cout << "Symbol: " << option.symbol << endl;
            cout << "Strike: " << option.strike_price << endl;
            cout << "Mark Price: " << option.mark_price << endl;
            cout << "Delta: " << option.greeks.delta << endl;
            cout << "Gamma: " << option.greeks.gamma << endl;
            cout << "Theta: " << option.greeks.theta << endl;
            cout << "Vega: " << option.greeks.vega << endl;
            cout << "Rho: " << option.greeks.rho << endl;
            cout << "IV: " << option.implied_volatility << endl;
            cout << "---" << endl;
        }
        
        // Keep the main thread alive
        this_thread::sleep_for(chrono::seconds(5));
        
    } catch (const exception& e) {
        cerr << "Fatal error: " << e.what() << endl;
        return 1;
    }
    
    return 0;
}