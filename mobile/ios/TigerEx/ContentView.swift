import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var authManager = AuthenticationManager()
    
    var body: some View {
        Group {
            if authManager.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .environmentObject(authManager)
    }
}

struct LoginView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var showingRegister = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                Spacer()
                
                // Logo and Title
                VStack(spacing: 16) {
                    Text("TigerEx")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundColor(.orange)
                    
                    Text("Advanced Crypto Trading")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Login Form
                VStack(spacing: 16) {
                    TextField("Email", text: $email)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    
                    SecureField("Password", text: $password)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button(action: login) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .black))
                                    .scaleEffect(0.8)
                            } else {
                                Text("Login")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color.orange)
                        .foregroundColor(.black)
                        .cornerRadius(10)
                    }
                    .disabled(isLoading)
                    
                    Button("Don't have an account? Register") {
                        showingRegister = true
                    }
                    .foregroundColor(.blue)
                }
                
                // OAuth Buttons
                VStack(spacing: 12) {
                    Divider()
                        .padding(.vertical)
                    
                    Button(action: { authManager.signInWithGoogle() }) {
                        HStack {
                            Image(systemName: "globe")
                            Text("Continue with Google")
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color(.systemGray6))
                        .cornerRadius(10)
                    }
                    
                    Button(action: { authManager.signInWithApple() }) {
                        HStack {
                            Image(systemName: "applelogo")
                            Text("Continue with Apple")
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color.black)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    
                    Button(action: { authManager.signInWithTelegram() }) {
                        HStack {
                            Image(systemName: "paperplane.fill")
                            Text("Continue with Telegram")
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                }
                
                Spacer()
            }
            .padding(24)
            .navigationTitle("")
            .navigationBarHidden(true)
        }
        .sheet(isPresented: $showingRegister) {
            RegisterView()
        }
    }
    
    private func login() {
        isLoading = true
        authManager.signIn(email: email, password: password) { success in
            isLoading = false
            if !success {
                // Handle login error
            }
        }
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Home")
                }
            
            TradingView()
                .tabItem {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                    Text("Trade")
                }
            
            FuturesView()
                .tabItem {
                    Image(systemName: "arrow.up.arrow.down")
                    Text("Futures")
                }
            
            P2PView()
                .tabItem {
                    Image(systemName: "person.2.fill")
                    Text("P2P")
                }
            
            WalletView()
                .tabItem {
                    Image(systemName: "creditcard.fill")
                    Text("Wallet")
                }
        }
        .accentColor(.orange)
    }
}

struct HomeView: View {
    @StateObject private var viewModel = HomeViewModel()
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Portfolio Summary
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Portfolio Value")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        Text("$12,345.67")
                            .font(.system(size: 32, weight: .bold))
                        
                        HStack {
                            Text("+$234.56")
                                .foregroundColor(.green)
                            Text("(+1.95%)")
                                .foregroundColor(.green)
                        }
                        .font(.subheadline)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    // Quick Actions
                    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 12) {
                        QuickActionButton(title: "Trade", color: .orange, icon: "chart.line.uptrend.xyaxis")
                        QuickActionButton(title: "Futures", color: .purple, icon: "arrow.up.arrow.down")
                        QuickActionButton(title: "P2P", color: .blue, icon: "person.2.fill")
                        QuickActionButton(title: "Wallet", color: .green, icon: "creditcard.fill")
                    }
                    
                    // Market Data
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Markets")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        LazyVStack(spacing: 8) {
                            ForEach(viewModel.marketData, id: \.symbol) { market in
                                MarketRow(market: market)
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("TigerEx")
            .refreshable {
                viewModel.refreshData()
            }
        }
    }
}

struct QuickActionButton: View {
    let title: String
    let color: Color
    let icon: String
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
        }
        .frame(height: 60)
        .frame(maxWidth: .infinity)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct MarketRow: View {
    let market: MarketData
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(market.symbol)
                    .fontWeight(.semibold)
                
                Text("Vol: \(market.volume)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("$\(market.price)")
                    .fontWeight(.semibold)
                
                Text(market.change)
                    .font(.caption)
                    .foregroundColor(market.isPositive ? .green : .red)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

struct TradingView: View {
    @StateObject private var viewModel = TradingViewModel()
    
    var body: some View {
        NavigationView {
            VStack {
                // Trading Pair Header
                VStack(alignment: .leading, spacing: 8) {
                    Text(viewModel.selectedPair)
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("$43,250.00")
                        .font(.title2)
                        .foregroundColor(.green)
                    
                    Text("+2.45% (+$1,035.50)")
                        .font(.subheadline)
                        .foregroundColor(.green)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(Color(.systemGray6))
                
                HStack(spacing: 0) {
                    // Order Book
                    VStack(alignment: .leading) {
                        Text("Order Book")
                            .font(.headline)
                            .padding(.horizontal)
                        
                        ScrollView {
                            LazyVStack(spacing: 2) {
                                ForEach(viewModel.orderBook.sells.prefix(10), id: \.price) { order in
                                    OrderBookRow(order: order, isBuy: false)
                                }
                                
                                ForEach(viewModel.orderBook.buys.prefix(10), id: \.price) { order in
                                    OrderBookRow(order: order, isBuy: true)
                                }
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)
                    
                    Divider()
                    
                    // Order Form
                    OrderFormView()
                        .frame(maxWidth: .infinity)
                }
                .frame(maxHeight: .infinity)
            }
            .navigationTitle("Spot Trading")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct OrderBookRow: View {
    let order: OrderBookEntry
    let isBuy: Bool
    
    var body: some View {
        HStack {
            Text(order.price)
                .font(.caption)
                .foregroundColor(isBuy ? .green : .red)
            
            Spacer()
            
            Text(order.amount)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal)
        .padding(.vertical, 2)
    }
}

struct OrderFormView: View {
    @State private var orderType = "Buy"
    @State private var amount = ""
    @State private var price = ""
    
    var body: some View {
        VStack(spacing: 16) {
            Text("Place Order")
                .font(.headline)
            
            // Buy/Sell Picker
            Picker("Order Type", selection: $orderType) {
                Text("Buy").tag("Buy")
                Text("Sell").tag("Sell")
            }
            .pickerStyle(SegmentedPickerStyle())
            
            VStack(spacing: 12) {
                TextField("Price (USDT)", text: $price)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.decimalPad)
                
                TextField("Amount (BTC)", text: $amount)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.decimalPad)
            }
            
            Button(action: placeOrder) {
                Text("\(orderType) BTC")
                    .fontWeight(.semibold)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(orderType == "Buy" ? Color.green : Color.red)
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
            
            Spacer()
        }
        .padding()
    }
    
    private func placeOrder() {
        // Implement order placement
    }
}

// Additional Views
struct RegisterView: View { /* Implementation */ }
struct FuturesView: View { /* Implementation */ }
struct P2PView: View { /* Implementation */ }
struct WalletView: View { /* Implementation */ }

// ViewModels and Data Models would be implemented similarly to Android
class AuthenticationManager: ObservableObject {
    @Published var isAuthenticated = false
    
    func signIn(email: String, password: String, completion: @escaping (Bool) -> Void) {
        // Implement sign in logic
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.isAuthenticated = true
            completion(true)
        }
    }
    
    func signInWithGoogle() { /* Implementation */ }
    func signInWithApple() { /* Implementation */ }
    func signInWithTelegram() { /* Implementation */ }
}

class HomeViewModel: ObservableObject {
    @Published var marketData: [MarketData] = []
    @Published var portfolioValue: Double = 0
    
    init() {
        loadMarketData()
    }
    
    func loadMarketData() {
        // Mock data
        marketData = [
            MarketData(symbol: "BTC/USDT", price: "43,250.00", change: "+2.45%", volume: "2.1B", isPositive: true),
            MarketData(symbol: "ETH/USDT", price: "2,650.00", change: "+1.85%", volume: "1.8B", isPositive: true),
            MarketData(symbol: "BNB/USDT", price: "315.50", change: "-0.75%", volume: "450M", isPositive: false),
            MarketData(symbol: "ADA/USDT", price: "0.4850", change: "+3.20%", volume: "320M", isPositive: true)
        ]
        portfolioValue = 12345.67
    }
    
    func refreshData() {
        loadMarketData()
    }
}

class TradingViewModel: ObservableObject {
    @Published var selectedPair = "BTC/USDT"
    @Published var orderBook = OrderBook(
        buys: [
            OrderBookEntry(price: "43,248.50", amount: "0.1234"),
            OrderBookEntry(price: "43,247.25", amount: "0.2567")
        ],
        sells: [
            OrderBookEntry(price: "43,251.25", amount: "0.1567"),
            OrderBookEntry(price: "43,252.50", amount: "0.2234")
        ]
    )
}

struct MarketData {
    let symbol: String
    let price: String
    let change: String
    let volume: String
    let isPositive: Bool
}

struct OrderBookEntry {
    let price: String
    let amount: String
}

struct OrderBook {
    let buys: [OrderBookEntry]
    let sells: [OrderBookEntry]
}

#Preview {
    ContentView()
}
