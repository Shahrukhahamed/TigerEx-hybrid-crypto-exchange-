package com.tigerex.mobile

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.tigerex.mobile.viewmodel.TradingViewModel
import java.text.NumberFormat
import java.util.*

@Composable
fun TradingScreen(navController: NavController) {
    val tradingViewModel: TradingViewModel = viewModel()
    var selectedTab by remember { mutableStateOf("Spot") }
    var selectedPair by remember { mutableStateOf("BTCUSDT") }
    
    LaunchedEffect(Unit) {
        tradingViewModel.loadTradingData(selectedPair)
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1a1a1a))
    ) {
        // Header with pair selection
        TradingHeader(
            selectedPair = selectedPair,
            onPairSelected = { pair ->
                selectedPair = pair
                tradingViewModel.loadTradingData(pair)
            },
            onBackClick = { navController.popBackStack() }
        )
        
        // Trading type tabs
        TradingTypeTabs(
            selectedTab = selectedTab,
            onTabSelected = { selectedTab = it }
        )
        
        // Main trading content
        when (selectedTab) {
            "Spot" -> SpotTradingContent(tradingViewModel, selectedPair)
            "Futures" -> FuturesTradingContent(tradingViewModel, selectedPair)
            "Options" -> OptionsTradingContent(tradingViewModel, selectedPair)
            "Margin" -> MarginTradingContent(tradingViewModel, selectedPair)
        }
    }
}

@Composable
fun TradingHeader(
    selectedPair: String,
    onPairSelected: (String) -> Unit,
    onBackClick: () -> Unit
) {
    var showPairSelector by remember { mutableStateOf(false) }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(0.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onBackClick) {
                Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = Color.White)
            }
            
            Column(
                modifier = Modifier
                    .clickable { showPairSelector = true }
                    .padding(horizontal = 16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = selectedPair,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Icon(
                        Icons.Default.KeyboardArrowDown,
                        contentDescription = "Select pair",
                        tint = Color.Gray,
                        modifier = Modifier.size(20.dp)
                    )
                }
                
                // Mock price data
                Text(
                    text = "$45,234.56",
                    fontSize = 16.sp,
                    color = Color.Green
                )
                Text(
                    text = "+2.34% (+$1,023.45)",
                    fontSize = 12.sp,
                    color = Color.Green
                )
            }
            
            Row {
                IconButton(onClick = { /* Open chart settings */ }) {
                    Icon(Icons.Default.Settings, contentDescription = "Settings", tint = Color.White)
                }
                IconButton(onClick = { /* Open favorites */ }) {
                    Icon(Icons.Default.Star, contentDescription = "Favorites", tint = Color.White)
                }
            }
        }
    }
    
    if (showPairSelector) {
        PairSelectorDialog(
            onPairSelected = { pair ->
                onPairSelected(pair)
                showPairSelector = false
            },
            onDismiss = { showPairSelector = false }
        )
    }
}

@Composable
fun TradingTypeTabs(
    selectedTab: String,
    onTabSelected: (String) -> Unit
) {
    val tabs = listOf("Spot", "Futures", "Options", "Margin")
    
    LazyRow(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF2a2a2a))
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(tabs) { tab ->
            Button(
                onClick = { onTabSelected(tab) },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (selectedTab == tab) Color(0xFFf97316) else Color.Transparent,
                    contentColor = if (selectedTab == tab) Color.White else Color.Gray
                ),
                shape = RoundedCornerShape(20.dp),
                modifier = Modifier.height(36.dp)
            ) {
                Text(tab, fontSize = 14.sp)
            }
        }
    }
}

@Composable
fun SpotTradingContent(tradingViewModel: TradingViewModel, selectedPair: String) {
    val tradingData by tradingViewModel.tradingData.collectAsState()
    
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Price Chart
        item {
            TradingChart(tradingData.chartData)
        }
        
        // Order Book and Recent Trades
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OrderBookCard(
                    orderBook = tradingData.orderBook,
                    modifier = Modifier.weight(1f)
                )
                RecentTradesCard(
                    trades = tradingData.recentTrades,
                    modifier = Modifier.weight(1f)
                )
            }
        }
        
        // Trading Form
        item {
            SpotTradingForm(selectedPair)
        }
        
        // Open Orders
        item {
            OpenOrdersCard(tradingData.openOrders)
        }
        
        // Order History
        item {
            OrderHistoryCard(tradingData.orderHistory)
        }
    }
}

@Composable
fun TradingChart(chartData: List<ChartPoint>) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(300.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Price Chart",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                
                Row {
                    listOf("1m", "5m", "15m", "1h", "4h", "1d").forEach { timeframe ->
                        Text(
                            text = timeframe,
                            fontSize = 12.sp,
                            color = Color.Gray,
                            modifier = Modifier
                                .clickable { /* Change timeframe */ }
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Simple line chart
            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
            ) {
                if (chartData.isNotEmpty()) {
                    drawChart(chartData, size.width, size.height)
                }
            }
        }
    }
}

fun DrawScope.drawChart(data: List<ChartPoint>, width: Float, height: Float) {
    if (data.size < 2) return
    
    val minPrice = data.minOf { it.price }
    val maxPrice = data.maxOf { it.price }
    val priceRange = maxPrice - minPrice
    
    val path = Path()
    
    data.forEachIndexed { index, point ->
        val x = (index.toFloat() / (data.size - 1)) * width
        val y = height - ((point.price - minPrice) / priceRange) * height
        
        if (index == 0) {
            path.moveTo(x, y)
        } else {
            path.lineTo(x, y)
        }
    }
    
    drawPath(
        path = path,
        color = Color(0xFFf97316),
        style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3.dp.toPx())
    )
}

@Composable
fun OrderBookCard(orderBook: OrderBook, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(300.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "Order Book",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            // Headers
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Price", fontSize = 12.sp, color = Color.Gray)
                Text("Amount", fontSize = 12.sp, color = Color.Gray)
                Text("Total", fontSize = 12.sp, color = Color.Gray)
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Sell orders (red)
            LazyColumn(
                modifier = Modifier.weight(1f),
                reverseLayout = true
            ) {
                items(orderBook.sellOrders.take(5)) { order ->
                    OrderBookItem(order, Color.Red)
                }
            }
            
            // Current price
            Divider(color = Color.Gray, thickness = 1.dp)
            Text(
                text = "$${String.format("%.2f", orderBook.currentPrice)}",
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
            )
            Divider(color = Color.Gray, thickness = 1.dp)
            
            // Buy orders (green)
            LazyColumn(
                modifier = Modifier.weight(1f)
            ) {
                items(orderBook.buyOrders.take(5)) { order ->
                    OrderBookItem(order, Color.Green)
                }
            }
        }
    }
}

@Composable
fun OrderBookItem(order: OrderBookEntry, color: Color) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = String.format("%.2f", order.price),
            fontSize = 12.sp,
            color = color
        )
        Text(
            text = String.format("%.4f", order.amount),
            fontSize = 12.sp,
            color = Color.White
        )
        Text(
            text = String.format("%.2f", order.total),
            fontSize = 12.sp,
            color = Color.Gray
        )
    }
}

@Composable
fun RecentTradesCard(trades: List<Trade>, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(300.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "Recent Trades",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            // Headers
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Price", fontSize = 12.sp, color = Color.Gray)
                Text("Amount", fontSize = 12.sp, color = Color.Gray)
                Text("Time", fontSize = 12.sp, color = Color.Gray)
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            LazyColumn {
                items(trades) { trade ->
                    RecentTradeItem(trade)
                }
            }
        }
    }
}

@Composable
fun RecentTradeItem(trade: Trade) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = String.format("%.2f", trade.price),
            fontSize = 12.sp,
            color = if (trade.side == "buy") Color.Green else Color.Red
        )
        Text(
            text = String.format("%.4f", trade.amount),
            fontSize = 12.sp,
            color = Color.White
        )
        Text(
            text = trade.time,
            fontSize = 12.sp,
            color = Color.Gray
        )
    }
}

@Composable
fun SpotTradingForm(selectedPair: String) {
    var orderType by remember { mutableStateOf("Market") }
    var side by remember { mutableStateOf("Buy") }
    var amount by remember { mutableStateOf("") }
    var price by remember { mutableStateOf("") }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "Place Order",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            
            // Buy/Sell Toggle
            Row(
                modifier = Modifier.fillMaxWidth()
            ) {
                Button(
                    onClick = { side = "Buy" },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (side == "Buy") Color.Green else Color.Transparent,
                        contentColor = if (side == "Buy") Color.White else Color.Green
                    ),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Buy")
                }
                
                Spacer(modifier = Modifier.width(8.dp))
                
                Button(
                    onClick = { side = "Sell" },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (side == "Sell") Color.Red else Color.Transparent,
                        contentColor = if (side == "Sell") Color.White else Color.Red
                    ),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Sell")
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Order Type
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf("Market", "Limit", "Stop").forEach { type ->
                    Button(
                        onClick = { orderType = type },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (orderType == type) Color(0xFFf97316) else Color.Transparent,
                            contentColor = if (orderType == type) Color.White else Color.Gray
                        ),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(type, fontSize = 12.sp)
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Price input (for limit orders)
            if (orderType != "Market") {
                OutlinedTextField(
                    value = price,
                    onValueChange = { price = it },
                    label = { Text("Price") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFFf97316),
                        unfocusedBorderColor = Color.Gray
                    )
                )
                
                Spacer(modifier = Modifier.height(12.dp))
            }
            
            // Amount input
            OutlinedTextField(
                value = amount,
                onValueChange = { amount = it },
                label = { Text("Amount") },
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = Color(0xFFf97316),
                    unfocusedBorderColor = Color.Gray
                )
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Percentage buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf("25%", "50%", "75%", "100%").forEach { percentage ->
                    Button(
                        onClick = { /* Calculate amount based on percentage */ },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color.Transparent,
                            contentColor = Color.Gray
                        ),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(percentage, fontSize = 12.sp)
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // Place Order Button
            Button(
                onClick = { /* Place order */ },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (side == "Buy") Color.Green else Color.Red
                )
            ) {
                Text(
                    text = "$side $selectedPair",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

@Composable
fun OpenOrdersCard(orders: List<Order>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "Open Orders",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            
            if (orders.isEmpty()) {
                Text(
                    text = "No open orders",
                    fontSize = 14.sp,
                    color = Color.Gray,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            } else {
                LazyColumn(
                    modifier = Modifier.height(200.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(orders) { order ->
                        OrderItem(order)
                    }
                }
            }
        }
    }
}

@Composable
fun OrderHistoryCard(orders: List<Order>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "Order History",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            
            LazyColumn(
                modifier = Modifier.height(200.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(orders) { order ->
                    OrderItem(order)
                }
            }
        }
    }
}

@Composable
fun OrderItem(order: Order) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column {
            Text(
                text = "${order.side} ${order.pair}",
                fontSize = 14.sp,
                color = Color.White,
                fontWeight = FontWeight.Medium
            )
            Text(
                text = "${order.type} • ${order.amount}",
                fontSize = 12.sp,
                color = Color.Gray
            )
        }
        
        Column(horizontalAlignment = Alignment.End) {
            Text(
                text = "$${String.format("%.2f", order.price)}",
                fontSize = 14.sp,
                color = Color.White
            )
            Text(
                text = order.status,
                fontSize = 12.sp,
                color = when (order.status) {
                    "Filled" -> Color.Green
                    "Cancelled" -> Color.Red
                    "Partial" -> Color.Yellow
                    else -> Color.Gray
                }
            )
        }
    }
}

@Composable
fun PairSelectorDialog(
    onPairSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val popularPairs = listOf(
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
        "DOTUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT"
    )
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Select Trading Pair", color = Color.White) },
        text = {
            LazyColumn {
                items(popularPairs) { pair ->
                    Text(
                        text = pair,
                        color = Color.White,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onPairSelected(pair) }
                            .padding(vertical = 12.dp)
                    )
                }
            }
        },
        confirmButton = {},
        containerColor = Color(0xFF2a2a2a)
    )
}

// Additional trading screens for Futures, Options, Margin
@Composable
fun FuturesTradingContent(tradingViewModel: TradingViewModel, selectedPair: String) {
    // Similar to SpotTradingContent but with futures-specific features
    Text("Futures Trading - Coming Soon", color = Color.White, modifier = Modifier.padding(16.dp))
}

@Composable
fun OptionsTradingContent(tradingViewModel: TradingViewModel, selectedPair: String) {
    // Options trading interface
    Text("Options Trading - Coming Soon", color = Color.White, modifier = Modifier.padding(16.dp))
}

@Composable
fun MarginTradingContent(tradingViewModel: TradingViewModel, selectedPair: String) {
    // Margin trading interface
    Text("Margin Trading - Coming Soon", color = Color.White, modifier = Modifier.padding(16.dp))
}

// Data classes for trading
data class ChartPoint(val timestamp: Long, val price: Double)

data class OrderBook(
    val buyOrders: List<OrderBookEntry>,
    val sellOrders: List<OrderBookEntry>,
    val currentPrice: Double
)

data class OrderBookEntry(
    val price: Double,
    val amount: Double,
    val total: Double
)

data class Trade(
    val price: Double,
    val amount: Double,
    val side: String,
    val time: String
)

data class Order(
    val id: String,
    val pair: String,
    val side: String,
    val type: String,
    val amount: Double,
    val price: Double,
    val status: String,
    val timestamp: Long
)

data class TradingData(
    val chartData: List<ChartPoint> = emptyList(),
    val orderBook: OrderBook = OrderBook(emptyList(), emptyList(), 0.0),
    val recentTrades: List<Trade> = emptyList(),
    val openOrders: List<Order> = emptyList(),
    val orderHistory: List<Order> = emptyList()
)
