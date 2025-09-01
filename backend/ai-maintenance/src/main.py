"""
TigerEx AI-Based Maintenance System
Intelligent system monitoring, optimization, and automated maintenance
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow import keras
import psutil
import docker
import kubernetes
from kubernetes import client, config
import redis
import asyncpg
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import schedule
import time
from threading import Thread
import pickle
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx AI Maintenance System",
    description="Intelligent system monitoring and automated maintenance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/tigerex")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    KUBERNETES_NAMESPACE = os.getenv("KUBERNETES_NAMESPACE", "tigerex")
    
    # AI Model paths
    ANOMALY_MODEL_PATH = "models/anomaly_detection.pkl"
    PERFORMANCE_MODEL_PATH = "models/performance_prediction.h5"
    OPTIMIZATION_MODEL_PATH = "models/optimization.pkl"
    
    # Monitoring intervals
    SYSTEM_MONITOR_INTERVAL = 60  # seconds
    PERFORMANCE_ANALYSIS_INTERVAL = 300  # 5 minutes
    OPTIMIZATION_INTERVAL = 3600  # 1 hour
    
    # Thresholds
    CPU_THRESHOLD = 80.0
    MEMORY_THRESHOLD = 85.0
    DISK_THRESHOLD = 90.0
    RESPONSE_TIME_THRESHOLD = 1000  # ms
    ERROR_RATE_THRESHOLD = 0.05  # 5%

config = Config()

# Enums
class TaskType(str, Enum):
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_SCAN = "security_scan"
    DATABASE_OPTIMIZATION = "database_optimization"
    LOAD_BALANCING = "load_balancing"
    RESOURCE_SCALING = "resource_scaling"
    ANOMALY_DETECTION = "anomaly_detection"
    PREDICTIVE_MAINTENANCE = "predictive_maintenance"
    SYSTEM_CLEANUP = "system_cleanup"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecommendationType(str, Enum):
    PERFORMANCE = "performance"
    SECURITY = "security"
    OPTIMIZATION = "optimization"
    MAINTENANCE = "maintenance"
    SCALING = "scaling"

# Data Models
@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    response_time: float
    error_rate: float
    active_connections: int
    queue_size: int
    throughput: float

@dataclass
class AITask:
    id: str
    task_type: TaskType
    status: TaskStatus
    priority: Priority
    parameters: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    result_summary: Optional[str]
    result_data: Optional[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    actions_taken: List[Dict[str, Any]]
    manual_review_required: bool
    created_at: datetime

@dataclass
class AIRecommendation:
    id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    priority: Priority
    estimated_impact: str
    implementation_steps: List[str]
    estimated_time: str
    risk_level: str
    confidence_score: float
    created_at: datetime

# Pydantic Models
class CreateTaskRequest(BaseModel):
    task_type: TaskType
    priority: Priority = Priority.MEDIUM
    parameters: Dict[str, Any] = {}
    schedule_cron: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    task_type: TaskType
    status: TaskStatus
    priority: Priority
    progress: int
    result_summary: Optional[str]
    recommendations: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

# AI Maintenance System Manager
class AIMaintenanceManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.k8s_client = self.initialize_kubernetes()
        self.redis_client = redis.from_url(config.REDIS_URL)
        self.running_tasks = {}
        self.models = {}
        self.metrics_history = []
        
        # Initialize AI models
        asyncio.create_task(self.initialize_ai_models())
        
        # Start background monitoring
        self.start_background_monitoring()
    
    def initialize_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        return client.ApiClient()
    
    async def initialize_ai_models(self):
        """Initialize and load AI models"""
        try:
            # Load anomaly detection model
            if os.path.exists(config.ANOMALY_MODEL_PATH):
                self.models['anomaly'] = joblib.load(config.ANOMALY_MODEL_PATH)
            else:
                self.models['anomaly'] = self.create_anomaly_model()
                joblib.dump(self.models['anomaly'], config.ANOMALY_MODEL_PATH)
            
            # Load performance prediction model
            if os.path.exists(config.PERFORMANCE_MODEL_PATH):
                self.models['performance'] = keras.models.load_model(config.PERFORMANCE_MODEL_PATH)
            else:
                self.models['performance'] = self.create_performance_model()
                self.models['performance'].save(config.PERFORMANCE_MODEL_PATH)
            
            # Load optimization model
            if os.path.exists(config.OPTIMIZATION_MODEL_PATH):
                self.models['optimization'] = joblib.load(config.OPTIMIZATION_MODEL_PATH)
            else:
                self.models['optimization'] = self.create_optimization_model()
                joblib.dump(self.models['optimization'], config.OPTIMIZATION_MODEL_PATH)
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
    
    def create_anomaly_model(self):
        """Create anomaly detection model"""
        return IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
    
    def create_performance_model(self):
        """Create performance prediction neural network"""
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(10,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='linear')
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def create_optimization_model(self):
        """Create resource optimization model"""
        return RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
    
    def start_background_monitoring(self):
        """Start background monitoring threads"""
        def run_scheduler():
            schedule.every(config.SYSTEM_MONITOR_INTERVAL).seconds.do(
                lambda: asyncio.create_task(self.collect_system_metrics())
            )
            schedule.every(config.PERFORMANCE_ANALYSIS_INTERVAL).seconds.do(
                lambda: asyncio.create_task(self.analyze_performance())
            )
            schedule.every(config.OPTIMIZATION_INTERVAL).seconds.do(
                lambda: asyncio.create_task(self.run_optimization())
            )
            
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    async def collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Application metrics
            response_time = await self.measure_response_time()
            error_rate = await self.calculate_error_rate()
            active_connections = await self.get_active_connections()
            queue_size = await self.get_queue_size()
            throughput = await self.calculate_throughput()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                response_time=response_time,
                error_rate=error_rate,
                active_connections=active_connections,
                queue_size=queue_size,
                throughput=throughput
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            # Store in Redis for real-time access
            await self.store_metrics_in_redis(metrics)
            
            # Check for anomalies
            await self.detect_anomalies(metrics)
            
            # Check thresholds
            await self.check_thresholds(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def measure_response_time(self) -> float:
        """Measure API response time"""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8000/health') as response:
                    await response.text()
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except:
            return 0.0
    
    async def calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        try:
            # Get error count from Redis
            error_count = await self.redis_client.get('error_count_1min') or 0
            total_requests = await self.redis_client.get('request_count_1min') or 1
            return float(error_count) / float(total_requests)
        except:
            return 0.0
    
    async def get_active_connections(self) -> int:
        """Get number of active connections"""
        try:
            return int(await self.redis_client.get('active_connections') or 0)
        except:
            return 0
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            return int(await self.redis_client.get('queue_size') or 0)
        except:
            return 0
    
    async def calculate_throughput(self) -> float:
        """Calculate current throughput (requests per second)"""
        try:
            requests_1min = await self.redis_client.get('request_count_1min') or 0
            return float(requests_1min) / 60.0
        except:
            return 0.0
    
    async def store_metrics_in_redis(self, metrics: SystemMetrics):
        """Store metrics in Redis for real-time access"""
        try:
            metrics_data = {
                'timestamp': metrics.timestamp.isoformat(),
                'cpu_usage': metrics.cpu_usage,
                'memory_usage': metrics.memory_usage,
                'disk_usage': metrics.disk_usage,
                'response_time': metrics.response_time,
                'error_rate': metrics.error_rate,
                'active_connections': metrics.active_connections,
                'throughput': metrics.throughput
            }
            
            await self.redis_client.setex(
                'current_metrics',
                300,  # 5 minutes TTL
                json.dumps(metrics_data)
            )
            
        except Exception as e:
            logger.error(f"Error storing metrics in Redis: {e}")
    
    async def detect_anomalies(self, metrics: SystemMetrics):
        """Detect anomalies using AI model"""
        try:
            if len(self.metrics_history) < 10:
                return  # Need more data for anomaly detection
            
            # Prepare data for anomaly detection
            features = self.prepare_features_for_anomaly_detection()
            
            if len(features) > 0:
                # Predict anomalies
                anomaly_scores = self.models['anomaly'].decision_function(features)
                is_anomaly = self.models['anomaly'].predict(features)
                
                # Check if current metrics are anomalous
                if is_anomaly[-1] == -1:  # -1 indicates anomaly
                    await self.handle_anomaly_detected(metrics, anomaly_scores[-1])
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
    
    def prepare_features_for_anomaly_detection(self) -> np.ndarray:
        """Prepare features for anomaly detection"""
        features = []
        for metrics in self.metrics_history[-100:]:  # Last 100 data points
            feature_vector = [
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.disk_usage,
                metrics.response_time,
                metrics.error_rate,
                metrics.active_connections,
                metrics.queue_size,
                metrics.throughput,
                metrics.network_io.get('bytes_sent', 0) / 1024 / 1024,  # MB
                metrics.network_io.get('bytes_recv', 0) / 1024 / 1024   # MB
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    async def handle_anomaly_detected(self, metrics: SystemMetrics, anomaly_score: float):
        """Handle detected anomaly"""
        try:
            # Create anomaly detection task
            task_id = f"anomaly_{int(datetime.now().timestamp())}"
            
            task = AITask(
                id=task_id,
                task_type=TaskType.ANOMALY_DETECTION,
                status=TaskStatus.RUNNING,
                priority=Priority.HIGH,
                parameters={
                    'anomaly_score': float(anomaly_score),
                    'metrics': {
                        'cpu_usage': metrics.cpu_usage,
                        'memory_usage': metrics.memory_usage,
                        'response_time': metrics.response_time,
                        'error_rate': metrics.error_rate
                    }
                },
                started_at=datetime.now(),
                completed_at=None,
                execution_time_ms=None,
                result_summary=None,
                result_data=None,
                recommendations=[],
                actions_taken=[],
                manual_review_required=True,
                created_at=datetime.now()
            )
            
            # Analyze anomaly and generate recommendations
            recommendations = await self.analyze_anomaly(metrics, anomaly_score)
            task.recommendations = recommendations
            
            # Take automated actions if safe
            actions_taken = await self.take_automated_actions(recommendations)
            task.actions_taken = actions_taken
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result_summary = f"Anomaly detected with score {anomaly_score:.3f}. {len(recommendations)} recommendations generated."
            
            # Store task
            self.running_tasks[task_id] = task
            
            # Send alert
            await self.send_anomaly_alert(task)
            
            logger.warning(f"Anomaly detected: {task.result_summary}")
            
        except Exception as e:
            logger.error(f"Error handling anomaly: {e}")
    
    async def analyze_anomaly(self, metrics: SystemMetrics, anomaly_score: float) -> List[Dict[str, Any]]:
        """Analyze anomaly and generate recommendations"""
        recommendations = []
        
        # High CPU usage
        if metrics.cpu_usage > config.CPU_THRESHOLD:
            recommendations.append({
                'type': 'performance',
                'title': 'High CPU Usage Detected',
                'description': f'CPU usage is at {metrics.cpu_usage:.1f}%, exceeding threshold of {config.CPU_THRESHOLD}%',
                'priority': 'high',
                'actions': [
                    'Scale up CPU resources',
                    'Optimize CPU-intensive processes',
                    'Enable CPU throttling for non-critical services'
                ],
                'estimated_impact': 'Reduce CPU usage by 20-30%'
            })
        
        # High memory usage
        if metrics.memory_usage > config.MEMORY_THRESHOLD:
            recommendations.append({
                'type': 'performance',
                'title': 'High Memory Usage Detected',
                'description': f'Memory usage is at {metrics.memory_usage:.1f}%, exceeding threshold of {config.MEMORY_THRESHOLD}%',
                'priority': 'high',
                'actions': [
                    'Scale up memory resources',
                    'Clear memory caches',
                    'Restart memory-intensive services'
                ],
                'estimated_impact': 'Reduce memory usage by 15-25%'
            })
        
        # High response time
        if metrics.response_time > config.RESPONSE_TIME_THRESHOLD:
            recommendations.append({
                'type': 'performance',
                'title': 'High Response Time Detected',
                'description': f'Response time is {metrics.response_time:.1f}ms, exceeding threshold of {config.RESPONSE_TIME_THRESHOLD}ms',
                'priority': 'medium',
                'actions': [
                    'Optimize database queries',
                    'Enable response caching',
                    'Scale up application instances'
                ],
                'estimated_impact': 'Reduce response time by 30-50%'
            })
        
        # High error rate
        if metrics.error_rate > config.ERROR_RATE_THRESHOLD:
            recommendations.append({
                'type': 'security',
                'title': 'High Error Rate Detected',
                'description': f'Error rate is {metrics.error_rate:.3f}, exceeding threshold of {config.ERROR_RATE_THRESHOLD}',
                'priority': 'critical',
                'actions': [
                    'Investigate error logs',
                    'Check service health',
                    'Implement circuit breakers'
                ],
                'estimated_impact': 'Reduce error rate by 80-90%'
            })
        
        return recommendations
    
    async def take_automated_actions(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Take safe automated actions based on recommendations"""
        actions_taken = []
        
        for recommendation in recommendations:
            if recommendation['type'] == 'performance':
                if 'Clear memory caches' in recommendation['actions']:
                    try:
                        # Clear Redis cache
                        await self.redis_client.flushdb()
                        actions_taken.append({
                            'action': 'Clear memory caches',
                            'status': 'completed',
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        actions_taken.append({
                            'action': 'Clear memory caches',
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
                
                if 'Enable response caching' in recommendation['actions']:
                    try:
                        # Enable caching in Redis
                        await self.redis_client.set('caching_enabled', 'true', ex=3600)
                        actions_taken.append({
                            'action': 'Enable response caching',
                            'status': 'completed',
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        actions_taken.append({
                            'action': 'Enable response caching',
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
        
        return actions_taken
    
    async def check_thresholds(self, metrics: SystemMetrics):
        """Check if metrics exceed thresholds"""
        alerts = []
        
        if metrics.cpu_usage > config.CPU_THRESHOLD:
            alerts.append(f"CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > config.MEMORY_THRESHOLD:
            alerts.append(f"Memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.disk_usage > config.DISK_THRESHOLD:
            alerts.append(f"Disk usage: {metrics.disk_usage:.1f}%")
        
        if metrics.response_time > config.RESPONSE_TIME_THRESHOLD:
            alerts.append(f"Response time: {metrics.response_time:.1f}ms")
        
        if metrics.error_rate > config.ERROR_RATE_THRESHOLD:
            alerts.append(f"Error rate: {metrics.error_rate:.3f}")
        
        if alerts:
            await self.send_threshold_alert(alerts)
    
    async def analyze_performance(self):
        """Analyze system performance and predict future issues"""
        try:
            if len(self.metrics_history) < 50:
                return  # Need more data for analysis
            
            # Prepare data for performance prediction
            features = self.prepare_features_for_performance_prediction()
            
            if len(features) > 0:
                # Predict future performance
                predictions = self.models['performance'].predict(features[-10:])
                
                # Analyze trends
                trends = self.analyze_performance_trends()
                
                # Generate performance recommendations
                recommendations = await self.generate_performance_recommendations(predictions, trends)
                
                if recommendations:
                    # Create performance optimization task
                    await self.create_performance_task(recommendations)
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
    
    def prepare_features_for_performance_prediction(self) -> np.ndarray:
        """Prepare features for performance prediction"""
        features = []
        for i in range(len(self.metrics_history) - 10):
            # Use sliding window of 10 metrics
            window = self.metrics_history[i:i+10]
            feature_vector = []
            
            for metrics in window:
                feature_vector.extend([
                    metrics.cpu_usage / 100.0,
                    metrics.memory_usage / 100.0,
                    metrics.response_time / 1000.0,
                    metrics.error_rate,
                    metrics.throughput / 100.0,
                    metrics.active_connections / 1000.0,
                    metrics.queue_size / 100.0,
                    metrics.disk_usage / 100.0,
                    metrics.network_io.get('bytes_sent', 0) / 1024 / 1024 / 1000,
                    metrics.network_io.get('bytes_recv', 0) / 1024 / 1024 / 1000
                ])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends"""
        if len(self.metrics_history) < 20:
            return {}
        
        recent_metrics = self.metrics_history[-20:]
        
        # Calculate trends
        cpu_trend = np.polyfit(range(len(recent_metrics)), [m.cpu_usage for m in recent_metrics], 1)[0]
        memory_trend = np.polyfit(range(len(recent_metrics)), [m.memory_usage for m in recent_metrics], 1)[0]
        response_time_trend = np.polyfit(range(len(recent_metrics)), [m.response_time for m in recent_metrics], 1)[0]
        error_rate_trend = np.polyfit(range(len(recent_metrics)), [m.error_rate for m in recent_metrics], 1)[0]
        
        return {
            'cpu_trend': float(cpu_trend),
            'memory_trend': float(memory_trend),
            'response_time_trend': float(response_time_trend),
            'error_rate_trend': float(error_rate_trend)
        }
    
    async def generate_performance_recommendations(self, predictions: np.ndarray, trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Check if CPU trend is increasing
        if trends.get('cpu_trend', 0) > 0.5:
            recommendations.append({
                'type': 'optimization',
                'title': 'CPU Usage Trending Upward',
                'description': 'CPU usage is showing an increasing trend. Consider optimization.',
                'priority': 'medium',
                'actions': [
                    'Profile CPU-intensive processes',
                    'Optimize algorithms',
                    'Consider horizontal scaling'
                ],
                'estimated_impact': 'Prevent future CPU bottlenecks'
            })
        
        # Check if memory trend is increasing
        if trends.get('memory_trend', 0) > 0.3:
            recommendations.append({
                'type': 'optimization',
                'title': 'Memory Usage Trending Upward',
                'description': 'Memory usage is showing an increasing trend. Potential memory leak.',
                'priority': 'high',
                'actions': [
                    'Check for memory leaks',
                    'Optimize memory usage',
                    'Implement garbage collection tuning'
                ],
                'estimated_impact': 'Prevent memory exhaustion'
            })
        
        # Check if response time is increasing
        if trends.get('response_time_trend', 0) > 10:
            recommendations.append({
                'type': 'performance',
                'title': 'Response Time Degrading',
                'description': 'Response time is showing a degrading trend.',
                'priority': 'medium',
                'actions': [
                    'Optimize database queries',
                    'Implement caching',
                    'Review API endpoints'
                ],
                'estimated_impact': 'Improve user experience'
            })
        
        return recommendations
    
    async def run_optimization(self):
        """Run system optimization tasks"""
        try:
            # Database optimization
            await self.optimize_database()
            
            # Resource optimization
            await self.optimize_resources()
            
            # Cache optimization
            await self.optimize_cache()
            
            # Load balancing optimization
            await self.optimize_load_balancing()
            
        except Exception as e:
            logger.error(f"Error running optimization: {e}")
    
    async def optimize_database(self):
        """Optimize database performance"""
        try:
            # Connect to database
            conn = await asyncpg.connect(config.DATABASE_URL)
            
            # Analyze slow queries
            slow_queries = await conn.fetch("""
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements
                WHERE mean_time > 100
                ORDER BY mean_time DESC
                LIMIT 10
            """)
            
            recommendations = []
            for query in slow_queries:
                recommendations.append({
                    'type': 'database',
                    'title': f'Slow Query Detected',
                    'description': f'Query with mean time {query["mean_time"]:.2f}ms',
                    'query': query['query'][:100] + '...',
                    'actions': ['Add index', 'Optimize query', 'Use query cache']
                })
            
            # Update table statistics
            await conn.execute("ANALYZE;")
            
            # Vacuum tables if needed
            await conn.execute("VACUUM ANALYZE;")
            
            await conn.close()
            
            if recommendations:
                await self.create_database_optimization_task(recommendations)
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
    
    async def optimize_resources(self):
        """Optimize system resources"""
        try:
            # Get current resource usage
            current_metrics = self.metrics_history[-1] if self.metrics_history else None
            if not current_metrics:
                return
            
            recommendations = []
            
            # Check if scaling is needed
            if current_metrics.cpu_usage > 70:
                recommendations.append({
                    'type': 'scaling',
                    'title': 'CPU Scaling Recommended',
                    'description': f'CPU usage at {current_metrics.cpu_usage:.1f}%',
                    'action': 'scale_up_cpu',
                    'estimated_impact': 'Reduce CPU load by 30%'
                })
            
            if current_metrics.memory_usage > 75:
                recommendations.append({
                    'type': 'scaling',
                    'title': 'Memory Scaling Recommended',
                    'description': f'Memory usage at {current_metrics.memory_usage:.1f}%',
                    'action': 'scale_up_memory',
                    'estimated_impact': 'Reduce memory pressure'
                })
            
            # Auto-scale if configured
            for recommendation in recommendations:
                if recommendation['action'] == 'scale_up_cpu':
                    await self.scale_kubernetes_deployment('cpu')
                elif recommendation['action'] == 'scale_up_memory':
                    await self.scale_kubernetes_deployment('memory')
            
        except Exception as e:
            logger.error(f"Error optimizing resources: {e}")
    
    async def scale_kubernetes_deployment(self, resource_type: str):
        """Scale Kubernetes deployment"""
        try:
            apps_v1 = client.AppsV1Api(self.k8s_client)
            
            # Get current deployment
            deployment = apps_v1.read_namespaced_deployment(
                name="tigerex-api",
                namespace=config.KUBERNETES_NAMESPACE
            )
            
            # Scale up replicas
            current_replicas = deployment.spec.replicas
            new_replicas = min(current_replicas + 1, 10)  # Max 10 replicas
            
            deployment.spec.replicas = new_replicas
            
            # Update deployment
            apps_v1.patch_namespaced_deployment(
                name="tigerex-api",
                namespace=config.KUBERNETES_NAMESPACE,
                body=deployment
            )
            
            logger.info(f"Scaled deployment from {current_replicas} to {new_replicas} replicas")
            
        except Exception as e:
            logger.error(f"Error scaling Kubernetes deployment: {e}")
    
    async def send_anomaly_alert(self, task: AITask):
        """Send anomaly alert"""
        try:
            # Send email alert (simplified)
            subject = f"TigerEx AI Alert: Anomaly Detected"
            body = f"""
            Anomaly detected in TigerEx system:
            
            Task ID: {task.id}
            Anomaly Score: {task.parameters.get('anomaly_score', 'N/A')}
            Recommendations: {len(task.recommendations)}
            Actions Taken: {len(task.actions_taken)}
            
            Please review the system status.
            """
            
            # In production, implement proper email sending
            logger.warning(f"ALERT: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending anomaly alert: {e}")
    
    async def send_threshold_alert(self, alerts: List[str]):
        """Send threshold alert"""
        try:
            subject = f"TigerEx Threshold Alert"
            body = f"The following metrics exceeded thresholds:\n\n" + "\n".join(alerts)
            
            logger.warning(f"THRESHOLD ALERT: {', '.join(alerts)}")
            
        except Exception as e:
            logger.error(f"Error sending threshold alert: {e}")
    
    async def create_performance_task(self, recommendations: List[Dict[str, Any]]):
        """Create performance optimization task"""
        task_id = f"perf_{int(datetime.now().timestamp())}"
        
        task = AITask(
            id=task_id,
            task_type=TaskType.PERFORMANCE_OPTIMIZATION,
            status=TaskStatus.COMPLETED,
            priority=Priority.MEDIUM,
            parameters={},
            started_at=datetime.now(),
            completed_at=datetime.now(),
            execution_time_ms=0,
            result_summary=f"Performance analysis completed. {len(recommendations)} recommendations generated.",
            result_data={'trends': self.analyze_performance_trends()},
            recommendations=recommendations,
            actions_taken=[],
            manual_review_required=True,
            created_at=datetime.now()
        )
        
        self.running_tasks[task_id] = task
    
    async def create_database_optimization_task(self, recommendations: List[Dict[str, Any]]):
        """Create database optimization task"""
        task_id = f"db_{int(datetime.now().timestamp())}"
        
        task = AITask(
            id=task_id,
            task_type=TaskType.DATABASE_OPTIMIZATION,
            status=TaskStatus.COMPLETED,
            priority=Priority.MEDIUM,
            parameters={},
            started_at=datetime.now(),
            completed_at=datetime.now(),
            execution_time_ms=0,
            result_summary=f"Database optimization completed. {len(recommendations)} recommendations generated.",
            result_data={},
            recommendations=recommendations,
            actions_taken=[
                {
                    'action': 'Update table statistics',
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'action': 'Vacuum analyze tables',
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                }
            ],
            manual_review_required=False,
            created_at=datetime.now()
        )
        
        self.running_tasks[task_id] = task

# Initialize AI maintenance manager
ai_manager = AIMaintenanceManager()

# API Endpoints
@app.post("/api/v1/ai/tasks/create")
async def create_ai_task(request: CreateTaskRequest):
    """Create a new AI maintenance task"""
    try:
        task_id = f"{request.task_type.value}_{int(datetime.now().timestamp())}"
        
        task = AITask(
            id=task_id,
            task_type=request.task_type,
            status=TaskStatus.PENDING,
            priority=request.priority,
            parameters=request.parameters,
            started_at=None,
            completed_at=None,
            execution_time_ms=None,
            result_summary=None,
            result_data=None,
            recommendations=[],
            actions_taken=[],
            manual_review_required=False,
            created_at=datetime.now()
        )
        
        ai_manager.running_tasks[task_id] = task
        
        return {
            "task_id": task_id,
            "status": "created",
            "message": "AI maintenance task created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating AI task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/tasks")
async def get_ai_tasks():
    """Get all AI maintenance tasks"""
    try:
        tasks = []
        for task in ai_manager.running_tasks.values():
            tasks.append({
                "id": task.id,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "priority": task.priority.value,
                "progress": 100 if task.status == TaskStatus.COMPLETED else 
                          50 if task.status == TaskStatus.RUNNING else 0,
                "result_summary": task.result_summary,
                "recommendations": task.recommendations,
                "created_at": task.created_at,
                "updated_at": task.completed_at or task.started_at or task.created_at
            })
        
        return {"tasks": tasks}
        
    except Exception as e:
        logger.error(f"Error getting AI tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/tasks/{task_id}")
async def get_ai_task(task_id: str):
    """Get specific AI maintenance task"""
    try:
        task = ai_manager.running_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "id": task.id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "priority": task.priority.value,
            "parameters": task.parameters,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "execution_time_ms": task.execution_time_ms,
            "result_summary": task.result_summary,
            "result_data": task.result_data,
            "recommendations": task.recommendations,
            "actions_taken": task.actions_taken,
            "manual_review_required": task.manual_review_required,
            "created_at": task.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/metrics/current")
async def get_current_metrics():
    """Get current system metrics"""
    try:
        metrics_data = await ai_manager.redis_client.get('current_metrics')
        if metrics_data:
            return json.loads(metrics_data)
        else:
            return {"message": "No current metrics available"}
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/recommendations")
async def get_ai_recommendations():
    """Get AI-generated recommendations"""
    try:
        recommendations = []
        
        for task in ai_manager.running_tasks.values():
            if task.recommendations:
                for rec in task.recommendations:
                    recommendations.append({
                        "task_id": task.id,
                        "task_type": task.task_type.value,
                        "recommendation": rec,
                        "created_at": task.created_at
                    })
        
        # Sort by priority and creation time
        recommendations.sort(key=lambda x: (
            0 if x['recommendation'].get('priority') == 'critical' else
            1 if x['recommendation'].get('priority') == 'high' else
            2 if x['recommendation'].get('priority') == 'medium' else 3,
            x['created_at']
        ), reverse=True)
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"Error getting AI recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/recommendations/{task_id}/apply")
async def apply_recommendation(task_id: str, recommendation_index: int):
    """Apply a specific recommendation"""
    try:
        task = ai_manager.running_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if recommendation_index >= len(task.recommendations):
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        recommendation = task.recommendations[recommendation_index]
        
        # Apply recommendation (simplified implementation)
        actions_taken = await ai_manager.take_automated_actions([recommendation])
        task.actions_taken.extend(actions_taken)
        
        return {
            "message": "Recommendation applied successfully",
            "actions_taken": actions_taken
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/health")
async def ai_health_check():
    """AI system health check"""
    try:
        health_status = {
            "status": "healthy",
            "models_loaded": len(ai_manager.models),
            "active_tasks": len([t for t in ai_manager.running_tasks.values() if t.status == TaskStatus.RUNNING]),
            "completed_tasks": len([t for t in ai_manager.running_tasks.values() if t.status == TaskStatus.COMPLETED]),
            "metrics_history_size": len(ai_manager.metrics_history),
            "timestamp": datetime.now()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking AI health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
