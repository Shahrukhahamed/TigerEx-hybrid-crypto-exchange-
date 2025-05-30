/*
TigerEx Web3 Blockchain Integration Service
Advanced Go service for multi-chain Web3 integration, smart contract interaction,
and custom blockchain support for both CEX and DEX operations
*/

package main

import (
	"context"
	"crypto/ecdsa"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"math/big"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/ethereum/go-ethereum"
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/accounts/abi/bind"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/ethclient"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"github.com/gorilla/websocket"
	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"
	_ "github.com/lib/pq"
	"github.com/shopspring/decimal"
	"github.com/sirupsen/logrus"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Configuration
type Config struct {
	DatabaseURL    string
	RedisURL       string
	EthereumRPC    string
	BSCRPC         string
	PolygonRPC     string
	ArbitrumRPC    string
	OptimismRPC    string
	AvalancheRPC   string
	SolanaRPC      string
	PrivateKey     string
	Port           string
	CustomChains   map[string]ChainConfig
}

type ChainConfig struct {
	Name            string `json:"name"`
	ChainID         int64  `json:"chain_id"`
	RPCURL          string `json:"rpc_url"`
	ExplorerURL     string `json:"explorer_url"`
	NativeCurrency  Currency `json:"native_currency"`
	IsTestnet       bool   `json:"is_testnet"`
	BlockTime       int    `json:"block_time"`
	GasToken        string `json:"gas_token"`
	ConsensusType   string `json:"consensus_type"`
	MaxGasPrice     string `json:"max_gas_price"`
	MinGasPrice     string `json:"min_gas_price"`
}

type Currency struct {
	Name     string `json:"name"`
	Symbol   string `json:"symbol"`
	Decimals int    `json:"decimals"`
}

// Blockchain models
type Blockchain struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	Name            string    `gorm:"unique;not null" json:"name"`
	ChainID         int64     `gorm:"unique;not null" json:"chain_id"`
	RPCURL          string    `gorm:"not null" json:"rpc_url"`
	ExplorerURL     string    `json:"explorer_url"`
	NativeCurrency  string    `json:"native_currency"`
	IsTestnet       bool      `gorm:"default:false" json:"is_testnet"`
	IsActive        bool      `gorm:"default:true" json:"is_active"`
	BlockTime       int       `json:"block_time"`
	GasToken        string    `json:"gas_token"`
	ConsensusType   string    `json:"consensus_type"`
	MaxGasPrice     string    `json:"max_gas_price"`
	MinGasPrice     string    `json:"min_gas_price"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

type SmartContract struct {
	ID            uint      `gorm:"primaryKey" json:"id"`
	Name          string    `gorm:"not null" json:"name"`
	Address       string    `gorm:"not null" json:"address"`
	ABI           string    `gorm:"type:text" json:"abi"`
	Bytecode      string    `gorm:"type:text" json:"bytecode"`
	BlockchainID  uint      `json:"blockchain_id"`
	Blockchain    Blockchain `gorm:"foreignKey:BlockchainID" json:"blockchain"`
	ContractType  string    `json:"contract_type"` // ERC20, ERC721, DEX_ROUTER, etc.
	IsVerified    bool      `gorm:"default:false" json:"is_verified"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

type Transaction struct {
	ID            uint      `gorm:"primaryKey" json:"id"`
	Hash          string    `gorm:"unique;not null" json:"hash"`
	BlockNumber   uint64    `json:"block_number"`
	BlockHash     string    `json:"block_hash"`
	FromAddress   string    `json:"from_address"`
	ToAddress     string    `json:"to_address"`
	Value         string    `json:"value"`
	GasUsed       uint64    `json:"gas_used"`
	GasPrice      string    `json:"gas_price"`
	Status        int       `json:"status"` // 1 = success, 0 = failed
	BlockchainID  uint      `json:"blockchain_id"`
	Blockchain    Blockchain `gorm:"foreignKey:BlockchainID" json:"blockchain"`
	ContractID    *uint     `json:"contract_id,omitempty"`
	Contract      *SmartContract `gorm:"foreignKey:ContractID" json:"contract,omitempty"`
	MethodName    string    `json:"method_name"`
	InputData     string    `gorm:"type:text" json:"input_data"`
	Logs          string    `gorm:"type:text" json:"logs"`
	CreatedAt     time.Time `json:"created_at"`
}

type TokenBalance struct {
	ID           uint      `gorm:"primaryKey" json:"id"`
	UserID       string    `gorm:"not null" json:"user_id"`
	TokenAddress string    `gorm:"not null" json:"token_address"`
	Balance      string    `json:"balance"`
	BlockchainID uint      `json:"blockchain_id"`
	Blockchain   Blockchain `gorm:"foreignKey:BlockchainID" json:"blockchain"`
	LastUpdated  time.Time `json:"last_updated"`
}

type DEXPool struct {
	ID           uint      `gorm:"primaryKey" json:"id"`
	PoolAddress  string    `gorm:"unique;not null" json:"pool_address"`
	DEXProtocol  string    `gorm:"not null" json:"dex_protocol"`
	TokenA       string    `gorm:"not null" json:"token_a"`
	TokenB       string    `gorm:"not null" json:"token_b"`
	Reserve0     string    `json:"reserve_0"`
	Reserve1     string    `json:"reserve_1"`
	LiquidityUSD decimal.Decimal `json:"liquidity_usd"`
	Volume24h    decimal.Decimal `json:"volume_24h"`
	FeeTier      decimal.Decimal `json:"fee_tier"`
	APY          decimal.Decimal `json:"apy"`
	BlockchainID uint      `json:"blockchain_id"`
	Blockchain   Blockchain `gorm:"foreignKey:BlockchainID" json:"blockchain"`
	IsActive     bool      `gorm:"default:true" json:"is_active"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

// Web3 service
type Web3Service struct {
	clients       map[string]*ethclient.Client
	db            *gorm.DB
	redis         *redis.Client
	config        *Config
	privateKey    *ecdsa.PrivateKey
	publicAddress common.Address
	mu            sync.RWMutex
	wsUpgrader    websocket.Upgrader
}

// Initialize Web3 service
func NewWeb3Service(config *Config) (*Web3Service, error) {
	// Initialize database
	db, err := gorm.Open(postgres.Open(config.DatabaseURL), &gorm.Config{})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %v", err)
	}

	// Auto-migrate tables
	err = db.AutoMigrate(&Blockchain{}, &SmartContract{}, &Transaction{}, &TokenBalance{}, &DEXPool{})
	if err != nil {
		return nil, fmt.Errorf("failed to migrate database: %v", err)
	}

	// Initialize Redis
	opt, err := redis.ParseURL(config.RedisURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse Redis URL: %v", err)
	}
	redisClient := redis.NewClient(opt)

	// Initialize blockchain clients
	clients := make(map[string]*ethclient.Client)
	
	// Standard chains
	chains := map[string]string{
		"ethereum":  config.EthereumRPC,
		"bsc":       config.BSCRPC,
		"polygon":   config.PolygonRPC,
		"arbitrum":  config.ArbitrumRPC,
		"optimism":  config.OptimismRPC,
		"avalanche": config.AvalancheRPC,
	}

	for name, rpcURL := range chains {
		if rpcURL != "" {
			client, err := ethclient.Dial(rpcURL)
			if err != nil {
				logrus.Warnf("Failed to connect to %s: %v", name, err)
				continue
			}
			clients[name] = client
			logrus.Infof("Connected to %s blockchain", name)
		}
	}

	// Custom chains
	for name, chainConfig := range config.CustomChains {
		client, err := ethclient.Dial(chainConfig.RPCURL)
		if err != nil {
			logrus.Warnf("Failed to connect to custom chain %s: %v", name, err)
			continue
		}
		clients[name] = client
		logrus.Infof("Connected to custom chain: %s", name)
	}

	// Initialize private key
	var privateKey *ecdsa.PrivateKey
	var publicAddress common.Address
	if config.PrivateKey != "" {
		privateKey, err = crypto.HexToECDSA(config.PrivateKey)
		if err != nil {
			return nil, fmt.Errorf("failed to parse private key: %v", err)
		}
		publicKey := privateKey.Public()
		publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
		if !ok {
			return nil, fmt.Errorf("failed to cast public key to ECDSA")
		}
		publicAddress = crypto.PubkeyToAddress(*publicKeyECDSA)
	}

	service := &Web3Service{
		clients:       clients,
		db:            db,
		redis:         redisClient,
		config:        config,
		privateKey:    privateKey,
		publicAddress: publicAddress,
		wsUpgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins in development
			},
		},
	}

	// Initialize default blockchains in database
	service.initializeDefaultBlockchains()

	return service, nil
}

func (w *Web3Service) initializeDefaultBlockchains() {
	defaultChains := []Blockchain{
		{
			Name:           "Ethereum",
			ChainID:        1,
			RPCURL:         w.config.EthereumRPC,
			ExplorerURL:    "https://etherscan.io",
			NativeCurrency: "ETH",
			BlockTime:      12,
			GasToken:       "ETH",
			ConsensusType:  "Proof of Stake",
			MaxGasPrice:    "100000000000", // 100 gwei
			MinGasPrice:    "1000000000",   // 1 gwei
		},
		{
			Name:           "BSC",
			ChainID:        56,
			RPCURL:         w.config.BSCRPC,
			ExplorerURL:    "https://bscscan.com",
			NativeCurrency: "BNB",
			BlockTime:      3,
			GasToken:       "BNB",
			ConsensusType:  "Proof of Stake Authority",
			MaxGasPrice:    "20000000000", // 20 gwei
			MinGasPrice:    "5000000000",  // 5 gwei
		},
		{
			Name:           "Polygon",
			ChainID:        137,
			RPCURL:         w.config.PolygonRPC,
			ExplorerURL:    "https://polygonscan.com",
			NativeCurrency: "MATIC",
			BlockTime:      2,
			GasToken:       "MATIC",
			ConsensusType:  "Proof of Stake",
			MaxGasPrice:    "50000000000", // 50 gwei
			MinGasPrice:    "1000000000",  // 1 gwei
		},
		{
			Name:           "Arbitrum",
			ChainID:        42161,
			RPCURL:         w.config.ArbitrumRPC,
			ExplorerURL:    "https://arbiscan.io",
			NativeCurrency: "ETH",
			BlockTime:      1,
			GasToken:       "ETH",
			ConsensusType:  "Optimistic Rollup",
			MaxGasPrice:    "10000000000", // 10 gwei
			MinGasPrice:    "100000000",   // 0.1 gwei
		},
		{
			Name:           "Optimism",
			ChainID:        10,
			RPCURL:         w.config.OptimismRPC,
			ExplorerURL:    "https://optimistic.etherscan.io",
			NativeCurrency: "ETH",
			BlockTime:      2,
			GasToken:       "ETH",
			ConsensusType:  "Optimistic Rollup",
			MaxGasPrice:    "10000000000", // 10 gwei
			MinGasPrice:    "100000000",   // 0.1 gwei
		},
		{
			Name:           "Avalanche",
			ChainID:        43114,
			RPCURL:         w.config.AvalancheRPC,
			ExplorerURL:    "https://snowtrace.io",
			NativeCurrency: "AVAX",
			BlockTime:      2,
			GasToken:       "AVAX",
			ConsensusType:  "Avalanche Consensus",
			MaxGasPrice:    "50000000000", // 50 gwei
			MinGasPrice:    "25000000000", // 25 gwei
		},
	}

	for _, chain := range defaultChains {
		var existingChain Blockchain
		result := w.db.Where("chain_id = ?", chain.ChainID).First(&existingChain)
		if result.Error == gorm.ErrRecordNotFound {
			w.db.Create(&chain)
			logrus.Infof("Added blockchain: %s (Chain ID: %d)", chain.Name, chain.ChainID)
		}
	}
}

// Blockchain management
func (w *Web3Service) AddCustomBlockchain(chainConfig ChainConfig) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	// Test connection
	client, err := ethclient.Dial(chainConfig.RPCURL)
	if err != nil {
		return fmt.Errorf("failed to connect to blockchain: %v", err)
	}

	// Verify chain ID
	chainID, err := client.ChainID(context.Background())
	if err != nil {
		return fmt.Errorf("failed to get chain ID: %v", err)
	}

	if chainID.Int64() != chainConfig.ChainID {
		return fmt.Errorf("chain ID mismatch: expected %d, got %d", chainConfig.ChainID, chainID.Int64())
	}

	// Add to clients map
	w.clients[chainConfig.Name] = client

	// Save to database
	blockchain := Blockchain{
		Name:           chainConfig.Name,
		ChainID:        chainConfig.ChainID,
		RPCURL:         chainConfig.RPCURL,
		ExplorerURL:    chainConfig.ExplorerURL,
		NativeCurrency: chainConfig.NativeCurrency.Symbol,
		IsTestnet:      chainConfig.IsTestnet,
		BlockTime:      chainConfig.BlockTime,
		GasToken:       chainConfig.GasToken,
		ConsensusType:  chainConfig.ConsensusType,
		MaxGasPrice:    chainConfig.MaxGasPrice,
		MinGasPrice:    chainConfig.MinGasPrice,
	}

	result := w.db.Create(&blockchain)
	if result.Error != nil {
		return fmt.Errorf("failed to save blockchain to database: %v", result.Error)
	}

	logrus.Infof("Added custom blockchain: %s (Chain ID: %d)", chainConfig.Name, chainConfig.ChainID)
	return nil
}

func (w *Web3Service) GetSupportedBlockchains() ([]Blockchain, error) {
	var blockchains []Blockchain
	result := w.db.Where("is_active = ?", true).Find(&blockchains)
	return blockchains, result.Error
}

// Smart contract management
func (w *Web3Service) DeployContract(chainName, contractName, abiJSON, bytecode string, constructorArgs []interface{}) (*SmartContract, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	// Parse ABI
	contractABI, err := abi.JSON(strings.NewReader(abiJSON))
	if err != nil {
		return nil, fmt.Errorf("failed to parse ABI: %v", err)
	}

	// Get auth
	auth, err := w.getTransactOpts(chainName)
	if err != nil {
		return nil, fmt.Errorf("failed to get transaction options: %v", err)
	}

	// Deploy contract
	address, tx, _, err := bind.DeployContract(auth, contractABI, common.FromHex(bytecode), client, constructorArgs...)
	if err != nil {
		return nil, fmt.Errorf("failed to deploy contract: %v", err)
	}

	// Wait for transaction to be mined
	receipt, err := bind.WaitMined(context.Background(), client, tx)
	if err != nil {
		return nil, fmt.Errorf("failed to wait for transaction: %v", err)
	}

	if receipt.Status != types.ReceiptStatusSuccessful {
		return nil, fmt.Errorf("contract deployment failed")
	}

	// Get blockchain from database
	var blockchain Blockchain
	result := w.db.Where("name = ?", chainName).First(&blockchain)
	if result.Error != nil {
		return nil, fmt.Errorf("failed to find blockchain: %v", result.Error)
	}

	// Save contract to database
	contract := SmartContract{
		Name:         contractName,
		Address:      address.Hex(),
		ABI:          abiJSON,
		Bytecode:     bytecode,
		BlockchainID: blockchain.ID,
		ContractType: "CUSTOM",
		IsVerified:   false,
	}

	result = w.db.Create(&contract)
	if result.Error != nil {
		return nil, fmt.Errorf("failed to save contract: %v", result.Error)
	}

	logrus.Infof("Deployed contract %s at %s on %s", contractName, address.Hex(), chainName)
	return &contract, nil
}

func (w *Web3Service) CallContract(chainName, contractAddress, methodName string, args []interface{}) ([]interface{}, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	// Get contract from database
	var contract SmartContract
	result := w.db.Joins("Blockchain").Where("smart_contracts.address = ? AND blockchains.name = ?", contractAddress, chainName).First(&contract)
	if result.Error != nil {
		return nil, fmt.Errorf("contract not found: %v", result.Error)
	}

	// Parse ABI
	contractABI, err := abi.JSON(strings.NewReader(contract.ABI))
	if err != nil {
		return nil, fmt.Errorf("failed to parse ABI: %v", err)
	}

	// Create contract instance
	contractInstance := bind.NewBoundContract(common.HexToAddress(contractAddress), contractABI, client, client, client)

	// Call method
	var results []interface{}
	err = contractInstance.Call(&bind.CallOpts{}, &results, methodName, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to call contract method: %v", err)
	}

	return results, nil
}

func (w *Web3Service) SendTransaction(chainName, contractAddress, methodName string, args []interface{}) (*types.Transaction, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	// Get contract from database
	var contract SmartContract
	result := w.db.Joins("Blockchain").Where("smart_contracts.address = ? AND blockchains.name = ?", contractAddress, chainName).First(&contract)
	if result.Error != nil {
		return nil, fmt.Errorf("contract not found: %v", result.Error)
	}

	// Parse ABI
	contractABI, err := abi.JSON(strings.NewReader(contract.ABI))
	if err != nil {
		return nil, fmt.Errorf("failed to parse ABI: %v", err)
	}

	// Get auth
	auth, err := w.getTransactOpts(chainName)
	if err != nil {
		return nil, fmt.Errorf("failed to get transaction options: %v", err)
	}

	// Create contract instance
	contractInstance := bind.NewBoundContract(common.HexToAddress(contractAddress), contractABI, client, client, client)

	// Send transaction
	tx, err := contractInstance.Transact(auth, methodName, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to send transaction: %v", err)
	}

	// Save transaction to database
	w.saveTransaction(tx, chainName, &contract.ID, methodName)

	return tx, nil
}

// Token operations
func (w *Web3Service) GetTokenBalance(chainName, tokenAddress, userAddress string) (*big.Int, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	// ERC20 ABI for balanceOf function
	erc20ABI := `[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]`
	
	contractABI, err := abi.JSON(strings.NewReader(erc20ABI))
	if err != nil {
		return nil, fmt.Errorf("failed to parse ABI: %v", err)
	}

	// Create contract instance
	contractInstance := bind.NewBoundContract(common.HexToAddress(tokenAddress), contractABI, client, client, client)

	// Call balanceOf
	var results []interface{}
	err = contractInstance.Call(&bind.CallOpts{}, &results, "balanceOf", common.HexToAddress(userAddress))
	if err != nil {
		return nil, fmt.Errorf("failed to get token balance: %v", err)
	}

	balance, ok := results[0].(*big.Int)
	if !ok {
		return nil, fmt.Errorf("failed to parse balance")
	}

	// Update database
	w.updateTokenBalance(userAddress, tokenAddress, chainName, balance.String())

	return balance, nil
}

func (w *Web3Service) TransferToken(chainName, tokenAddress, toAddress string, amount *big.Int) (*types.Transaction, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	// ERC20 ABI for transfer function
	erc20ABI := `[{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]`
	
	contractABI, err := abi.JSON(strings.NewReader(erc20ABI))
	if err != nil {
		return nil, fmt.Errorf("failed to parse ABI: %v", err)
	}

	// Get auth
	auth, err := w.getTransactOpts(chainName)
	if err != nil {
		return nil, fmt.Errorf("failed to get transaction options: %v", err)
	}

	// Create contract instance
	contractInstance := bind.NewBoundContract(common.HexToAddress(tokenAddress), contractABI, client, client, client)

	// Send transfer transaction
	tx, err := contractInstance.Transact(auth, "transfer", common.HexToAddress(toAddress), amount)
	if err != nil {
		return nil, fmt.Errorf("failed to transfer token: %v", err)
	}

	// Save transaction to database
	w.saveTransaction(tx, chainName, nil, "transfer")

	return tx, nil
}

// DEX operations
func (w *Web3Service) GetDEXPools(chainName, tokenA, tokenB string) ([]DEXPool, error) {
	var pools []DEXPool
	result := w.db.Joins("Blockchain").Where("blockchains.name = ? AND ((token_a = ? AND token_b = ?) OR (token_a = ? AND token_b = ?))", 
		chainName, tokenA, tokenB, tokenB, tokenA).Find(&pools)
	return pools, result.Error
}

func (w *Web3Service) SwapTokens(chainName, dexRouter, tokenIn, tokenOut string, amountIn *big.Int, minAmountOut *big.Int) (*types.Transaction, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	// Uniswap V2 Router ABI (simplified)
	routerABI := `[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]`
	
	contractABI, err := abi.JSON(strings.NewReader(routerABI))
	if err != nil {
		return nil, fmt.Errorf("failed to parse ABI: %v", err)
	}

	// Get auth
	auth, err := w.getTransactOpts(chainName)
	if err != nil {
		return nil, fmt.Errorf("failed to get transaction options: %v", err)
	}

	// Create contract instance
	contractInstance := bind.NewBoundContract(common.HexToAddress(dexRouter), contractABI, client, client, client)

	// Prepare swap parameters
	path := []common.Address{common.HexToAddress(tokenIn), common.HexToAddress(tokenOut)}
	deadline := big.NewInt(time.Now().Add(20 * time.Minute).Unix())

	// Send swap transaction
	tx, err := contractInstance.Transact(auth, "swapExactTokensForTokens", amountIn, minAmountOut, path, w.publicAddress, deadline)
	if err != nil {
		return nil, fmt.Errorf("failed to swap tokens: %v", err)
	}

	// Save transaction to database
	w.saveTransaction(tx, chainName, nil, "swapExactTokensForTokens")

	return tx, nil
}

// Utility functions
func (w *Web3Service) getTransactOpts(chainName string) (*bind.TransactOpts, error) {
	client, exists := w.clients[chainName]
	if !exists {
		return nil, fmt.Errorf("blockchain %s not supported", chainName)
	}

	chainID, err := client.ChainID(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to get chain ID: %v", err)
	}

	auth, err := bind.NewKeyedTransactorWithChainID(w.privateKey, chainID)
	if err != nil {
		return nil, fmt.Errorf("failed to create transactor: %v", err)
	}

	// Get gas price
	gasPrice, err := client.SuggestGasPrice(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to get gas price: %v", err)
	}

	auth.GasPrice = gasPrice
	auth.GasLimit = uint64(300000) // Default gas limit

	return auth, nil
}

func (w *Web3Service) saveTransaction(tx *types.Transaction, chainName string, contractID *uint, methodName string) {
	var blockchain Blockchain
	w.db.Where("name = ?", chainName).First(&blockchain)

	transaction := Transaction{
		Hash:         tx.Hash().Hex(),
		FromAddress:  w.publicAddress.Hex(),
		ToAddress:    tx.To().Hex(),
		Value:        tx.Value().String(),
		GasPrice:     tx.GasPrice().String(),
		BlockchainID: blockchain.ID,
		ContractID:   contractID,
		MethodName:   methodName,
		InputData:    hex.EncodeToString(tx.Data()),
	}

	w.db.Create(&transaction)
}

func (w *Web3Service) updateTokenBalance(userAddress, tokenAddress, chainName, balance string) {
	var blockchain Blockchain
	w.db.Where("name = ?", chainName).First(&blockchain)

	tokenBalance := TokenBalance{
		UserID:       userAddress,
		TokenAddress: tokenAddress,
		Balance:      balance,
		BlockchainID: blockchain.ID,
		LastUpdated:  time.Now(),
	}

	w.db.Where("user_id = ? AND token_address = ? AND blockchain_id = ?", 
		userAddress, tokenAddress, blockchain.ID).
		Assign(tokenBalance).
		FirstOrCreate(&tokenBalance)
}

// API handlers
func (w *Web3Service) setupRoutes() *gin.Engine {
	r := gin.Default()
	
	// CORS middleware
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"*"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	api := r.Group("/api/v1")
	{
		// Blockchain management
		api.GET("/blockchains", w.getBlockchains)
		api.POST("/blockchains", w.addBlockchain)
		api.GET("/blockchains/:name/status", w.getBlockchainStatus)

		// Smart contracts
		api.POST("/contracts/deploy", w.deployContract)
		api.POST("/contracts/call", w.callContract)
		api.POST("/contracts/send", w.sendTransaction)
		api.GET("/contracts/:address", w.getContract)

		// Token operations
		api.GET("/tokens/balance", w.getTokenBalance)
		api.POST("/tokens/transfer", w.transferToken)
		api.GET("/tokens/:address/info", w.getTokenInfo)

		// DEX operations
		api.GET("/dex/pools", w.getDEXPools)
		api.POST("/dex/swap", w.swapTokens)
		api.GET("/dex/quote", w.getSwapQuote)

		// Transaction management
		api.GET("/transactions/:hash", w.getTransaction)
		api.GET("/transactions", w.getTransactions)

		// WebSocket endpoint
		api.GET("/ws", w.handleWebSocket)
	}

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().Unix(),
			"chains":    len(w.clients),
		})
	})

	return r
}

// API handler implementations
func (w *Web3Service) getBlockchains(c *gin.Context) {
	blockchains, err := w.GetSupportedBlockchains()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, blockchains)
}

func (w *Web3Service) addBlockchain(c *gin.Context) {
	var chainConfig ChainConfig
	if err := c.ShouldBindJSON(&chainConfig); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := w.AddCustomBlockchain(chainConfig)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Blockchain added successfully"})
}

func (w *Web3Service) getBlockchainStatus(c *gin.Context) {
	chainName := c.Param("name")
	client, exists := w.clients[chainName]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "Blockchain not found"})
		return
	}

	// Get latest block
	header, err := client.HeaderByNumber(context.Background(), nil)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Get chain ID
	chainID, err := client.ChainID(context.Background())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"chain_name":     chainName,
		"chain_id":       chainID.Int64(),
		"latest_block":   header.Number.Uint64(),
		"block_time":     header.Time,
		"gas_price":      header.BaseFee,
		"status":         "connected",
	})
}

func (w *Web3Service) deployContract(c *gin.Context) {
	var req struct {
		ChainName       string        `json:"chain_name" binding:"required"`
		ContractName    string        `json:"contract_name" binding:"required"`
		ABI             string        `json:"abi" binding:"required"`
		Bytecode        string        `json:"bytecode" binding:"required"`
		ConstructorArgs []interface{} `json:"constructor_args"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	contract, err := w.DeployContract(req.ChainName, req.ContractName, req.ABI, req.Bytecode, req.ConstructorArgs)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, contract)
}

func (w *Web3Service) callContract(c *gin.Context) {
	var req struct {
		ChainName       string        `json:"chain_name" binding:"required"`
		ContractAddress string        `json:"contract_address" binding:"required"`
		MethodName      string        `json:"method_name" binding:"required"`
		Args            []interface{} `json:"args"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	results, err := w.CallContract(req.ChainName, req.ContractAddress, req.MethodName, req.Args)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"results": results})
}

func (w *Web3Service) sendTransaction(c *gin.Context) {
	var req struct {
		ChainName       string        `json:"chain_name" binding:"required"`
		ContractAddress string        `json:"contract_address" binding:"required"`
		MethodName      string        `json:"method_name" binding:"required"`
		Args            []interface{} `json:"args"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	tx, err := w.SendTransaction(req.ChainName, req.ContractAddress, req.MethodName, req.Args)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"transaction_hash": tx.Hash().Hex(),
		"gas_price":        tx.GasPrice().String(),
		"gas_limit":        tx.Gas(),
	})
}

func (w *Web3Service) getContract(c *gin.Context) {
	address := c.Param("address")
	chainName := c.Query("chain")

	var contract SmartContract
	query := w.db.Joins("Blockchain").Where("smart_contracts.address = ?", address)
	if chainName != "" {
		query = query.Where("blockchains.name = ?", chainName)
	}

	result := query.First(&contract)
	if result.Error != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Contract not found"})
		return
	}

	c.JSON(http.StatusOK, contract)
}

func (w *Web3Service) getTokenBalance(c *gin.Context) {
	chainName := c.Query("chain")
	tokenAddress := c.Query("token")
	userAddress := c.Query("user")

	if chainName == "" || tokenAddress == "" || userAddress == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required parameters"})
		return
	}

	balance, err := w.GetTokenBalance(chainName, tokenAddress, userAddress)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"balance":       balance.String(),
		"token_address": tokenAddress,
		"user_address":  userAddress,
		"chain":         chainName,
	})
}

func (w *Web3Service) transferToken(c *gin.Context) {
	var req struct {
		ChainName    string `json:"chain_name" binding:"required"`
		TokenAddress string `json:"token_address" binding:"required"`
		ToAddress    string `json:"to_address" binding:"required"`
		Amount       string `json:"amount" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	amount, ok := new(big.Int).SetString(req.Amount, 10)
	if !ok {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid amount"})
		return
	}

	tx, err := w.TransferToken(req.ChainName, req.TokenAddress, req.ToAddress, amount)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"transaction_hash": tx.Hash().Hex(),
		"status":           "pending",
	})
}

func (w *Web3Service) getTokenInfo(c *gin.Context) {
	address := c.Param("address")
	chainName := c.Query("chain")

	if chainName == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Chain parameter required"})
		return
	}

	client, exists := w.clients[chainName]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "Blockchain not supported"})
		return
	}

	// ERC20 ABI for token info
	erc20ABI := `[
		{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
		{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
		{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
		{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}
	]`

	contractABI, err := abi.JSON(strings.NewReader(erc20ABI))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to parse ABI"})
		return
	}

	contractInstance := bind.NewBoundContract(common.HexToAddress(address), contractABI, client, client, client)

	// Get token info
	var name, symbol string
	var decimals uint8
	var totalSupply *big.Int

	// Call name
	var nameResult []interface{}
	err = contractInstance.Call(&bind.CallOpts{}, &nameResult, "name")
	if err == nil && len(nameResult) > 0 {
		name = nameResult[0].(string)
	}

	// Call symbol
	var symbolResult []interface{}
	err = contractInstance.Call(&bind.CallOpts{}, &symbolResult, "symbol")
	if err == nil && len(symbolResult) > 0 {
		symbol = symbolResult[0].(string)
	}

	// Call decimals
	var decimalsResult []interface{}
	err = contractInstance.Call(&bind.CallOpts{}, &decimalsResult, "decimals")
	if err == nil && len(decimalsResult) > 0 {
		decimals = decimalsResult[0].(uint8)
	}

	// Call totalSupply
	var totalSupplyResult []interface{}
	err = contractInstance.Call(&bind.CallOpts{}, &totalSupplyResult, "totalSupply")
	if err == nil && len(totalSupplyResult) > 0 {
		totalSupply = totalSupplyResult[0].(*big.Int)
	}

	c.JSON(http.StatusOK, gin.H{
		"address":      address,
		"name":         name,
		"symbol":       symbol,
		"decimals":     decimals,
		"total_supply": totalSupply.String(),
		"chain":        chainName,
	})
}

func (w *Web3Service) getDEXPools(c *gin.Context) {
	chainName := c.Query("chain")
	tokenA := c.Query("token_a")
	tokenB := c.Query("token_b")

	if chainName == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Chain parameter required"})
		return
	}

	pools, err := w.GetDEXPools(chainName, tokenA, tokenB)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, pools)
}

func (w *Web3Service) swapTokens(c *gin.Context) {
	var req struct {
		ChainName     string `json:"chain_name" binding:"required"`
		DEXRouter     string `json:"dex_router" binding:"required"`
		TokenIn       string `json:"token_in" binding:"required"`
		TokenOut      string `json:"token_out" binding:"required"`
		AmountIn      string `json:"amount_in" binding:"required"`
		MinAmountOut  string `json:"min_amount_out" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	amountIn, ok := new(big.Int).SetString(req.AmountIn, 10)
	if !ok {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid amount_in"})
		return
	}

	minAmountOut, ok := new(big.Int).SetString(req.MinAmountOut, 10)
	if !ok {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid min_amount_out"})
		return
	}

	tx, err := w.SwapTokens(req.ChainName, req.DEXRouter, req.TokenIn, req.TokenOut, amountIn, minAmountOut)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"transaction_hash": tx.Hash().Hex(),
		"status":           "pending",
	})
}

func (w *Web3Service) getSwapQuote(c *gin.Context) {
	// Implementation for getting swap quotes from DEX routers
	c.JSON(http.StatusOK, gin.H{
		"message": "Swap quote endpoint - implementation needed",
	})
}

func (w *Web3Service) getTransaction(c *gin.Context) {
	hash := c.Param("hash")

	var transaction Transaction
	result := w.db.Preload("Blockchain").Preload("Contract").Where("hash = ?", hash).First(&transaction)
	if result.Error != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Transaction not found"})
		return
	}

	c.JSON(http.StatusOK, transaction)
}

func (w *Web3Service) getTransactions(c *gin.Context) {
	userID := c.Query("user_id")
	chainName := c.Query("chain")
	limit := c.DefaultQuery("limit", "50")

	query := w.db.Preload("Blockchain").Preload("Contract")

	if userID != "" {
		query = query.Where("from_address = ? OR to_address = ?", userID, userID)
	}

	if chainName != "" {
		query = query.Joins("JOIN blockchains ON transactions.blockchain_id = blockchains.id").
			Where("blockchains.name = ?", chainName)
	}

	limitInt, _ := strconv.Atoi(limit)
	var transactions []Transaction
	result := query.Order("created_at DESC").Limit(limitInt).Find(&transactions)

	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	c.JSON(http.StatusOK, transactions)
}

func (w *Web3Service) handleWebSocket(c *gin.Context) {
	conn, err := w.wsUpgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		logrus.Error("Failed to upgrade WebSocket connection:", err)
		return
	}
	defer conn.Close()

	// Handle WebSocket messages
	for {
		var msg map[string]interface{}
		err := conn.ReadJSON(&msg)
		if err != nil {
			logrus.Error("WebSocket read error:", err)
			break
		}

		// Process WebSocket message
		response := map[string]interface{}{
			"type":      "response",
			"timestamp": time.Now().Unix(),
			"data":      "WebSocket connection established",
		}

		err = conn.WriteJSON(response)
		if err != nil {
			logrus.Error("WebSocket write error:", err)
			break
		}
	}
}

// Load configuration
func loadConfig() *Config {
	return &Config{
		DatabaseURL:  getEnv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tigerex"),
		RedisURL:     getEnv("REDIS_URL", "redis://localhost:6379"),
		EthereumRPC:  getEnv("ETHEREUM_RPC", "https://mainnet.infura.io/v3/YOUR_KEY"),
		BSCRPC:       getEnv("BSC_RPC", "https://bsc-dataseed.binance.org/"),
		PolygonRPC:   getEnv("POLYGON_RPC", "https://polygon-rpc.com/"),
		ArbitrumRPC:  getEnv("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc"),
		OptimismRPC:  getEnv("OPTIMISM_RPC", "https://mainnet.optimism.io"),
		AvalancheRPC: getEnv("AVALANCHE_RPC", "https://api.avax.network/ext/bc/C/rpc"),
		SolanaRPC:    getEnv("SOLANA_RPC", "https://api.mainnet-beta.solana.com"),
		PrivateKey:   getEnv("PRIVATE_KEY", ""),
		Port:         getEnv("PORT", "8089"),
		CustomChains: make(map[string]ChainConfig),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func main() {
	// Initialize logging
	logrus.SetFormatter(&logrus.JSONFormatter{})
	logrus.SetLevel(logrus.InfoLevel)

	// Load configuration
	config := loadConfig()

	// Initialize Web3 service
	service, err := NewWeb3Service(config)
	if err != nil {
		log.Fatal("Failed to initialize Web3 service:", err)
	}

	// Setup routes
	router := service.setupRoutes()

	// Start server
	logrus.Infof("Starting TigerEx Web3 Integration Service on port %s", config.Port)
	log.Fatal(http.ListenAndServe(":"+config.Port, router))
}