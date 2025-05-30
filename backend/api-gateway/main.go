package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/sessions"
	"github.com/gin-contrib/sessions/redis"
	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/websocket"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"
	"golang.org/x/time/rate"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Configuration
type Config struct {
	Port           string
	DatabaseURL    string
	RedisURL       string
	JWTSecret      string
	Environment    string
	RateLimitRPS   int
	RateLimitBurst int
}

// Models
type User struct {
	ID                uint      `json:"id" gorm:"primaryKey"`
	Email             string    `json:"email" gorm:"unique;not null"`
	Username          string    `json:"username" gorm:"unique;not null"`
	PasswordHash      string    `json:"-" gorm:"not null"`
	FirstName         string    `json:"first_name"`
	LastName          string    `json:"last_name"`
	Phone             string    `json:"phone"`
	Country           string    `json:"country"`
	IsVerified        bool      `json:"is_verified" gorm:"default:false"`
	IsActive          bool      `json:"is_active" gorm:"default:true"`
	TwoFactorEnabled  bool      `json:"two_factor_enabled" gorm:"default:false"`
	TwoFactorSecret   string    `json:"-"`
	APIKeyEnabled     bool      `json:"api_key_enabled" gorm:"default:false"`
	TradingEnabled    bool      `json:"trading_enabled" gorm:"default:true"`
	WithdrawalEnabled bool      `json:"withdrawal_enabled" gorm:"default:true"`
	VIPLevel          int       `json:"vip_level" gorm:"default:0"`
	ReferralCode      string    `json:"referral_code" gorm:"unique"`
	ReferredBy        uint      `json:"referred_by"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

type APIKey struct {
	ID          uint      `json:"id" gorm:"primaryKey"`
	UserID      uint      `json:"user_id" gorm:"not null"`
	Name        string    `json:"name" gorm:"not null"`
	Key         string    `json:"key" gorm:"unique;not null"`
	Secret      string    `json:"-" gorm:"not null"`
	Permissions string    `json:"permissions"` // JSON array of permissions
	IsActive    bool      `json:"is_active" gorm:"default:true"`
	LastUsedAt  *time.Time `json:"last_used_at"`
	ExpiresAt   *time.Time `json:"expires_at"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type TradingPair struct {
	ID                uint    `json:"id" gorm:"primaryKey"`
	Symbol            string  `json:"symbol" gorm:"unique;not null"`
	BaseAsset         string  `json:"base_asset" gorm:"not null"`
	QuoteAsset        string  `json:"quote_asset" gorm:"not null"`
	Status            string  `json:"status" gorm:"default:'TRADING'"` // TRADING, HALT, BREAK
	MinQuantity       float64 `json:"min_quantity"`
	MaxQuantity       float64 `json:"max_quantity"`
	StepSize          float64 `json:"step_size"`
	MinPrice          float64 `json:"min_price"`
	MaxPrice          float64 `json:"max_price"`
	TickSize          float64 `json:"tick_size"`
	MinNotional       float64 `json:"min_notional"`
	MakerFee          float64 `json:"maker_fee" gorm:"default:0.001"`
	TakerFee          float64 `json:"taker_fee" gorm:"default:0.001"`
	IsMarginEnabled   bool    `json:"is_margin_enabled" gorm:"default:false"`
	IsFuturesEnabled  bool    `json:"is_futures_enabled" gorm:"default:false"`
	IsOptionsEnabled  bool    `json:"is_options_enabled" gorm:"default:false"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

type Order struct {
	ID               uint      `json:"id" gorm:"primaryKey"`
	UserID           uint      `json:"user_id" gorm:"not null"`
	Symbol           string    `json:"symbol" gorm:"not null"`
	ClientOrderID    string    `json:"client_order_id"`
	Side             string    `json:"side" gorm:"not null"` // BUY, SELL
	Type             string    `json:"type" gorm:"not null"` // MARKET, LIMIT, STOP_LOSS, etc.
	TimeInForce      string    `json:"time_in_force" gorm:"default:'GTC'"`
	Quantity         float64   `json:"quantity" gorm:"not null"`
	Price            float64   `json:"price"`
	StopPrice        float64   `json:"stop_price"`
	IcebergQuantity  float64   `json:"iceberg_quantity"`
	FilledQuantity   float64   `json:"filled_quantity" gorm:"default:0"`
	Status           string    `json:"status" gorm:"default:'NEW'"`
	Fee              float64   `json:"fee" gorm:"default:0"`
	FeeAsset         string    `json:"fee_asset"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

// JWT Claims
type Claims struct {
	UserID      uint   `json:"user_id"`
	Email       string `json:"email"`
	Permissions []string `json:"permissions"`
	jwt.RegisteredClaims
}

// Rate Limiter
type RateLimiter struct {
	visitors map[string]*rate.Limiter
	mu       sync.RWMutex
	rate     rate.Limit
	burst    int
}

func NewRateLimiter(rps int, burst int) *RateLimiter {
	return &RateLimiter{
		visitors: make(map[string]*rate.Limiter),
		rate:     rate.Limit(rps),
		burst:    burst,
	}
}

func (rl *RateLimiter) GetLimiter(ip string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.visitors[ip]
	if !exists {
		limiter = rate.NewLimiter(rl.rate, rl.burst)
		rl.visitors[ip] = limiter
	}

	return limiter
}

// WebSocket Hub
type Hub struct {
	clients    map[*Client]bool
	broadcast  chan []byte
	register   chan *Client
	unregister chan *Client
}

type Client struct {
	hub  *Hub
	conn *websocket.Conn
	send chan []byte
	userID uint
	subscriptions map[string]bool
}

type Message struct {
	Type    string      `json:"type"`
	Channel string      `json:"channel"`
	Data    interface{} `json:"data"`
}

// API Gateway
type APIGateway struct {
	config      *Config
	db          *gorm.DB
	redis       *redis.Client
	logger      *zap.Logger
	rateLimiter *RateLimiter
	hub         *Hub
	upgrader    websocket.Upgrader
}

func NewAPIGateway(config *Config) (*APIGateway, error) {
	// Initialize logger
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, err
	}

	// Initialize database
	db, err := gorm.Open(postgres.Open(config.DatabaseURL), &gorm.Config{})
	if err != nil {
		return nil, err
	}

	// Auto-migrate models
	err = db.AutoMigrate(&User{}, &APIKey{}, &TradingPair{}, &Order{})
	if err != nil {
		return nil, err
	}

	// Initialize Redis
	opt, err := redis.ParseURL(config.RedisURL)
	if err != nil {
		return nil, err
	}
	redisClient := redis.NewClient(opt)

	// Initialize rate limiter
	rateLimiter := NewRateLimiter(config.RateLimitRPS, config.RateLimitBurst)

	// Initialize WebSocket hub
	hub := &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan []byte),
		register:   make(chan *Client),
		unregister: make(chan *Client),
	}

	upgrader := websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true // Allow all origins in development
		},
	}

	return &APIGateway{
		config:      config,
		db:          db,
		redis:       redisClient,
		logger:      logger,
		rateLimiter: rateLimiter,
		hub:         hub,
		upgrader:    upgrader,
	}, nil
}

// Middleware
func (api *APIGateway) RateLimitMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		ip := c.ClientIP()
		limiter := api.rateLimiter.GetLimiter(ip)

		if !limiter.Allow() {
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error": "Rate limit exceeded",
				"retry_after": "60s",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

func (api *APIGateway) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			c.Abort()
			return
		}

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		if tokenString == authHeader {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Bearer token required"})
			c.Abort()
			return
		}

		claims := &Claims{}
		token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
			return []byte(api.config.JWTSecret), nil
		})

		if err != nil || !token.Valid {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
			c.Abort()
			return
		}

		c.Set("user_id", claims.UserID)
		c.Set("email", claims.Email)
		c.Set("permissions", claims.Permissions)
		c.Next()
	}
}

func (api *APIGateway) APIKeyMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		apiKey := c.GetHeader("X-API-Key")
		signature := c.GetHeader("X-API-Signature")
		timestamp := c.GetHeader("X-API-Timestamp")

		if apiKey == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "API key required"})
			c.Abort()
			return
		}

		// Validate API key and signature
		var key APIKey
		if err := api.db.Where("key = ? AND is_active = ?", apiKey, true).First(&key).Error; err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid API key"})
			c.Abort()
			return
		}

		// Check expiration
		if key.ExpiresAt != nil && key.ExpiresAt.Before(time.Now()) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "API key expired"})
			c.Abort()
			return
		}

		// Validate signature (simplified - implement proper HMAC validation)
		if signature == "" || timestamp == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Signature and timestamp required"})
			c.Abort()
			return
		}

		// Update last used timestamp
		now := time.Now()
		key.LastUsedAt = &now
		api.db.Save(&key)

		c.Set("user_id", key.UserID)
		c.Set("api_key_id", key.ID)
		c.Next()
	}
}

// Routes
func (api *APIGateway) SetupRoutes() *gin.Engine {
	if api.config.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()
	r.Use(gin.Logger())
	r.Use(gin.Recovery())

	// CORS configuration
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowHeaders = []string{"Origin", "Content-Length", "Content-Type", "Authorization", "X-API-Key", "X-API-Signature", "X-API-Timestamp"}
	r.Use(cors.New(config))

	// Session middleware
	store, _ := redis.NewStore(10, "tcp", "localhost:6379", "", []byte("secret"))
	r.Use(sessions.Sessions("tigerex_session", store))

	// Rate limiting
	r.Use(api.RateLimitMiddleware())

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "healthy",
			"timestamp": time.Now().Unix(),
		})
	})

	// Public routes
	public := r.Group("/api/v1")
	{
		public.POST("/auth/register", api.Register)
		public.POST("/auth/login", api.Login)
		public.POST("/auth/refresh", api.RefreshToken)
		public.GET("/market/ticker/:symbol", api.GetTicker)
		public.GET("/market/depth/:symbol", api.GetOrderBook)
		public.GET("/market/trades/:symbol", api.GetRecentTrades)
		public.GET("/market/klines/:symbol", api.GetKlines)
		public.GET("/market/24hr", api.Get24hrStats)
		public.GET("/exchange/info", api.GetExchangeInfo)
		public.GET("/exchange/time", api.GetServerTime)
	}

	// Protected routes (JWT)
	protected := r.Group("/api/v1")
	protected.Use(api.AuthMiddleware())
	{
		// Account endpoints
		protected.GET("/account/info", api.GetAccountInfo)
		protected.GET("/account/balance", api.GetBalance)
		protected.GET("/account/orders", api.GetOrders)
		protected.GET("/account/trades", api.GetTrades)
		protected.POST("/account/withdraw", api.Withdraw)
		protected.GET("/account/deposit/address", api.GetDepositAddress)
		protected.GET("/account/deposit/history", api.GetDepositHistory)
		protected.GET("/account/withdraw/history", api.GetWithdrawHistory)

		// Trading endpoints
		protected.POST("/order", api.PlaceOrder)
		protected.DELETE("/order", api.CancelOrder)
		protected.DELETE("/orders", api.CancelAllOrders)
		protected.GET("/order", api.GetOrder)
		protected.GET("/orders/open", api.GetOpenOrders)

		// Margin trading
		protected.POST("/margin/borrow", api.MarginBorrow)
		protected.POST("/margin/repay", api.MarginRepay)
		protected.GET("/margin/account", api.GetMarginAccount)

		// Futures trading
		protected.POST("/futures/order", api.PlaceFuturesOrder)
		protected.GET("/futures/account", api.GetFuturesAccount)
		protected.POST("/futures/leverage", api.ChangeLeverage)

		// Staking
		protected.POST("/staking/stake", api.Stake)
		protected.POST("/staking/unstake", api.Unstake)
		protected.GET("/staking/rewards", api.GetStakingRewards)

		// Copy trading
		protected.POST("/copy/follow", api.FollowTrader)
		protected.POST("/copy/unfollow", api.UnfollowTrader)
		protected.GET("/copy/leaders", api.GetCopyTradingLeaders)

		// API key management
		protected.POST("/api-keys", api.CreateAPIKey)
		protected.GET("/api-keys", api.GetAPIKeys)
		protected.DELETE("/api-keys/:id", api.DeleteAPIKey)
	}

	// API key protected routes
	apiRoutes := r.Group("/api/v1")
	apiRoutes.Use(api.APIKeyMiddleware())
	{
		apiRoutes.POST("/order/api", api.PlaceOrderAPI)
		apiRoutes.DELETE("/order/api", api.CancelOrderAPI)
		apiRoutes.GET("/account/api", api.GetAccountInfoAPI)
	}

	// WebSocket endpoint
	r.GET("/ws", api.HandleWebSocket)

	// Admin routes (separate authentication)
	admin := r.Group("/admin/api/v1")
	admin.Use(api.AdminAuthMiddleware())
	{
		admin.GET("/users", api.GetUsers)
		admin.POST("/users/:id/verify", api.VerifyUser)
		admin.POST("/users/:id/suspend", api.SuspendUser)
		admin.GET("/trading-pairs", api.GetTradingPairs)
		admin.POST("/trading-pairs", api.CreateTradingPair)
		admin.PUT("/trading-pairs/:id", api.UpdateTradingPair)
		admin.DELETE("/trading-pairs/:id", api.DeleteTradingPair)
		admin.GET("/system/stats", api.GetSystemStats)
		admin.GET("/orders/all", api.GetAllOrders)
		admin.POST("/maintenance", api.SetMaintenanceMode)
	}

	return r
}

// Authentication handlers
func (api *APIGateway) Register(c *gin.Context) {
	var req struct {
		Email     string `json:"email" binding:"required,email"`
		Username  string `json:"username" binding:"required,min=3,max=20"`
		Password  string `json:"password" binding:"required,min=8"`
		FirstName string `json:"first_name" binding:"required"`
		LastName  string `json:"last_name" binding:"required"`
		Country   string `json:"country" binding:"required"`
		ReferralCode string `json:"referral_code"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Check if user already exists
	var existingUser User
	if err := api.db.Where("email = ? OR username = ?", req.Email, req.Username).First(&existingUser).Error; err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "User already exists"})
		return
	}

	// Hash password (implement proper password hashing)
	passwordHash := hashPassword(req.Password)

	// Generate referral code
	referralCode := generateReferralCode()

	user := User{
		Email:        req.Email,
		Username:     req.Username,
		PasswordHash: passwordHash,
		FirstName:    req.FirstName,
		LastName:     req.LastName,
		Country:      req.Country,
		ReferralCode: referralCode,
	}

	// Handle referral
	if req.ReferralCode != "" {
		var referrer User
		if err := api.db.Where("referral_code = ?", req.ReferralCode).First(&referrer).Error; err == nil {
			user.ReferredBy = referrer.ID
		}
	}

	if err := api.db.Create(&user).Error; err != nil {
		api.logger.Error("Failed to create user", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	// Generate JWT token
	token, err := api.generateJWT(user.ID, user.Email, []string{"trading", "withdrawal"})
	if err != nil {
		api.logger.Error("Failed to generate token", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "User created successfully",
		"token":   token,
		"user": gin.H{
			"id":       user.ID,
			"email":    user.Email,
			"username": user.Username,
		},
	})
}

func (api *APIGateway) Login(c *gin.Context) {
	var req struct {
		Email    string `json:"email" binding:"required"`
		Password string `json:"password" binding:"required"`
		TwoFactorCode string `json:"two_factor_code"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var user User
	if err := api.db.Where("email = ?", req.Email).First(&user).Error; err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Verify password
	if !verifyPassword(req.Password, user.PasswordHash) {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Check if account is active
	if !user.IsActive {
		c.JSON(http.StatusForbidden, gin.H{"error": "Account is suspended"})
		return
	}

	// Verify 2FA if enabled
	if user.TwoFactorEnabled {
		if req.TwoFactorCode == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Two-factor authentication code required"})
			return
		}
		// Implement TOTP verification
		if !verifyTOTP(user.TwoFactorSecret, req.TwoFactorCode) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid two-factor authentication code"})
			return
		}
	}

	// Generate JWT token
	permissions := []string{"trading"}
	if user.WithdrawalEnabled {
		permissions = append(permissions, "withdrawal")
	}

	token, err := api.generateJWT(user.ID, user.Email, permissions)
	if err != nil {
		api.logger.Error("Failed to generate token", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Login successful",
		"token":   token,
		"user": gin.H{
			"id":              user.ID,
			"email":           user.Email,
			"username":        user.Username,
			"is_verified":     user.IsVerified,
			"trading_enabled": user.TradingEnabled,
			"vip_level":       user.VIPLevel,
		},
	})
}

// Trading handlers
func (api *APIGateway) PlaceOrder(c *gin.Context) {
	userID := c.GetUint("user_id")
	
	var req struct {
		Symbol          string  `json:"symbol" binding:"required"`
		Side            string  `json:"side" binding:"required,oneof=BUY SELL"`
		Type            string  `json:"type" binding:"required,oneof=MARKET LIMIT STOP_LOSS STOP_LIMIT TAKE_PROFIT TAKE_PROFIT_LIMIT"`
		TimeInForce     string  `json:"time_in_force" binding:"oneof=GTC IOC FOK"`
		Quantity        float64 `json:"quantity" binding:"required,gt=0"`
		Price           float64 `json:"price"`
		StopPrice       float64 `json:"stop_price"`
		IcebergQuantity float64 `json:"iceberg_quantity"`
		ClientOrderID   string  `json:"client_order_id"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate trading pair
	var tradingPair TradingPair
	if err := api.db.Where("symbol = ? AND status = ?", req.Symbol, "TRADING").First(&tradingPair).Error; err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid trading pair or trading halted"})
		return
	}

	// Validate order parameters
	if req.Quantity < tradingPair.MinQuantity || req.Quantity > tradingPair.MaxQuantity {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid quantity"})
		return
	}

	if req.Type != "MARKET" && (req.Price < tradingPair.MinPrice || req.Price > tradingPair.MaxPrice) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid price"})
		return
	}

	// Create order
	order := Order{
		UserID:          userID,
		Symbol:          req.Symbol,
		ClientOrderID:   req.ClientOrderID,
		Side:            req.Side,
		Type:            req.Type,
		TimeInForce:     req.TimeInForce,
		Quantity:        req.Quantity,
		Price:           req.Price,
		StopPrice:       req.StopPrice,
		IcebergQuantity: req.IcebergQuantity,
		Status:          "NEW",
	}

	if err := api.db.Create(&order).Error; err != nil {
		api.logger.Error("Failed to create order", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create order"})
		return
	}

	// Send order to matching engine (implement message queue)
	api.sendOrderToMatchingEngine(order)

	c.JSON(http.StatusCreated, gin.H{
		"message": "Order placed successfully",
		"order":   order,
	})
}

// WebSocket handler
func (api *APIGateway) HandleWebSocket(c *gin.Context) {
	conn, err := api.upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		api.logger.Error("WebSocket upgrade failed", zap.Error(err))
		return
	}

	client := &Client{
		hub:           api.hub,
		conn:          conn,
		send:          make(chan []byte, 256),
		subscriptions: make(map[string]bool),
	}

	client.hub.register <- client

	go client.writePump()
	go client.readPump()
}

// WebSocket client methods
func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	c.conn.SetReadLimit(512)
	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			break
		}

		var msg Message
		if err := json.Unmarshal(message, &msg); err != nil {
			continue
		}

		// Handle subscription/unsubscription
		switch msg.Type {
		case "subscribe":
			c.subscriptions[msg.Channel] = true
		case "unsubscribe":
			delete(c.subscriptions, msg.Channel)
		}
	}
}

func (c *Client) writePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			n := len(c.send)
			for i := 0; i < n; i++ {
				w.Write([]byte{'\n'})
				w.Write(<-c.send)
			}

			if err := w.Close(); err != nil {
				return
			}
		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// Hub methods
func (h *Hub) run() {
	for {
		select {
		case client := <-h.register:
			h.clients[client] = true
		case client := <-h.unregister:
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
			}
		case message := <-h.broadcast:
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					close(client.send)
					delete(h.clients, client)
				}
			}
		}
	}
}

// Utility functions
func (api *APIGateway) generateJWT(userID uint, email string, permissions []string) (string, error) {
	claims := Claims{
		UserID:      userID,
		Email:       email,
		Permissions: permissions,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(api.config.JWTSecret))
}

func (api *APIGateway) sendOrderToMatchingEngine(order Order) {
	// Implement message queue integration (Kafka, RabbitMQ, etc.)
	api.logger.Info("Sending order to matching engine", zap.Uint("order_id", order.ID))
}

// Placeholder implementations
func hashPassword(password string) string {
	// Implement bcrypt password hashing
	return "hashed_" + password
}

func verifyPassword(password, hash string) bool {
	// Implement bcrypt password verification
	return hash == "hashed_"+password
}

func generateReferralCode() string {
	// Generate unique referral code
	return fmt.Sprintf("REF%d", time.Now().Unix())
}

func verifyTOTP(secret, code string) bool {
	// Implement TOTP verification
	return true
}

func main() {
	config := &Config{
		Port:           getEnv("PORT", "8080"),
		DatabaseURL:    getEnv("DATABASE_URL", "postgres://postgres:password@localhost/tigerex?sslmode=disable"),
		RedisURL:       getEnv("REDIS_URL", "redis://localhost:6379"),
		JWTSecret:      getEnv("JWT_SECRET", "your-secret-key"),
		Environment:    getEnv("ENVIRONMENT", "development"),
		RateLimitRPS:   getEnvInt("RATE_LIMIT_RPS", 100),
		RateLimitBurst: getEnvInt("RATE_LIMIT_BURST", 200),
	}

	api, err := NewAPIGateway(config)
	if err != nil {
		log.Fatal("Failed to initialize API Gateway:", err)
	}

	// Start WebSocket hub
	go api.hub.run()

	// Setup routes
	router := api.SetupRoutes()

	// Start server
	srv := &http.Server{
		Addr:    ":" + config.Port,
		Handler: router,
	}

	go func() {
		api.logger.Info("Starting TigerEx API Gateway", zap.String("port", config.Port))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			api.logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	api.logger.Info("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		api.logger.Fatal("Server forced to shutdown", zap.Error(err))
	}

	api.logger.Info("Server exited")
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}