//
//  ContentView.swift
//  TigerEx iOS App
//  Comprehensive iOS trading application with all major exchange features
//

import SwiftUI
import Combine
import LocalAuthentication
import CryptoKit
import Network
import WebKit
import Charts

@main
struct TigerExApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @StateObject private var authManager = AuthenticationManager()
    @StateObject private var tradingManager = TradingManager()
    @StateObject private var portfolioManager = PortfolioManager()
    @StateObject private var webSocketManager = WebSocketManager()
    @StateObject private var biometricManager = BiometricManager()
    
    var body: some View {
        Group {
            if authManager.isAuthenticated {
                MainTradingView()
                    .environmentObject(authManager)
                    .environmentObject(tradingManager)
                    .environmentObject(portfolioManager)
                    .environmentObject(webSocketManager)
            } else {
                LoginView()
                    .environmentObject(authManager)
                    .environmentObject(biometricManager)
            }
        }
        .onAppear {
            setupApp()
        }
    }
    
    private func setupApp() {
        webSocketManager.connect()
        if authManager.isAuthenticated {
            tradingManager.loadInitialData()
            portfolioManager.loadPortfolio()
        }
    }
}

// MARK: - Authentication Manager
class AuthenticationManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var requires2FA = false
    
    private let apiService = APIService.shared
    private let keychainManager = KeychainManager()
    
    init() {
        checkAuthenticationStatus()
    }
    
    func checkAuthenticationStatus() {
        if let token = keychainManager.getAccessToken() {
            validateToken(token)
        }
    }
    
    func login(email: String, password: String, totpCode: String? = nil) {
        isLoading = true
        errorMessage = nil
        
        let loginRequest = LoginRequest(email: email, password: password, totpCode: totpCode)
        
        apiService.login(request: loginRequest) { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let response):
                    if response.requires2FA && totpCode == nil {
                        self?.requires2FA = true
                        self?.errorMessage = "2FA code required"
                    } else {
                        self?.keychainManager.saveAccessToken(response.accessToken)
                        self?.keychainManager.saveCredentials(email: email, password: password)
                        self?.currentUser = response.user
                        self?.isAuthenticated = true
                        self?.requires2FA = false
                    }
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func logout() {
        keychainManager.deleteAccessToken()
        keychainManager.deleteCredentials()
        currentUser = nil
        isAuthenticated = false
        requires2FA = false
    }
    
    private func validateToken(_ token: String) {
        apiService.validateToken(token) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let user):
                    self?.currentUser = user
                    self?.isAuthenticated = true
                case .failure:
                    self?.logout()
                }
            }
        }
    }
}

// MARK: - Trading Manager
class TradingManager: ObservableObject {
    @Published var markets: [Market] = []
    @Published var selectedMarket: Market?
    @Published var orderBook: OrderBook?
    @Published var recentTrades: [RecentTrade] = []
    @Published var openOrders: [Order] = []
    @Published var orderHistory: [Order] = []
    @Published var chartData: [ChartDataPoint] = []
    @Published var selectedTimeframe: Timeframe = .oneHour
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    private var cancellables = Set<AnyCancellable>()
    
    enum Timeframe: String, CaseIterable {
        case oneMinute = "1m"
        case fiveMinutes = "5m"
        case fifteenMinutes = "15m"
        case oneHour = "1h"
        case fourHours = "4h"
        case oneDay = "1d"
        case oneWeek = "1w"
        
        var displayName: String {
            switch self {
            case .oneMinute: return "1m"
            case .fiveMinutes: return "5m"
            case .fifteenMinutes: return "15m"
            case .oneHour: return "1h"
            case .fourHours: return "4h"
            case .oneDay: return "1d"
            case .oneWeek: return "1w"
            }
        }
    }
    
    func loadInitialData() {
        loadMarkets()
        loadOpenOrders()
        loadOrderHistory()
    }
    
    func loadMarkets() {
        isLoading = true
        
        apiService.getMarkets { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let markets):
                    self?.markets = markets
                    if self?.selectedMarket == nil && !markets.isEmpty {
                        self?.selectMarket(markets[0])
                    }
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func selectMarket(_ market: Market) {
        selectedMarket = market
        loadOrderBook(for: market.symbol)
        loadRecentTrades(for: market.symbol)
        loadChartData(for: market.symbol, timeframe: selectedTimeframe)
    }
    
    func loadOrderBook(for symbol: String) {
        apiService.getOrderBook(symbol: symbol) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let orderBook):
                    self?.orderBook = orderBook
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func loadRecentTrades(for symbol: String) {
        apiService.getRecentTrades(symbol: symbol) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let trades):
                    self?.recentTrades = trades
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func loadChartData(for symbol: String, timeframe: Timeframe) {
        apiService.getChartData(symbol: symbol, timeframe: timeframe.rawValue) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let chartData):
                    self?.chartData = chartData
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func loadOpenOrders() {
        apiService.getOpenOrders { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let orders):
                    self?.openOrders = orders
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func loadOrderHistory() {
        apiService.getOrderHistory { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let orders):
                    self?.orderHistory = orders
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func placeOrder(_ orderRequest: OrderRequest) {
        apiService.placeOrder(request: orderRequest) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let order):
                    self?.openOrders.append(order)
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func cancelOrder(_ orderId: String) {
        apiService.cancelOrder(orderId: orderId) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    self?.openOrders.removeAll { $0.id == orderId }
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func changeTimeframe(_ timeframe: Timeframe) {
        selectedTimeframe = timeframe
        if let symbol = selectedMarket?.symbol {
            loadChartData(for: symbol, timeframe: timeframe)
        }
    }
}

// MARK: - Portfolio Manager
class PortfolioManager: ObservableObject {
    @Published var totalBalance: Decimal = 0
    @Published var availableBalance: Decimal = 0
    @Published var totalPnL: Decimal = 0
    @Published var dailyPnL: Decimal = 0
    @Published var portfolioChange24h: Double = 0
    @Published var assets: [AssetBalance] = []
    @Published var positions: [Position] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    
    func loadPortfolio() {
        isLoading = true
        
        apiService.getPortfolio { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let portfolio):
                    self?.totalBalance = portfolio.totalBalance
                    self?.availableBalance = portfolio.availableBalance
                    self?.totalPnL = portfolio.totalPnL
                    self?.dailyPnL = portfolio.dailyPnL
                    self?.portfolioChange24h = portfolio.change24h
                    self?.assets = portfolio.assets
                    self?.positions = portfolio.positions
                case .failure(let error):
                    self?.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func refreshPortfolio() {
        loadPortfolio()
    }
}

// MARK: - WebSocket Manager
class WebSocketManager: ObservableObject {
    @Published var isConnected = false
    @Published var tickerData: [String: TickerData] = [:]
    @Published var orderBookUpdates: [String: OrderBookUpdate] = [:]
    @Published var tradeUpdates: [TradeUpdate] = []
    
    private var webSocketTask: URLSessionWebSocketTask?
    private let urlSession = URLSession.shared
    private var reconnectTimer: Timer?
    
    func connect() {
        guard let url = URL(string: "wss://api.tigerex.com/ws") else { return }
        
        webSocketTask = urlSession.webSocketTask(with: url)
        webSocketTask?.resume()
        
        receiveMessage()
        isConnected = true
        
        // Setup reconnection logic
        setupReconnection()
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        reconnectTimer?.invalidate()
        isConnected = false
    }
    
    private func setupReconnection() {
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            if self?.isConnected == false {
                self?.connect()
            }
        }
    }
    
    func subscribe(to channel: String) {
        let subscribeMessage = WebSocketMessage(
            method: "subscribe",
            params: ["channel": channel]
        )
        sendMessage(subscribeMessage)
    }
    
    private func sendMessage(_ message: WebSocketMessage) {
        guard let data = try? JSONEncoder().encode(message) else { return }
        let string = String(data: data, encoding: .utf8) ?? ""
        
        webSocketTask?.send(.string(string)) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self?.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                self?.receiveMessage()
                
            case .failure(let error):
                print("WebSocket receive error: \(error)")
                DispatchQueue.main.async {
                    self?.isConnected = false
                }
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let message = try? JSONDecoder().decode(WebSocketResponse.self, from: data) else {
            return
        }
        
        DispatchQueue.main.async {
            switch message.type {
            case "ticker":
                if let tickerData = try? JSONDecoder().decode(TickerData.self, from: message.data) {
                    self.tickerData[tickerData.symbol] = tickerData
                }
            case "orderbook":
                if let orderBookUpdate = try? JSONDecoder().decode(OrderBookUpdate.self, from: message.data) {
                    self.orderBookUpdates[orderBookUpdate.symbol] = orderBookUpdate
                }
            case "trade":
                if let tradeUpdate = try? JSONDecoder().decode(TradeUpdate.self, from: message.data) {
                    self.tradeUpdates.append(tradeUpdate)
                    if self.tradeUpdates.count > 100 {
                        self.tradeUpdates.removeFirst()
                    }
                }
            default:
                break
            }
        }
    }
}

// MARK: - Biometric Manager
class BiometricManager: ObservableObject {
    @Published var isBiometricAvailable = false
    @Published var biometricType: LABiometryType = .none
    
    private let context = LAContext()
    
    init() {
        checkBiometricAvailability()
    }
    
    func checkBiometricAvailability() {
        var error: NSError?
        
        if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
            isBiometricAvailable = true
            biometricType = context.biometryType
        } else {
            isBiometricAvailable = false
        }
    }
    
    func authenticateWithBiometrics(completion: @escaping (Bool, Error?) -> Void) {
        let reason = "Authenticate to access your TigerEx account"
        
        context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, error in
            DispatchQueue.main.async {
                completion(success, error)
            }
        }
    }
}

// MARK: - Login View
struct LoginView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @EnvironmentObject var biometricManager: BiometricManager
    
    @State private var email = ""
    @State private var password = ""
    @State private var totpCode = ""
    @State private var showPassword = false
    
    var body: some View {
        GeometryReader { geometry in
            ScrollView {
                VStack(spacing: 30) {
                    Spacer(minLength: 50)
                    
                    // Logo and Title
                    VStack(spacing: 16) {
                        Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                            .font(.system(size: 80))
                            .foregroundColor(.orange)
                        
                        Text("TigerEx")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        
                        Text("Advanced Crypto Trading Platform")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    // Login Form
                    VStack(spacing: 20) {
                        // Email Field
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Email")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            TextField("Enter your email", text: $email)
                                .textFieldStyle(CustomTextFieldStyle())
                                .keyboardType(.emailAddress)
                                .autocapitalization(.none)
                        }
                        
                        // Password Field
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Password")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            HStack {
                                if showPassword {
                                    TextField("Enter your password", text: $password)
                                } else {
                                    SecureField("Enter your password", text: $password)
                                }
                                
                                Button(action: { showPassword.toggle() }) {
                                    Image(systemName: showPassword ? "eye.slash" : "eye")
                                        .foregroundColor(.secondary)
                                }
                            }
                            .textFieldStyle(CustomTextFieldStyle())
                        }
                        
                        // 2FA Field (if required)
                        if authManager.requires2FA {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("2FA Code")
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                
                                TextField("Enter 6-digit code", text: $totpCode)
                                    .textFieldStyle(CustomTextFieldStyle())
                                    .keyboardType(.numberPad)
                            }
                        }
                        
                        // Login Button
                        Button(action: login) {
                            HStack {
                                if authManager.isLoading {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                        .scaleEffect(0.8)
                                } else {
                                    Text("Sign In")
                                        .font(.headline)
                                        .fontWeight(.semibold)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                            .background(
                                LinearGradient(
                                    colors: [.orange, .red],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .foregroundColor(.white)
                            .cornerRadius(16)
                        }
                        .disabled(authManager.isLoading || email.isEmpty || password.isEmpty)
                        
                        // Biometric Login
                        if biometricManager.isBiometricAvailable {
                            Button(action: biometricLogin) {
                                HStack(spacing: 12) {
                                    Image(systemName: biometricIcon)
                                        .font(.title2)
                                    Text("Sign in with \(biometricText)")
                                        .font(.headline)
                                }
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(Color(.systemGray6))
                                .foregroundColor(.primary)
                                .cornerRadius(16)
                            }
                        }
                    }
                    .padding(.horizontal, 32)
                    
                    // Error Message
                    if let errorMessage = authManager.errorMessage {
                        Text(errorMessage)
                            .font(.subheadline)
                            .foregroundColor(.red)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 32)
                    }
                    
                    Spacer(minLength: 50)
                }
                .frame(minHeight: geometry.size.height)
            }
        }
        .background(
            LinearGradient(
                colors: [Color(.systemBackground), Color(.systemGray6)],
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }
    
    private var biometricIcon: String {
        switch biometricManager.biometricType {
        case .faceID: return "faceid"
        case .touchID: return "touchid"
        default: return "lock.shield"
        }
    }
    
    private var biometricText: String {
        switch biometricManager.biometricType {
        case .faceID: return "Face ID"
        case .touchID: return "Touch ID"
        default: return "Biometrics"
        }
    }
    
    private func login() {
        authManager.login(
            email: email,
            password: password,
            totpCode: totpCode.isEmpty ? nil : totpCode
        )
    }
    
    private func biometricLogin() {
        biometricManager.authenticateWithBiometrics { success, error in
            if success {
                if let credentials = KeychainManager().getStoredCredentials() {
                    authManager.login(email: credentials.email, password: credentials.password)
                }
            }
        }
    }
}

// MARK: - Custom Text Field Style
struct CustomTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding(.horizontal, 16)
            .padding(.vertical, 16)
            .background(Color(.systemGray6))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(.systemGray4), lineWidth: 1)
            )
    }
}

// MARK: - Main Trading View
struct MainTradingView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @EnvironmentObject var tradingManager: TradingManager
    @EnvironmentObject var portfolioManager: PortfolioManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // Home Tab
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Home")
                }
                .tag(0)
            
            // Markets Tab
            MarketsView()
                .tabItem {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                    Text("Markets")
                }
                .tag(1)
            
            // Trading Tab
            TradingView()
                .tabItem {
                    Image(systemName: "arrow.left.arrow.right")
                    Text("Trade")
                }
                .tag(2)
            
            // Portfolio Tab
            PortfolioView()
                .tabItem {
                    Image(systemName: "briefcase.fill")
                    Text("Portfolio")
                }
                .tag(3)
            
            // More Tab
            MoreView()
                .tabItem {
                    Image(systemName: "ellipsis")
                    Text("More")
                }
                .tag(4)
        }
        .accentColor(.orange)
        .onAppear {
            setupWebSocketSubscriptions()
        }
    }
    
    private func setupWebSocketSubscriptions() {
        for market in tradingManager.markets {
            webSocketManager.subscribe(to: "ticker@\(market.symbol.lowercased())")
        }
        
        if let userId = authManager.currentUser?.id {
            webSocketManager.subscribe(to: "user@\(userId)")
        }
    }
}

// MARK: - Home View
struct HomeView: View {
    @EnvironmentObject var portfolioManager: PortfolioManager
    @EnvironmentObject var tradingManager: TradingManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Portfolio Summary
                    PortfolioSummaryCard()
                    
                    // Quick Actions
                    QuickActionsGrid()
                    
                    // Market Overview
                    MarketOverviewCard()
                    
                    // Recent Activity
                    RecentActivityCard()
                }
                .padding(.horizontal, 16)
            }
            .navigationTitle("TigerEx")
            .refreshable {
                portfolioManager.refreshPortfolio()
                tradingManager.loadMarkets()
            }
        }
    }
}

// MARK: - Portfolio Summary Card
struct PortfolioSummaryCard: View {
    @EnvironmentObject var portfolioManager: PortfolioManager
    
    var body: some View {
        VStack(spacing: 16) {
            HStack {
                Text("Portfolio Balance")
                    .font(.headline)
                    .foregroundColor(.secondary)
                Spacer()
                Button(action: { portfolioManager.refreshPortfolio() }) {
                    Image(systemName: "arrow.clockwise")
                        .foregroundColor(.orange)
                }
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("$\(portfolioManager.totalBalance.formatted())")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                HStack {
                    Text("24h Change:")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    Text("\(portfolioManager.portfolioChange24h >= 0 ? "+" : "")\(portfolioManager.portfolioChange24h, specifier: "%.2f")%")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(portfolioManager.portfolioChange24h >= 0 ? .green : .red)
                    
                    Spacer()
                    
                    Text("P&L: $\(portfolioManager.totalPnL.formatted())")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(portfolioManager.totalPnL >= 0 ? .green : .red)
                }
            }
        }
        .padding(20)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

// MARK: - Quick Actions Grid
struct QuickActionsGrid: View {
    let actions = [
        QuickAction(title: "Spot Trading", icon: "arrow.up.arrow.down", color: .blue),
        QuickAction(title: "Futures", icon: "chart.bar", color: .purple),
        QuickAction(title: "Options", icon: "option", color: .green),
        QuickAction(title: "Copy Trading", icon: "doc.on.doc", color: .orange),
        QuickAction(title: "Earn", icon: "percent", color: .yellow),
        QuickAction(title: "NFT", icon: "photo", color: .pink),
        QuickAction(title: "DeFi", icon: "building.columns", color: .indigo),
        QuickAction(title: "Wallet", icon: "creditcard", color: .teal)
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Quick Actions")
                .font(.headline)
                .foregroundColor(.primary)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 16) {
                ForEach(actions, id: \.title) { action in
                    QuickActionButton(action: action)
                }
            }
        }
        .padding(20)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

struct QuickAction {
    let title: String
    let icon: String
    let color: Color
}

struct QuickActionButton: View {
    let action: QuickAction
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: action.icon)
                .font(.title2)
                .foregroundColor(action.color)
                .frame(width: 40, height: 40)
                .background(action.color.opacity(0.1))
                .cornerRadius(12)
            
            Text(action.title)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.primary)
                .multilineTextAlignment(.center)
        }
        .onTapGesture {
            // Handle action tap
        }
    }
}

// MARK: - Market Overview Card
struct MarketOverviewCard: View {
    @EnvironmentObject var tradingManager: TradingManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    
    var topMarkets: [Market] {
        Array(tradingManager.markets.prefix(5))
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Market Overview")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
                NavigationLink("View All", destination: MarketsView())
                    .font(.subheadline)
                    .foregroundColor(.orange)
            }
            
            VStack(spacing: 12) {
                ForEach(topMarkets) { market in
                    MarketRowCompact(market: market)
                }
            }
        }
        .padding(20)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

struct MarketRowCompact: View {
    let market: Market
    @EnvironmentObject var webSocketManager: WebSocketManager
    
    private var tickerData: TickerData? {
        webSocketManager.tickerData[market.symbol]
    }
    
    private var currentPrice: Decimal {
        tickerData?.price ?? market.price
    }
    
    private var priceChange: Double {
        tickerData?.priceChange24h ?? market.priceChange24h
    }
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(market.symbol)
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                
                Text(market.baseAsset)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("$\(currentPrice.formatted())")
                    .font(.headline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Text("\(priceChange >= 0 ? "+" : "")\(priceChange, specifier: "%.2f")%")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(priceChange >= 0 ? .green : .red)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Recent Activity Card
struct RecentActivityCard: View {
    @EnvironmentObject var tradingManager: TradingManager
    
    var recentOrders: [Order] {
        Array(tradingManager.orderHistory.prefix(3))
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Recent Activity")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
                NavigationLink("View All", destination: OrderHistoryView())
                    .font(.subheadline)
                    .foregroundColor(.orange)
            }
            
            if recentOrders.isEmpty {
                Text("No recent activity")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 20)
            } else {
                VStack(spacing: 12) {
                    ForEach(recentOrders) { order in
                        RecentActivityRow(order: order)
                    }
                }
            }
        }
        .padding(20)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

struct RecentActivityRow: View {
    let order: Order
    
    var body: some View {
        HStack {
            Image(systemName: order.side == .buy ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                .foregroundColor(order.side == .buy ? .green : .red)
                .font(.title2)
            
            VStack(alignment: .leading, spacing: 2) {
                Text("\(order.side.rawValue.capitalized) \(order.symbol)")
                    .font(.headline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Text("\(order.quantity.formatted()) @ $\(order.price.formatted())")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                Text("$\(order.totalValue.formatted())")
                    .font(.headline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Text(order.status.rawValue.capitalized)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(statusColor(for: order.status))
            }
        }
        .padding(.vertical, 4)
    }
    
    private func statusColor(for status: OrderStatus) -> Color {
        switch status {
        case .filled: return .green
        case .cancelled: return .red
        case .partiallyFilled: return .yellow
        case .pending: return .blue
        }
    }
}

// MARK: - Data Models
struct User: Codable, Identifiable {
    let id: String
    let email: String
    let username: String
    let firstName: String
    let lastName: String
    let isVerified: Bool
    let twoFactorEnabled: Bool
}

struct Market: Codable, Identifiable {
    let id: String
    let symbol: String
    let baseAsset: String
    let quoteAsset: String
    let price: Decimal
    let priceChange24h: Double
    let volume24h: Decimal
    let high24h: Decimal
    let low24h: Decimal
    let isActive: Bool
}

struct OrderBook: Codable {
    let symbol: String
    let bids: [OrderBookEntry]
    let asks: [OrderBookEntry]
    let lastUpdateId: Int64
}

struct OrderBookEntry: Codable {
    let price: Decimal
    let quantity: Decimal
}

struct Order: Codable, Identifiable {
    let id: String
    let symbol: String
    let side: OrderSide
    let type: OrderType
    let quantity: Decimal
    let price: Decimal
    let filledQuantity: Decimal
    let status: OrderStatus
    let createdAt: Date
    let updatedAt: Date
    
    var totalValue: Decimal {
        quantity * price
    }
}

enum OrderSide: String, Codable, CaseIterable {
    case buy = "BUY"
    case sell = "SELL"
}

enum OrderType: String, Codable, CaseIterable {
    case market = "MARKET"
    case limit = "LIMIT"
    case stopLoss = "STOP_LOSS"
    case stopLimit = "STOP_LIMIT"
    case takeProfit = "TAKE_PROFIT"
    case takeProfitLimit = "TAKE_PROFIT_LIMIT"
}

enum OrderStatus: String, Codable {
    case pending = "PENDING"
    case partiallyFilled = "PARTIALLY_FILLED"
    case filled = "FILLED"
    case cancelled = "CANCELLED"
}

struct AssetBalance: Codable, Identifiable {
    let id = UUID()
    let asset: String
    let free: Decimal
    let locked: Decimal
    let total: Decimal
}

struct Position: Codable, Identifiable {
    let id: String
    let symbol: String
    let side: String
    let size: Decimal
    let entryPrice: Decimal
    let markPrice: Decimal
    let unrealizedPnl: Decimal
    let percentage: Double
}

struct Portfolio: Codable {
    let totalBalance: Decimal
    let availableBalance: Decimal
    let totalPnL: Decimal
    let dailyPnL: Decimal
    let change24h: Double
    let assets: [AssetBalance]
    let positions: [Position]
}

struct RecentTrade: Codable, Identifiable {
    let id: String
    let symbol: String
    let price: Decimal
    let quantity: Decimal
    let side: String
    let timestamp: Date
}

struct ChartDataPoint: Codable, Identifiable {
    let id = UUID()
    let timestamp: Date
    let open: Decimal
    let high: Decimal
    let low: Decimal
    let close: Decimal
    let volume: Decimal
}

struct TickerData: Codable {
    let symbol: String
    let price: Decimal
    let priceChange24h: Double
    let volume24h: Decimal
}

struct OrderBookUpdate: Codable {
    let symbol: String
    let bids: [OrderBookEntry]
    let asks: [OrderBookEntry]
}

struct TradeUpdate: Codable {
    let symbol: String
    let price: Decimal
    let quantity: Decimal
    let side: String
    let timestamp: Date
}

struct LoginRequest: Codable {
    let email: String
    let password: String
    let totpCode: String?
}

struct LoginResponse: Codable {
    let accessToken: String
    let user: User
    let requires2FA: Bool
}

struct OrderRequest: Codable {
    let symbol: String
    let side: OrderSide
    let type: OrderType
    let quantity: Decimal
    let price: Decimal?
    let stopPrice: Decimal?
    let timeInForce: String?
}

struct WebSocketMessage: Codable {
    let method: String
    let params: [String: String]
}

struct WebSocketResponse: Codable {
    let type: String
    let data: Data
}

// MARK: - API Service
class APIService {
    static let shared = APIService()
    private let baseURL = "https://api.tigerex.com"
    private let session = URLSession.shared
    
    private init() {}
    
    func login(request: LoginRequest, completion: @escaping (Result<LoginResponse, Error>) -> Void) {
        // Implementation for login API call
        // This is a mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            let user = User(
                id: "1",
                email: request.email,
                username: "user1",
                firstName: "John",
                lastName: "Doe",
                isVerified: true,
                twoFactorEnabled: false
            )
            
            let response = LoginResponse(
                accessToken: "mock_token",
                user: user,
                requires2FA: request.totpCode == nil && request.email.contains("2fa")
            )
            
            completion(.success(response))
        }
    }
    
    func validateToken(_ token: String, completion: @escaping (Result<User, Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let user = User(
                id: "1",
                email: "user@example.com",
                username: "user1",
                firstName: "John",
                lastName: "Doe",
                isVerified: true,
                twoFactorEnabled: false
            )
            completion(.success(user))
        }
    }
    
    func getMarkets(completion: @escaping (Result<[Market], Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let markets = [
                Market(id: "1", symbol: "BTCUSDT", baseAsset: "BTC", quoteAsset: "USDT", price: 45000, priceChange24h: 2.5, volume24h: 1000000, high24h: 46000, low24h: 44000, isActive: true),
                Market(id: "2", symbol: "ETHUSDT", baseAsset: "ETH", quoteAsset: "USDT", price: 3000, priceChange24h: -1.2, volume24h: 500000, high24h: 3100, low24h: 2950, isActive: true),
                Market(id: "3", symbol: "BNBUSDT", baseAsset: "BNB", quoteAsset: "USDT", price: 300, priceChange24h: 0.8, volume24h: 200000, high24h: 305, low24h: 295, isActive: true)
            ]
            completion(.success(markets))
        }
    }
    
    func getPortfolio(completion: @escaping (Result<Portfolio, Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let assets = [
                AssetBalance(asset: "BTC", free: 1.5, locked: 0.5, total: 2.0),
                AssetBalance(asset: "ETH", free: 10.0, locked: 2.0, total: 12.0),
                AssetBalance(asset: "USDT", free: 5000.0, locked: 1000.0, total: 6000.0)
            ]
            
            let positions = [
                Position(id: "1", symbol: "BTCUSDT", side: "LONG", size: 0.1, entryPrice: 44000, markPrice: 45000, unrealizedPnl: 100, percentage: 2.27)
            ]
            
            let portfolio = Portfolio(
                totalBalance: 156000,
                availableBalance: 145000,
                totalPnL: 2500,
                dailyPnL: 150,
                change24h: 1.8,
                assets: assets,
                positions: positions
            )
            
            completion(.success(portfolio))
        }
    }
    
    func getOrderBook(symbol: String, completion: @escaping (Result<OrderBook, Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            let bids = [
                OrderBookEntry(price: 44950, quantity: 0.5),
                OrderBookEntry(price: 44940, quantity: 1.2),
                OrderBookEntry(price: 44930, quantity: 0.8)
            ]
            
            let asks = [
                OrderBookEntry(price: 45050, quantity: 0.7),
                OrderBookEntry(price: 45060, quantity: 1.1),
                OrderBookEntry(price: 45070, quantity: 0.9)
            ]
            
            let orderBook = OrderBook(symbol: symbol, bids: bids, asks: asks, lastUpdateId: 12345)
            completion(.success(orderBook))
        }
    }
    
    func getRecentTrades(symbol: String, completion: @escaping (Result<[RecentTrade], Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            let trades = [
                RecentTrade(id: "1", symbol: symbol, price: 45000, quantity: 0.1, side: "BUY", timestamp: Date()),
                RecentTrade(id: "2", symbol: symbol, price: 44995, quantity: 0.2, side: "SELL", timestamp: Date().addingTimeInterval(-60)),
                RecentTrade(id: "3", symbol: symbol, price: 45005, quantity: 0.15, side: "BUY", timestamp: Date().addingTimeInterval(-120))
            ]
            completion(.success(trades))
        }
    }
    
    func getChartData(symbol: String, timeframe: String, completion: @escaping (Result<[ChartDataPoint], Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            var chartData: [ChartDataPoint] = []
            let basePrice: Decimal = 45000
            
            for i in 0..<100 {
                let timestamp = Date().addingTimeInterval(TimeInterval(-i * 3600))
                let randomChange = Decimal(Double.random(in: -500...500))
                let open = basePrice + randomChange
                let close = open + Decimal(Double.random(in: -200...200))
                let high = max(open, close) + Decimal(Double.random(in: 0...100))
                let low = min(open, close) - Decimal(Double.random(in: 0...100))
                let volume = Decimal(Double.random(in: 100...1000))
                
                chartData.append(ChartDataPoint(
                    timestamp: timestamp,
                    open: open,
                    high: high,
                    low: low,
                    close: close,
                    volume: volume
                ))
            }
            
            completion(.success(chartData.reversed()))
        }
    }
    
    func getOpenOrders(completion: @escaping (Result<[Order], Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            let orders = [
                Order(id: "1", symbol: "BTCUSDT", side: .buy, type: .limit, quantity: 0.1, price: 44000, filledQuantity: 0, status: .pending, createdAt: Date(), updatedAt: Date())
            ]
            completion(.success(orders))
        }
    }
    
    func getOrderHistory(completion: @escaping (Result<[Order], Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            let orders = [
                Order(id: "2", symbol: "ETHUSDT", side: .sell, type: .market, quantity: 1.0, price: 3000, filledQuantity: 1.0, status: .filled, createdAt: Date().addingTimeInterval(-3600), updatedAt: Date().addingTimeInterval(-3600)),
                Order(id: "3", symbol: "BNBUSDT", side: .buy, type: .limit, quantity: 10.0, price: 295, filledQuantity: 10.0, status: .filled, createdAt: Date().addingTimeInterval(-7200), updatedAt: Date().addingTimeInterval(-7200))
            ]
            completion(.success(orders))
        }
    }
    
    func placeOrder(request: OrderRequest, completion: @escaping (Result<Order, Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let order = Order(
                id: UUID().uuidString,
                symbol: request.symbol,
                side: request.side,
                type: request.type,
                quantity: request.quantity,
                price: request.price ?? 0,
                filledQuantity: 0,
                status: .pending,
                createdAt: Date(),
                updatedAt: Date()
            )
            completion(.success(order))
        }
    }
    
    func cancelOrder(orderId: String, completion: @escaping (Result<Void, Error>) -> Void) {
        // Mock implementation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            completion(.success(()))
        }
    }
}

// MARK: - Keychain Manager
class KeychainManager {
    private let service = "com.tigerex.app"
    
    func saveAccessToken(_ token: String) {
        save(key: "access_token", value: token)
    }
    
    func getAccessToken() -> String? {
        return get(key: "access_token")
    }
    
    func deleteAccessToken() {
        delete(key: "access_token")
    }
    
    func saveCredentials(email: String, password: String) {
        let credentials = "\(email):\(password)"
        save(key: "credentials", value: credentials)
    }
    
    func getStoredCredentials() -> (email: String, password: String)? {
        guard let credentials = get(key: "credentials"),
              let colonIndex = credentials.firstIndex(of: ":") else {
            return nil
        }
        
        let email = String(credentials[..<colonIndex])
        let password = String(credentials[credentials.index(after: colonIndex)...])
        
        return (email: email, password: password)
    }
    
    func deleteCredentials() {
        delete(key: "credentials")
    }
    
    private func save(key: String, value: String) {
        let data = value.data(using: .utf8)!
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    private func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let string = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return string
    }
    
    private func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - Additional Views (Placeholder implementations)
struct MarketsView: View {
    var body: some View {
        Text("Markets View - Coming Soon")
            .navigationTitle("Markets")
    }
}

struct TradingView: View {
    var body: some View {
        Text("Trading View - Coming Soon")
            .navigationTitle("Trade")
    }
}

struct PortfolioView: View {
    var body: some View {
        Text("Portfolio View - Coming Soon")
            .navigationTitle("Portfolio")
    }
}

struct MoreView: View {
    var body: some View {
        Text("More View - Coming Soon")
            .navigationTitle("More")
    }
}

struct OrderHistoryView: View {
    var body: some View {
        Text("Order History - Coming Soon")
            .navigationTitle("Order History")
    }
}
