package com.tigerex.mobile

import android.os.Bundle
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import androidx.viewpager2.adapter.FragmentStateAdapter
import androidx.viewpager2.widget.ViewPager2
import com.google.android.material.tabs.TabLayout
import com.google.android.material.tabs.TabLayoutMediator
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.snackbar.Snackbar
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.io.IOException
import java.math.BigDecimal
import java.math.RoundingMode
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.Executors
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.IvParameterSpec
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore

/**
 * TigerEx Mobile Trading Activity
 * Advanced Kotlin-based mobile trading interface with biometric authentication,
 * real-time market data, and comprehensive trading features
 */
class TradingActivity : AppCompatActivity() {
    
    private lateinit var viewModel: TradingViewModel
    private lateinit var webSocketManager: WebSocketManager
    private lateinit var biometricPrompt: BiometricPrompt
    private lateinit var promptInfo: BiometricPrompt.PromptInfo
    private lateinit var securityManager: SecurityManager
    
    // UI Components
    private lateinit var viewPager: ViewPager2
    private lateinit var tabLayout: TabLayout
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var marketRecyclerView: RecyclerView
    private lateinit var balanceTextView: TextView
    private lateinit var pnlTextView: TextView
    private lateinit var tradingButton: Button
    
    // Adapters
    private lateinit var marketAdapter: MarketAdapter
    private lateinit var pagerAdapter: TradingPagerAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_trading)
        
        initializeComponents()
        setupUI()
        setupBiometricAuthentication()
        setupWebSocket()
        observeViewModel()
        
        // Load initial data
        viewModel.loadMarketData()
        viewModel.loadUserBalance()
    }
    
    private fun initializeComponents() {
        viewModel = ViewModelProvider(this)[TradingViewModel::class.java]
        webSocketManager = WebSocketManager()
        securityManager = SecurityManager(this)
        
        // Initialize UI components
        viewPager = findViewById(R.id.viewPager)
        tabLayout = findViewById(R.id.tabLayout)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        marketRecyclerView = findViewById(R.id.marketRecyclerView)
        balanceTextView = findViewById(R.id.balanceTextView)
        pnlTextView = findViewById(R.id.pnlTextView)
        tradingButton = findViewById(R.id.tradingButton)
    }
    
    private fun setupUI() {
        // Setup ViewPager with fragments
        pagerAdapter = TradingPagerAdapter(this)
        viewPager.adapter = pagerAdapter
        
        // Setup TabLayout
        TabLayoutMediator(tabLayout, viewPager) { tab, position ->
            tab.text = when (position) {
                0 -> "Spot"
                1 -> "Futures"
                2 -> "Options"
                3 -> "Copy Trading"
                4 -> "Earn"
                else -> "Tab $position"
            }
        }.attach()
        
        // Setup Market RecyclerView
        marketAdapter = MarketAdapter { market ->
            onMarketSelected(market)
        }
        marketRecyclerView.apply {
            layoutManager = LinearLayoutManager(this@TradingActivity)
            adapter = marketAdapter
        }
        
        // Setup SwipeRefresh
        swipeRefresh.setOnRefreshListener {
            viewModel.refreshData()
        }
        
        // Setup Trading Button
        tradingButton.setOnClickListener {
            showTradingBottomSheet()
        }
    }
    
    private fun setupBiometricAuthentication() {
        val biometricManager = BiometricManager.from(this)
        
        when (biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK)) {
            BiometricManager.BIOMETRIC_SUCCESS -> {
                setupBiometricPrompt()
            }
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> {
                showMessage("No biometric features available on this device")
            }
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> {
                showMessage("Biometric features are currently unavailable")
            }
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> {
                showMessage("Please enroll biometric credentials in device settings")
            }
        }
    }
    
    private fun setupBiometricPrompt() {
        val executor = ContextCompat.getMainExecutor(this)
        
        biometricPrompt = BiometricPrompt(this, executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    super.onAuthenticationError(errorCode, errString)
                    showMessage("Authentication error: $errString")
                }
                
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    showMessage("Authentication succeeded!")
                    // Proceed with secure operations
                    enableTradingFeatures()
                }
                
                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    showMessage("Authentication failed")
                }
            })
        
        promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Biometric Authentication")
            .setSubtitle("Use your fingerprint or face to authenticate")
            .setNegativeButtonText("Use PIN")
            .build()
    }
    
    private fun setupWebSocket() {
        webSocketManager.connect("wss://api.tigerex.com/ws") { message ->
            runOnUiThread {
                handleWebSocketMessage(message)
            }
        }
    }
    
    private fun observeViewModel() {
        viewModel.marketData.observe(this) { markets ->
            marketAdapter.updateMarkets(markets)
            swipeRefresh.isRefreshing = false
        }
        
        viewModel.userBalance.observe(this) { balance ->
            balanceTextView.text = "Balance: ${formatCurrency(balance.totalBalance)}"
        }
        
        viewModel.pnl.observe(this) { pnl ->
            pnlTextView.text = "P&L: ${formatCurrency(pnl)}"
            pnlTextView.setTextColor(
                if (pnl >= BigDecimal.ZERO) 
                    ContextCompat.getColor(this, R.color.green) 
                else 
                    ContextCompat.getColor(this, R.color.red)
            )
        }
        
        viewModel.loading.observe(this) { isLoading ->
            // Show/hide loading indicators
        }
        
        viewModel.error.observe(this) { error ->
            error?.let { showMessage(it) }
        }
    }
    
    private fun onMarketSelected(market: Market) {
        viewModel.selectMarket(market)
        webSocketManager.subscribe("ticker@${market.symbol.lowercase()}")
    }
    
    private fun showTradingBottomSheet() {
        // Require biometric authentication for trading
        biometricPrompt.authenticate(promptInfo)
    }
    
    private fun enableTradingFeatures() {
        val bottomSheetDialog = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.bottom_sheet_trading, null)
        bottomSheetDialog.setContentView(view)
        
        setupTradingBottomSheet(view, bottomSheetDialog)
        bottomSheetDialog.show()
    }
    
    private fun setupTradingBottomSheet(view: View, dialog: BottomSheetDialog) {
        val symbolSpinner = view.findViewById<Spinner>(R.id.symbolSpinner)
        val sideChipGroup = view.findViewById<ChipGroup>(R.id.sideChipGroup)
        val typeChipGroup = view.findViewById<ChipGroup>(R.id.typeChipGroup)
        val quantityEditText = view.findViewById<EditText>(R.id.quantityEditText)
        val priceEditText = view.findViewById<EditText>(R.id.priceEditText)
        val percentageChipGroup = view.findViewById<ChipGroup>(R.id.percentageChipGroup)
        val placeOrderButton = view.findViewById<Button>(R.id.placeOrderButton)
        
        // Setup symbol spinner
        val symbols = viewModel.marketData.value?.map { it.symbol } ?: emptyList()
        val symbolAdapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, symbols)
        symbolSpinner.adapter = symbolAdapter
        
        // Setup percentage chips
        val percentages = listOf(25, 50, 75, 100)
        percentages.forEach { percentage ->
            val chip = Chip(this)
            chip.text = "$percentage%"
            chip.isCheckable = true
            chip.setOnClickListener {
                calculateQuantityByPercentage(percentage, quantityEditText)
            }
            percentageChipGroup.addView(chip)
        }
        
        // Setup place order button
        placeOrderButton.setOnClickListener {
            val selectedSymbol = symbolSpinner.selectedItem as? String ?: return@setOnClickListener
            val side = getSelectedChipText(sideChipGroup) ?: return@setOnClickListener
            val type = getSelectedChipText(typeChipGroup) ?: return@setOnClickListener
            val quantity = quantityEditText.text.toString().toBigDecimalOrNull() ?: return@setOnClickListener
            val price = if (type == "MARKET") null else priceEditText.text.toString().toBigDecimalOrNull()
            
            val order = OrderRequest(
                symbol = selectedSymbol,
                side = side,
                type = type,
                quantity = quantity,
                price = price
            )
            
            viewModel.placeOrder(order)
            dialog.dismiss()
        }
    }
    
    private fun getSelectedChipText(chipGroup: ChipGroup): String? {
        val selectedChipId = chipGroup.checkedChipId
        return if (selectedChipId != View.NO_ID) {
            findViewById<Chip>(selectedChipId).text.toString()
        } else null
    }
    
    private fun calculateQuantityByPercentage(percentage: Int, quantityEditText: EditText) {
        val balance = viewModel.userBalance.value?.availableBalance ?: BigDecimal.ZERO
        val currentPrice = viewModel.selectedMarket.value?.price ?: BigDecimal.ZERO
        
        if (currentPrice > BigDecimal.ZERO) {
            val quantity = balance.multiply(BigDecimal(percentage))
                .divide(BigDecimal(100), 8, RoundingMode.DOWN)
                .divide(currentPrice, 8, RoundingMode.DOWN)
            
            quantityEditText.setText(quantity.toPlainString())
        }
    }
    
    private fun handleWebSocketMessage(message: String) {
        try {
            val gson = Gson()
            val wsMessage = gson.fromJson(message, WebSocketMessage::class.java)
            
            when (wsMessage.type) {
                "ticker" -> {
                    val ticker = gson.fromJson(wsMessage.data, TickerData::class.java)
                    viewModel.updateTicker(ticker)
                }
                "orderbook" -> {
                    val orderBook = gson.fromJson(wsMessage.data, OrderBookData::class.java)
                    viewModel.updateOrderBook(orderBook)
                }
                "trade" -> {
                    val trade = gson.fromJson(wsMessage.data, TradeData::class.java)
                    viewModel.addTrade(trade)
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun formatCurrency(amount: BigDecimal): String {
        val formatter = NumberFormat.getCurrencyInstance(Locale.US)
        return formatter.format(amount)
    }
    
    private fun showMessage(message: String) {
        Snackbar.make(findViewById(android.R.id.content), message, Snackbar.LENGTH_LONG).show()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        webSocketManager.disconnect()
    }
}

/**
 * ViewPager adapter for trading fragments
 */
class TradingPagerAdapter(fragmentActivity: FragmentActivity) : FragmentStateAdapter(fragmentActivity) {
    
    override fun getItemCount(): Int = 5
    
    override fun createFragment(position: Int): Fragment {
        return when (position) {
            0 -> SpotTradingFragment()
            1 -> FuturesTradingFragment()
            2 -> OptionsTradingFragment()
            3 -> CopyTradingFragment()
            4 -> EarnFragment()
            else -> SpotTradingFragment()
        }
    }
}

/**
 * Market adapter for RecyclerView
 */
class MarketAdapter(private val onMarketClick: (Market) -> Unit) : RecyclerView.Adapter<MarketAdapter.MarketViewHolder>() {
    
    private var markets = listOf<Market>()
    
    fun updateMarkets(newMarkets: List<Market>) {
        markets = newMarkets
        notifyDataSetChanged()
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MarketViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_market, parent, false)
        return MarketViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: MarketViewHolder, position: Int) {
        holder.bind(markets[position])
    }
    
    override fun getItemCount(): Int = markets.size
    
    inner class MarketViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val symbolTextView: TextView = itemView.findViewById(R.id.symbolTextView)
        private val priceTextView: TextView = itemView.findViewById(R.id.priceTextView)
        private val changeTextView: TextView = itemView.findViewById(R.id.changeTextView)
        private val volumeTextView: TextView = itemView.findViewById(R.id.volumeTextView)
        
        fun bind(market: Market) {
            symbolTextView.text = market.symbol
            priceTextView.text = "$${market.price}"
            changeTextView.text = "${if (market.change24h >= BigDecimal.ZERO) "+" else ""}${market.change24h}%"
            volumeTextView.text = "Vol: ${market.volume24h}"
            
            changeTextView.setTextColor(
                if (market.change24h >= BigDecimal.ZERO)
                    ContextCompat.getColor(itemView.context, R.color.green)
                else
                    ContextCompat.getColor(itemView.context, R.color.red)
            )
            
            itemView.setOnClickListener {
                onMarketClick(market)
            }
        }
    }
}

/**
 * WebSocket manager for real-time data
 */
class WebSocketManager {
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .build()
    
    fun connect(url: String, onMessage: (String) -> Unit) {
        val request = Request.Builder()
            .url(url)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                println("WebSocket connected")
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                onMessage(text)
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                println("WebSocket closing: $reason")
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                println("WebSocket error: ${t.message}")
            }
        })
    }
    
    fun subscribe(channel: String) {
        val message = """
            {
                "method": "subscribe",
                "params": {
                    "channel": "$channel"
                }
            }
        """.trimIndent()
        
        webSocket?.send(message)
    }
    
    fun disconnect() {
        webSocket?.close(1000, "Closing connection")
    }
}

/**
 * Security manager for encryption and secure storage
 */
class SecurityManager(private val context: Context) {
    private val keyAlias = "TigerExSecretKey"
    
    init {
        generateSecretKey()
    }
    
    private fun generateSecretKey() {
        val keyGenerator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        val keyGenParameterSpec = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_CBC)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_PKCS7)
            .build()
        
        keyGenerator.init(keyGenParameterSpec)
        keyGenerator.generateKey()
    }
    
    fun encrypt(data: String): Pair<ByteArray, ByteArray> {
        val keyStore = KeyStore.getInstance("AndroidKeyStore")
        keyStore.load(null)
        
        val secretKey = keyStore.getKey(keyAlias, null) as SecretKey
        val cipher = Cipher.getInstance("AES/CBC/PKCS7Padding")
        cipher.init(Cipher.ENCRYPT_MODE, secretKey)
        
        val iv = cipher.iv
        val encryptedData = cipher.doFinal(data.toByteArray())
        
        return Pair(encryptedData, iv)
    }
    
    fun decrypt(encryptedData: ByteArray, iv: ByteArray): String {
        val keyStore = KeyStore.getInstance("AndroidKeyStore")
        keyStore.load(null)
        
        val secretKey = keyStore.getKey(keyAlias, null) as SecretKey
        val cipher = Cipher.getInstance("AES/CBC/PKCS7Padding")
        cipher.init(Cipher.DECRYPT_MODE, secretKey, IvParameterSpec(iv))
        
        val decryptedData = cipher.doFinal(encryptedData)
        return String(decryptedData)
    }
}

/**
 * Data classes for API responses and WebSocket messages
 */
data class Market(
    val symbol: String,
    val price: BigDecimal,
    val change24h: BigDecimal,
    val volume24h: BigDecimal,
    val high24h: BigDecimal,
    val low24h: BigDecimal
)

data class UserBalance(
    val totalBalance: BigDecimal,
    val availableBalance: BigDecimal,
    val lockedBalance: BigDecimal,
    val assets: List<AssetBalance>
)

data class AssetBalance(
    val asset: String,
    val available: BigDecimal,
    val locked: BigDecimal
)

data class OrderRequest(
    val symbol: String,
    val side: String,
    val type: String,
    val quantity: BigDecimal,
    val price: BigDecimal? = null,
    val timeInForce: String = "GTC"
)

data class OrderResponse(
    val orderId: String,
    val status: String,
    val symbol: String,
    val side: String,
    val type: String,
    val quantity: BigDecimal,
    val price: BigDecimal?,
    val createdAt: Long
)

data class WebSocketMessage(
    val type: String,
    val data: String
)

data class TickerData(
    val symbol: String,
    val price: BigDecimal,
    val change24h: BigDecimal,
    val volume24h: BigDecimal
)

data class OrderBookData(
    val symbol: String,
    val bids: List<OrderBookEntry>,
    val asks: List<OrderBookEntry>
)

data class OrderBookEntry(
    val price: BigDecimal,
    val quantity: BigDecimal
)

data class TradeData(
    val symbol: String,
    val price: BigDecimal,
    val quantity: BigDecimal,
    val side: String,
    val timestamp: Long
)

/**
 * API service interface using Retrofit
 */
interface TigerExApiService {
    
    @GET("api/v1/market/ticker")
    suspend fun getMarketData(): List<Market>
    
    @GET("api/v1/account/balance")
    suspend fun getUserBalance(@Header("Authorization") token: String): UserBalance
    
    @POST("api/v1/order")
    suspend fun placeOrder(
        @Header("Authorization") token: String,
        @Body order: OrderRequest
    ): OrderResponse
    
    @GET("api/v1/orders/open")
    suspend fun getOpenOrders(@Header("Authorization") token: String): List<OrderResponse>
    
    @DELETE("api/v1/order")
    suspend fun cancelOrder(
        @Header("Authorization") token: String,
        @Query("orderId") orderId: String
    ): Boolean
}

/**
 * Repository for API calls
 */
class TradingRepository {
    private val apiService: TigerExApiService
    
    init {
        val retrofit = Retrofit.Builder()
            .baseUrl("https://api.tigerex.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .client(
                OkHttpClient.Builder()
                    .addInterceptor(HttpLoggingInterceptor().apply {
                        level = HttpLoggingInterceptor.Level.BODY
                    })
                    .build()
            )
            .build()
        
        apiService = retrofit.create(TigerExApiService::class.java)
    }
    
    suspend fun getMarketData(): List<Market> {
        return apiService.getMarketData()
    }
    
    suspend fun getUserBalance(token: String): UserBalance {
        return apiService.getUserBalance("Bearer $token")
    }
    
    suspend fun placeOrder(token: String, order: OrderRequest): OrderResponse {
        return apiService.placeOrder("Bearer $token", order)
    }
    
    suspend fun getOpenOrders(token: String): List<OrderResponse> {
        return apiService.getOpenOrders("Bearer $token")
    }
    
    suspend fun cancelOrder(token: String, orderId: String): Boolean {
        return apiService.cancelOrder("Bearer $token", orderId)
    }
}

/**
 * ViewModel for trading activity
 */
class TradingViewModel : ViewModel() {
    private val repository = TradingRepository()
    private val _marketData = MutableLiveData<List<Market>>()
    private val _userBalance = MutableLiveData<UserBalance>()
    private val _pnl = MutableLiveData<BigDecimal>()
    private val _selectedMarket = MutableLiveData<Market>()
    private val _loading = MutableLiveData<Boolean>()
    private val _error = MutableLiveData<String>()
    
    val marketData: LiveData<List<Market>> = _marketData
    val userBalance: LiveData<UserBalance> = _userBalance
    val pnl: LiveData<BigDecimal> = _pnl
    val selectedMarket: LiveData<Market> = _selectedMarket
    val loading: LiveData<Boolean> = _loading
    val error: LiveData<String> = _error
    
    private val coroutineScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    fun loadMarketData() {
        coroutineScope.launch {
            try {
                _loading.value = true
                val markets = withContext(Dispatchers.IO) {
                    repository.getMarketData()
                }
                _marketData.value = markets
            } catch (e: Exception) {
                _error.value = "Failed to load market data: ${e.message}"
            } finally {
                _loading.value = false
            }
        }
    }
    
    fun loadUserBalance() {
        coroutineScope.launch {
            try {
                val token = getAuthToken() ?: return@launch
                val balance = withContext(Dispatchers.IO) {
                    repository.getUserBalance(token)
                }
                _userBalance.value = balance
                calculatePnL(balance)
            } catch (e: Exception) {
                _error.value = "Failed to load balance: ${e.message}"
            }
        }
    }
    
    fun placeOrder(order: OrderRequest) {
        coroutineScope.launch {
            try {
                _loading.value = true
                val token = getAuthToken() ?: return@launch
                val response = withContext(Dispatchers.IO) {
                    repository.placeOrder(token, order)
                }
                // Handle successful order placement
                loadUserBalance() // Refresh balance
            } catch (e: Exception) {
                _error.value = "Failed to place order: ${e.message}"
            } finally {
                _loading.value = false
            }
        }
    }
    
    fun selectMarket(market: Market) {
        _selectedMarket.value = market
    }
    
    fun updateTicker(ticker: TickerData) {
        val currentMarkets = _marketData.value?.toMutableList() ?: return
        val index = currentMarkets.indexOfFirst { it.symbol == ticker.symbol }
        if (index != -1) {
            currentMarkets[index] = currentMarkets[index].copy(
                price = ticker.price,
                change24h = ticker.change24h,
                volume24h = ticker.volume24h
            )
            _marketData.value = currentMarkets
        }
    }
    
    fun updateOrderBook(orderBook: OrderBookData) {
        // Update order book data
    }
    
    fun addTrade(trade: TradeData) {
        // Add new trade to trade history
    }
    
    fun refreshData() {
        loadMarketData()
        loadUserBalance()
    }
    
    private fun calculatePnL(balance: UserBalance) {
        // Calculate P&L based on current positions and market prices
        _pnl.value = BigDecimal.ZERO // Placeholder
    }
    
    private fun getAuthToken(): String? {
        // Get authentication token from secure storage
        return "dummy_token" // Placeholder
    }
    
    override fun onCleared() {
        super.onCleared()
        coroutineScope.cancel()
    }
}