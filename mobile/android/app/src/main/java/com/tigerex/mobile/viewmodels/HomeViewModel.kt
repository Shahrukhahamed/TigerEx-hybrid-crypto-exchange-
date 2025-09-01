package com.tigerex.mobile.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tigerex.mobile.data.models.MarketData
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class HomeViewModel : ViewModel() {
    private val _marketData = MutableStateFlow<List<MarketData>>(emptyList())
    val marketData: StateFlow<List<MarketData>> = _marketData.asStateFlow()
    
    private val _portfolioValue = MutableStateFlow(0.0)
    val portfolioValue: StateFlow<Double> = _portfolioValue.asStateFlow()
    
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    init {
        loadMarketData()
        loadPortfolioData()
    }
    
    private fun loadMarketData() {
        viewModelScope.launch {
            _isLoading.value = true
            
            // Simulate API call
            val mockData = listOf(
                MarketData("BTC/USDT", "43,250.00", "+2.45%", "2.1B", true),
                MarketData("ETH/USDT", "2,650.00", "+1.85%", "1.8B", true),
                MarketData("BNB/USDT", "315.50", "-0.75%", "450M", false),
                MarketData("ADA/USDT", "0.4850", "+3.20%", "320M", true),
                MarketData("SOL/USDT", "98.75", "+4.15%", "280M", true),
                MarketData("MATIC/USDT", "0.8950", "-1.25%", "180M", false),
                MarketData("DOT/USDT", "7.25", "+2.80%", "150M", true),
                MarketData("AVAX/USDT", "38.50", "+1.95%", "120M", true)
            )
            
            _marketData.value = mockData
            _isLoading.value = false
        }
    }
    
    private fun loadPortfolioData() {
        viewModelScope.launch {
            // Simulate portfolio data loading
            _portfolioValue.value = 12345.67
        }
    }
    
    fun refreshData() {
        loadMarketData()
        loadPortfolioData()
    }
}

class TradingViewModel : ViewModel() {
    private val _selectedPair = MutableStateFlow("BTC/USDT")
    val selectedPair: StateFlow<String> = _selectedPair.asStateFlow()
    
    private val _orderBook = MutableStateFlow(
        com.tigerex.mobile.data.models.OrderBook(
            buys = listOf(
                com.tigerex.mobile.data.models.OrderBookEntry("43,248.50", "0.1234"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,247.25", "0.2567"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,246.00", "0.3891"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,245.75", "0.1456"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,244.50", "0.2789")
            ),
            sells = listOf(
                com.tigerex.mobile.data.models.OrderBookEntry("43,251.25", "0.1567"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,252.50", "0.2234"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,253.75", "0.3456"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,255.00", "0.1789"),
                com.tigerex.mobile.data.models.OrderBookEntry("43,256.25", "0.2345")
            )
        )
    )
    val orderBook: StateFlow<com.tigerex.mobile.data.models.OrderBook> = _orderBook.asStateFlow()
    
    fun selectPair(pair: String) {
        _selectedPair.value = pair
        loadOrderBook(pair)
    }
    
    private fun loadOrderBook(pair: String) {
        viewModelScope.launch {
            // Simulate order book loading
            // In real app, this would fetch from API
        }
    }
    
    fun placeOrder(
        type: String,
        amount: Double,
        price: Double
    ) {
        viewModelScope.launch {
            // Implement order placement logic
        }
    }
}
