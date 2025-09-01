package com.tigerex.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tigerex.mobile.ui.theme.TigerExTheme
import com.tigerex.mobile.screens.*
import com.tigerex.mobile.data.models.*
import com.tigerex.mobile.viewmodels.*
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            TigerExTheme {
                TigerExApp()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TigerExApp() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "splash"
    ) {
        composable("splash") { SplashScreen(navController) }
        composable("login") { LoginScreen(navController) }
        composable("register") { RegisterScreen(navController) }
        composable("home") { HomeScreen(navController) }
        composable("trading") { TradingScreen(navController) }
        composable("futures") { FuturesScreen(navController) }
        composable("options") { OptionsScreen(navController) }
        composable("p2p") { P2PScreen(navController) }
        composable("wallet") { WalletScreen(navController) }
        composable("portfolio") { PortfolioScreen(navController) }
        composable("copy_trading") { CopyTradingScreen(navController) }
        composable("nft") { NFTScreen(navController) }
        composable("profile") { ProfileScreen(navController) }
        composable("admin") { AdminScreen(navController) }
    }
}

// Splash Screen
@Composable
fun SplashScreen(navController: NavController) {
    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(2000)
        navController.navigate("login") {
            popUpTo("splash") { inclusive = true }
        }
    }
    
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "TigerEx",
                fontSize = 48.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFFF59E0B)
            )
            Text(
                text = "Advanced Crypto Trading",
                fontSize = 16.sp,
                color = Color.Gray
            )
        }
    }
}

// Login Screen
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(navController: NavController) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Welcome Back",
            fontSize = 32.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 32.dp)
        )
        
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp)
        )
        
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 24.dp)
        )
        
        Button(
            onClick = {
                isLoading = true
                // Simulate login
                navController.navigate("home") {
                    popUpTo("login") { inclusive = true }
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFFF59E0B)
            )
        ) {
            if (isLoading) {
                CircularProgressIndicator(color = Color.Black, modifier = Modifier.size(20.dp))
            } else {
                Text("Login", color = Color.Black, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            }
        }
        
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            TextButton(onClick = { navController.navigate("register") }) {
                Text("Don't have an account? Register")
            }
        }
        
        // OAuth Buttons
        Spacer(modifier = Modifier.height(32.dp))
        
        OutlinedButton(
            onClick = { /* Google OAuth */ },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
        ) {
            Text("Continue with Google")
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        OutlinedButton(
            onClick = { /* Apple OAuth */ },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
        ) {
            Text("Continue with Apple")
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        OutlinedButton(
            onClick = { /* Telegram OAuth */ },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
        ) {
            Text("Continue with Telegram")
        }
    }
}

// Home Screen
@Composable
fun HomeScreen(navController: NavController) {
    val viewModel: HomeViewModel = viewModel()
    val marketData by viewModel.marketData.collectAsState()
    
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        // Header
        TopAppBar(
            title = { Text("TigerEx") },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color(0xFF1F2937)
            )
        )
        
        // Portfolio Summary
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFF374151)
            )
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = "Portfolio Value",
                    color = Color.Gray,
                    fontSize = 14.sp
                )
                Text(
                    text = "$12,345.67",
                    color = Color.White,
                    fontSize = 32.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "+$234.56 (+1.95%)",
                    color = Color(0xFF10B981),
                    fontSize = 16.sp
                )
            }
        }
        
        // Quick Actions
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            QuickActionButton("Trade", Color(0xFFF59E0B)) { navController.navigate("trading") }
            QuickActionButton("Futures", Color(0xFF8B5CF6)) { navController.navigate("futures") }
            QuickActionButton("P2P", Color(0xFF06B6D4)) { navController.navigate("p2p") }
            QuickActionButton("Wallet", Color(0xFF10B981)) { navController.navigate("wallet") }
        }
        
        // Market Data
        Text(
            text = "Markets",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(16.dp)
        )
        
        LazyColumn {
            items(marketData) { market ->
                MarketItem(market)
            }
        }
    }
}

@Composable
fun QuickActionButton(
    text: String,
    color: Color,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(containerColor = color),
        modifier = Modifier.size(80.dp, 40.dp)
    ) {
        Text(
            text = text,
            color = Color.White,
            fontSize = 12.sp
        )
    }
}

@Composable
fun MarketItem(market: MarketData) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF374151)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = market.symbol,
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Vol: ${market.volume}",
                    color = Color.Gray,
                    fontSize = 12.sp
                )
            }
            
            Column(
                horizontalAlignment = Alignment.End
            ) {
                Text(
                    text = "$${market.price}",
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = market.change,
                    color = if (market.isPositive) Color(0xFF10B981) else Color(0xFFEF4444),
                    fontSize = 12.sp
                )
            }
        }
    }
}

// Trading Screen
@Composable
fun TradingScreen(navController: NavController) {
    val viewModel: TradingViewModel = viewModel()
    val selectedPair by viewModel.selectedPair.collectAsState()
    val orderBook by viewModel.orderBook.collectAsState()
    
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        TopAppBar(
            title = { Text("Spot Trading") },
            navigationIcon = {
                IconButton(onClick = { navController.popBackStack() }) {
                    Text("←")
                }
            }
        )
        
        // Trading Pair Selector
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = selectedPair,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "$43,250.00",
                    fontSize = 20.sp,
                    color = Color(0xFF10B981)
                )
                Text(
                    text = "+2.45% (+$1,035.50)",
                    fontSize = 14.sp,
                    color = Color(0xFF10B981)
                )
            }
        }
        
        // Order Book and Order Form
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .padding(horizontal = 16.dp)
        ) {
            // Order Book
            Card(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .padding(end = 8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Order Book",
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                    
                    LazyColumn {
                        items(orderBook.sells.take(5)) { order ->
                            OrderBookItem(order, false)
                        }
                        items(orderBook.buys.take(5)) { order ->
                            OrderBookItem(order, true)
                        }
                    }
                }
            }
            
            // Order Form
            Card(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .padding(start = 8.dp)
            ) {
                OrderForm()
            }
        }
    }
}

@Composable
fun OrderBookItem(order: OrderBookEntry, isBuy: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = order.price,
            color = if (isBuy) Color(0xFF10B981) else Color(0xFFEF4444),
            fontSize = 12.sp
        )
        Text(
            text = order.amount,
            color = Color.Gray,
            fontSize = 12.sp
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderForm() {
    var orderType by remember { mutableStateOf("Buy") }
    var amount by remember { mutableStateOf("") }
    var price by remember { mutableStateOf("") }
    
    Column(
        modifier = Modifier.padding(16.dp)
    ) {
        Text(
            text = "Place Order",
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        
        // Buy/Sell Toggle
        Row(
            modifier = Modifier.fillMaxWidth()
        ) {
            Button(
                onClick = { orderType = "Buy" },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (orderType == "Buy") Color(0xFF10B981) else Color.Gray
                ),
                modifier = Modifier.weight(1f)
            ) {
                Text("Buy")
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
                onClick = { orderType = "Sell" },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (orderType == "Sell") Color(0xFFEF4444) else Color.Gray
                ),
                modifier = Modifier.weight(1f)
            ) {
                Text("Sell")
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        OutlinedTextField(
            value = price,
            onValueChange = { price = it },
            label = { Text("Price (USDT)") },
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        OutlinedTextField(
            value = amount,
            onValueChange = { amount = it },
            label = { Text("Amount (BTC)") },
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Button(
            onClick = { /* Place order */ },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(
                containerColor = if (orderType == "Buy") Color(0xFF10B981) else Color(0xFFEF4444)
            )
        ) {
            Text("$orderType ${if (orderType == "Buy") "BTC" else "BTC"}")
        }
    }
}

// Additional screens would be implemented similarly...
@Composable fun RegisterScreen(navController: NavController) { /* Implementation */ }
@Composable fun FuturesScreen(navController: NavController) { /* Implementation */ }
@Composable fun OptionsScreen(navController: NavController) { /* Implementation */ }
@Composable fun P2PScreen(navController: NavController) { /* Implementation */ }
@Composable fun WalletScreen(navController: NavController) { /* Implementation */ }
@Composable fun PortfolioScreen(navController: NavController) { /* Implementation */ }
@Composable fun CopyTradingScreen(navController: NavController) { /* Implementation */ }
@Composable fun NFTScreen(navController: NavController) { /* Implementation */ }
@Composable fun ProfileScreen(navController: NavController) { /* Implementation */ }
@Composable fun AdminScreen(navController: NavController) { /* Implementation */ }
