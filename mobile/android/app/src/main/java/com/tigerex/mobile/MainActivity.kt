package com.tigerex.mobile

import android.os.Bundle
import android.content.Intent
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tigerex.mobile.ui.theme.TigerExTheme
import com.tigerex.mobile.viewmodel.*
import com.tigerex.mobile.model.*
import com.tigerex.mobile.service.*
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.*

class MainActivity : ComponentActivity() {
    private lateinit var biometricPrompt: BiometricPrompt
    private lateinit var promptInfo: BiometricPrompt.PromptInfo
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setupBiometricAuthentication()
        
        setContent {
            TigerExTheme {
                TigerExApp()
            }
        }
    }
    
    private fun setupBiometricAuthentication() {
        val executor = ContextCompat.getMainExecutor(this)
        biometricPrompt = BiometricPrompt(this as FragmentActivity,
            executor, object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    super.onAuthenticationError(errorCode, errString)
                    Toast.makeText(applicationContext, "Authentication error: $errString", Toast.LENGTH_SHORT).show()
                }
                
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    Toast.makeText(applicationContext, "Authentication succeeded!", Toast.LENGTH_SHORT).show()
                }
                
                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    Toast.makeText(applicationContext, "Authentication failed", Toast.LENGTH_SHORT).show()
                }
            })
        
        promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("TigerEx Biometric Authentication")
            .setSubtitle("Log in using your biometric credential")
            .setNegativeButtonText("Use account password")
            .build()
    }
}

@Composable
fun TigerExApp() {
    val navController = rememberNavController()
    val authViewModel: AuthViewModel = viewModel()
    
    NavHost(navController = navController, startDestination = "splash") {
        composable("splash") { SplashScreen(navController, authViewModel) }
        composable("login") { LoginScreen(navController, authViewModel) }
        composable("register") { RegisterScreen(navController, authViewModel) }
        composable("main") { MainScreen(navController) }
        composable("trading") { TradingScreen(navController) }
        composable("portfolio") { PortfolioScreen(navController) }
        composable("wallet") { WalletScreen(navController) }
        composable("earn") { EarnScreen(navController) }
        composable("copy_trading") { CopyTradingScreen(navController) }
        composable("futures") { FuturesScreen(navController) }
        composable("options") { OptionsScreen(navController) }
        composable("nft") { NFTScreen(navController) }
        composable("defi") { DeFiScreen(navController) }
        composable("settings") { SettingsScreen(navController) }
    }
}

@Composable
fun SplashScreen(navController: NavController, authViewModel: AuthViewModel) {
    val context = LocalContext.current
    
    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(2000)
        if (authViewModel.isLoggedIn()) {
            navController.navigate("main") {
                popUpTo("splash") { inclusive = true }
            }
        } else {
            navController.navigate("login") {
                popUpTo("splash") { inclusive = true }
            }
        }
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1a1a1a)),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "TigerEx",
                fontSize = 48.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFFf97316)
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Advanced Crypto Trading Platform",
                fontSize = 16.sp,
                color = Color.White
            )
            Spacer(modifier = Modifier.height(32.dp))
            CircularProgressIndicator(color = Color(0xFFf97316))
        }
    }
}

@Composable
fun LoginScreen(navController: NavController, authViewModel: AuthViewModel) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1a1a1a))
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "Welcome Back",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            
            Text(
                text = "Sign in to your TigerEx account",
                fontSize = 16.sp,
                color = Color.Gray
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text("Email") },
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = Color(0xFFf97316),
                    unfocusedBorderColor = Color.Gray
                )
            )
            
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Password") },
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = Color(0xFFf97316),
                    unfocusedBorderColor = Color.Gray
                )
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            Button(
                onClick = {
                    scope.launch {
                        isLoading = true
                        val success = authViewModel.login(email, password)
                        isLoading = false
                        if (success) {
                            navController.navigate("main") {
                                popUpTo("login") { inclusive = true }
                            }
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFf97316)),
                enabled = !isLoading
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                } else {
                    Text("Sign In", fontSize = 18.sp, fontWeight = FontWeight.Medium)
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Row {
                Text("Don't have an account? ", color = Color.Gray)
                Text(
                    "Sign Up",
                    color = Color(0xFFf97316),
                    modifier = Modifier.clickable {
                        navController.navigate("register")
                    }
                )
            }
        }
    }
}

@Composable
fun MainScreen(navController: NavController) {
    val portfolioViewModel: PortfolioViewModel = viewModel()
    val marketViewModel: MarketViewModel = viewModel()
    
    LaunchedEffect(Unit) {
        portfolioViewModel.loadPortfolio()
        marketViewModel.loadMarketData()
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1a1a1a))
    ) {
        // Header
        TopAppBar(
            title = { Text("TigerEx", color = Color.White, fontWeight = FontWeight.Bold) },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF2a2a2a)),
            actions = {
                IconButton(onClick = { navController.navigate("settings") }) {
                    Icon(Icons.Default.Settings, contentDescription = "Settings", tint = Color.White)
                }
            }
        )
        
        LazyColumn(
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Portfolio Summary
            item {
                PortfolioSummaryCard(portfolioViewModel)
            }
            
            // Quick Actions
            item {
                QuickActionsGrid(navController)
            }
            
            // Market Overview
            item {
                MarketOverviewCard(marketViewModel)
            }
            
            // Recent Transactions
            item {
                RecentTransactionsCard()
            }
        }
        
        // Bottom Navigation
        BottomNavigationBar(navController)
    }
}

@Composable
fun PortfolioSummaryCard(portfolioViewModel: PortfolioViewModel) {
    val portfolio by portfolioViewModel.portfolio.collectAsState()
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "Portfolio Balance",
                fontSize = 16.sp,
                color = Color.Gray
            )
            
            Text(
                text = "$${NumberFormat.getNumberInstance(Locale.US).format(portfolio.totalValue)}",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("24h Change", fontSize = 12.sp, color = Color.Gray)
                    Text(
                        text = "${if (portfolio.change24h >= 0) "+" else ""}${String.format("%.2f", portfolio.change24h)}%",
                        fontSize = 14.sp,
                        color = if (portfolio.change24h >= 0) Color.Green else Color.Red,
                        fontWeight = FontWeight.Medium
                    )
                }
                
                Column {
                    Text("P&L", fontSize = 12.sp, color = Color.Gray)
                    Text(
                        text = "${if (portfolio.pnl >= 0) "+" else ""}$${String.format("%.2f", portfolio.pnl)}",
                        fontSize = 14.sp,
                        color = if (portfolio.pnl >= 0) Color.Green else Color.Red,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
fun QuickActionsGrid(navController: NavController) {
    val actions = listOf(
        QuickAction("Spot Trading", Icons.Default.TrendingUp, "trading"),
        QuickAction("Futures", Icons.Default.ShowChart, "futures"),
        QuickAction("Options", Icons.Default.Analytics, "options"),
        QuickAction("Copy Trading", Icons.Default.ContentCopy, "copy_trading"),
        QuickAction("Earn", Icons.Default.Savings, "earn"),
        QuickAction("NFT", Icons.Default.Image, "nft"),
        QuickAction("DeFi", Icons.Default.AccountBalance, "defi"),
        QuickAction("Wallet", Icons.Default.Wallet, "wallet")
    )
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "Quick Actions",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            
            for (row in actions.chunked(4)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    for (action in row) {
                        QuickActionItem(
                            action = action,
                            onClick = { navController.navigate(action.route) },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    // Fill remaining slots if row is not complete
                    repeat(4 - row.size) {
                        Spacer(modifier = Modifier.weight(1f))
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}

@Composable
fun QuickActionItem(
    action: QuickAction,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .clickable { onClick() }
            .padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .background(
                    Color(0xFFf97316).copy(alpha = 0.1f),
                    RoundedCornerShape(12.dp)
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = action.icon,
                contentDescription = action.title,
                tint = Color(0xFFf97316),
                modifier = Modifier.size(24.dp)
            )
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = action.title,
            fontSize = 12.sp,
            color = Color.White,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
fun MarketOverviewCard(marketViewModel: MarketViewModel) {
    val marketData by marketViewModel.marketData.collectAsState()
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "Market Overview",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            
            LazyColumn(
                modifier = Modifier.height(200.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(marketData.topCoins) { coin ->
                    MarketCoinItem(coin)
                }
            }
        }
    }
}

@Composable
fun MarketCoinItem(coin: CoinData) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = coin.symbol,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                color = Color.White
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = coin.name,
                fontSize = 12.sp,
                color = Color.Gray
            )
        }
        
        Column(horizontalAlignment = Alignment.End) {
            Text(
                text = "$${String.format("%.4f", coin.price)}",
                fontSize = 14.sp,
                color = Color.White
            )
            Text(
                text = "${if (coin.change24h >= 0) "+" else ""}${String.format("%.2f", coin.change24h)}%",
                fontSize = 12.sp,
                color = if (coin.change24h >= 0) Color.Green else Color.Red
            )
        }
    }
}

@Composable
fun RecentTransactionsCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF2a2a2a)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Recent Transactions",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                
                Text(
                    text = "View All",
                    fontSize = 14.sp,
                    color = Color(0xFFf97316),
                    modifier = Modifier.clickable { /* Navigate to transactions */ }
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Mock transaction data
            val transactions = listOf(
                Transaction("BTC", "Buy", 0.5, 45000.0, "Completed"),
                Transaction("ETH", "Sell", 2.0, 3000.0, "Completed"),
                Transaction("BNB", "Buy", 10.0, 300.0, "Pending")
            )
            
            transactions.forEach { transaction ->
                TransactionItem(transaction)
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
fun TransactionItem(transaction: Transaction) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = if (transaction.type == "Buy") Icons.Default.TrendingUp else Icons.Default.TrendingDown,
                contentDescription = transaction.type,
                tint = if (transaction.type == "Buy") Color.Green else Color.Red,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = "${transaction.type} ${transaction.symbol}",
                    fontSize = 14.sp,
                    color = Color.White,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    text = "${transaction.amount} ${transaction.symbol}",
                    fontSize = 12.sp,
                    color = Color.Gray
                )
            }
        }
        
        Column(horizontalAlignment = Alignment.End) {
            Text(
                text = "$${String.format("%.2f", transaction.price * transaction.amount)}",
                fontSize = 14.sp,
                color = Color.White
            )
            Text(
                text = transaction.status,
                fontSize = 12.sp,
                color = when (transaction.status) {
                    "Completed" -> Color.Green
                    "Pending" -> Color.Yellow
                    else -> Color.Red
                }
            )
        }
    }
}

@Composable
fun BottomNavigationBar(navController: NavController) {
    val items = listOf(
        BottomNavItem("Home", Icons.Default.Home, "main"),
        BottomNavItem("Trading", Icons.Default.TrendingUp, "trading"),
        BottomNavItem("Portfolio", Icons.Default.PieChart, "portfolio"),
        BottomNavItem("Wallet", Icons.Default.Wallet, "wallet"),
        BottomNavItem("More", Icons.Default.MoreHoriz, "settings")
    )
    
    NavigationBar(
        containerColor = Color(0xFF2a2a2a),
        contentColor = Color.White
    ) {
        items.forEach { item ->
            NavigationBarItem(
                icon = { Icon(item.icon, contentDescription = item.label) },
                label = { Text(item.label, fontSize = 12.sp) },
                selected = false, // You can implement selection logic here
                onClick = { navController.navigate(item.route) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = Color(0xFFf97316),
                    selectedTextColor = Color(0xFFf97316),
                    unselectedIconColor = Color.Gray,
                    unselectedTextColor = Color.Gray
                )
            )
        }
    }
}

// Data classes
data class QuickAction(
    val title: String,
    val icon: ImageVector,
    val route: String
)

data class BottomNavItem(
    val label: String,
    val icon: ImageVector,
    val route: String
)

data class Transaction(
    val symbol: String,
    val type: String,
    val amount: Double,
    val price: Double,
    val status: String
)

data class CoinData(
    val symbol: String,
    val name: String,
    val price: Double,
    val change24h: Double
)

data class Portfolio(
    val totalValue: Double = 0.0,
    val change24h: Double = 0.0,
    val pnl: Double = 0.0
)

data class MarketData(
    val topCoins: List<CoinData> = emptyList()
)
