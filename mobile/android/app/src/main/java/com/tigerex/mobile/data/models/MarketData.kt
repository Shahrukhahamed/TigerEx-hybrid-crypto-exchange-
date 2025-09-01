package com.tigerex.mobile.data.models

data class MarketData(
    val symbol: String,
    val price: String,
    val change: String,
    val volume: String,
    val isPositive: Boolean
)

data class OrderBookEntry(
    val price: String,
    val amount: String
)

data class OrderBook(
    val buys: List<OrderBookEntry>,
    val sells: List<OrderBookEntry>
)

data class TradingPair(
    val symbol: String,
    val baseAsset: String,
    val quoteAsset: String,
    val price: Double,
    val change24h: Double,
    val volume24h: Double,
    val high24h: Double,
    val low24h: Double
)

data class WalletBalance(
    val asset: String,
    val free: Double,
    val locked: Double,
    val total: Double,
    val usdValue: Double
)

data class Transaction(
    val id: String,
    val type: String,
    val asset: String,
    val amount: Double,
    val status: String,
    val timestamp: Long,
    val txHash: String?
)

data class P2POrder(
    val id: String,
    val type: String, // buy/sell
    val asset: String,
    val fiatCurrency: String,
    val amount: Double,
    val price: Double,
    val paymentMethods: List<String>,
    val minLimit: Double,
    val maxLimit: Double,
    val terms: String,
    val trader: P2PTrader,
    val status: String
)

data class P2PTrader(
    val username: String,
    val completionRate: Double,
    val totalTrades: Int,
    val rating: Double,
    val isVerified: Boolean
)

data class NFTItem(
    val id: String,
    val name: String,
    val description: String,
    val imageUrl: String,
    val collection: String,
    val price: Double,
    val currency: String,
    val owner: String,
    val isForSale: Boolean
)

data class CopyTrader(
    val id: String,
    val username: String,
    val avatar: String,
    val totalReturn: Double,
    val monthlyReturn: Double,
    val winRate: Double,
    val followers: Int,
    val aum: Double, // Assets Under Management
    val maxDrawdown: Double,
    val tradingPairs: List<String>,
    val isVerified: Boolean,
    val description: String
)

data class Portfolio(
    val totalValue: Double,
    val totalPnl: Double,
    val totalPnlPercentage: Double,
    val balances: List<WalletBalance>,
    val positions: List<Position>
)

data class Position(
    val symbol: String,
    val side: String, // long/short
    val size: Double,
    val entryPrice: Double,
    val markPrice: Double,
    val pnl: Double,
    val pnlPercentage: Double,
    val margin: Double,
    val leverage: Int
)
