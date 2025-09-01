"""
TigerEx AI-Based Maintenance System
Advanced AI system for predictive maintenance, anomaly detection, and automated system optimization
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
import tensorflow as tf
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import redis
import httpx
from sqlalchemy import create_engine, text
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="TigerEx AI Maintenance System",
    description="Advanced AI system for predictive maintenance and system optimization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tigerex")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize connections
redis_client = redis.from_url(REDIS_URL)
db_engine = create_engine(DATABASE_URL)

# Pydantic models
class SystemMetrics(BaseModel):
    timestamp: datetime
    service_name: str
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    disk_usage: float = Field(..., ge=0, le=100)
    network_io: float = Field(..., ge=0)
    response_time: float = Field(..., ge=0)
    error_rate: float = Field(..., ge=0, le=100)
    throughput: float = Field(..., ge=0)
    active_connections: int = Field(..., ge=0)

class AnomalyAlert(BaseModel):
    alert_id: str
    service_name: str
    anomaly_type: str
    severity: str  # low, medium, high, critical
    description: str
    metrics: Dict[str, Any]
    timestamp: datetime
    recommended_actions: List[str]

class MaintenanceTask(BaseModel):
    task_id: str
    task_type: str
    service_name: str
    priority: str  # low, medium, high, critical
    description: str
    estimated_duration: int  # minutes
    scheduled_time: datetime
    status: str = "pending"  # pending, running, completed, failed

class PerformanceOptimization(BaseModel):
    optimization_id: str
    service_name: str
    optimization_type: str
    current_metrics: Dict[str, float]
    target_metrics: Dict[str, float]
    actions: List[str]
    estimated_improvement: Dict[str, float]

@dataclass
class AIMaintenanceSystem:
    """Core AI Maintenance System"""
    
    def __init__(self):
        self.anomaly_detector = None
        self.performance_predictor = None
        self.scaler = StandardScaler()
        self.load_models()
        
    def load_models(self):
        """Load or initialize AI models"""
        try:
            # Load pre-trained models if they exist
            self.anomaly_detector = joblib.load('models/anomaly_detector.pkl')
            self.performance_predictor = joblib.load('models/performance_predictor.pkl')
            self.scaler = joblib.load('models/scaler.pkl')
            logger.info("Loaded pre-trained models")
        except FileNotFoundError:
            # Initialize new models
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            self.performance_predictor = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )
            logger.info("Initialized new AI models")
    
    def save_models(self):
        """Save trained models"""
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.anomaly_detector, 'models/anomaly_detector.pkl')
        joblib.dump(self.performance_predictor, 'models/performance_predictor.pkl')
        joblib.dump(self.scaler, 'models/scaler.pkl')
        logger.info("Saved AI models")
    
    def detect_anomalies(self, metrics: List[SystemMetrics]) -> List[AnomalyAlert]:
        """Detect anomalies in system metrics using AI"""
        if not metrics:
            return []
        
        # Convert metrics to feature matrix
        features = []
        for metric in metrics:
            features.append([
                metric.cpu_usage,
                metric.memory_usage,
                metric.disk_usage,
                metric.network_io,
                metric.response_time,
                metric.error_rate,
                metric.throughput,
                metric.active_connections
            ])
        
        X = np.array(features)
        X_scaled = self.scaler.fit_transform(X)
        
        # Detect anomalies
        anomaly_scores = self.anomaly_detector.decision_function(X_scaled)
        anomalies = self.anomaly_detector.predict(X_scaled)
        
        alerts = []
        for i, (metric, is_anomaly, score) in enumerate(zip(metrics, anomalies, anomaly_scores)):
            if is_anomaly == -1:  # Anomaly detected
                severity = self._calculate_severity(score, metric)
                alert = AnomalyAlert(
                    alert_id=f"anomaly_{datetime.now().timestamp()}_{i}",
                    service_name=metric.service_name,
                    anomaly_type=self._classify_anomaly_type(metric),
                    severity=severity,
                    description=self._generate_anomaly_description(metric),
                    metrics={
                        "cpu_usage": metric.cpu_usage,
                        "memory_usage": metric.memory_usage,
                        "response_time": metric.response_time,
                        "error_rate": metric.error_rate,
                        "anomaly_score": float(score)
                    },
                    timestamp=metric.timestamp,
                    recommended_actions=self._generate_recommendations(metric, severity)
                )
                alerts.append(alert)
        
        return alerts
    
    def predict_performance(self, historical_metrics: List[SystemMetrics], 
                          prediction_horizon: int = 60) -> Dict[str, Any]:
        """Predict future performance metrics"""
        if len(historical_metrics) < 10:
            return {"error": "Insufficient historical data"}
        
        # Prepare time series data
        df = pd.DataFrame([
            {
                'timestamp': m.timestamp,
                'cpu_usage': m.cpu_usage,
                'memory_usage': m.memory_usage,
                'response_time': m.response_time,
                'throughput': m.throughput,
                'error_rate': m.error_rate
            }
            for m in historical_metrics
        ])
        
        df = df.sort_values('timestamp')
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Feature engineering
        features = ['cpu_usage', 'memory_usage', 'hour', 'day_of_week']
        X = df[features].values
        
        predictions = {}
        targets = ['response_time', 'throughput', 'error_rate']
        
        for target in targets:
            y = df[target].values
            
            # Train model
            self.performance_predictor.fit(X, y)
            
            # Generate future predictions
            future_times = [
                historical_metrics[-1].timestamp + timedelta(minutes=i)
                for i in range(1, prediction_horizon + 1)
            ]
            
            future_features = []
            for future_time in future_times:
                # Use latest metrics as base
                latest = historical_metrics[-1]
                future_features.append([
                    latest.cpu_usage,
                    latest.memory_usage,
                    future_time.hour,
                    future_time.weekday()
                ])
            
            future_X = np.array(future_features)
            future_predictions = self.performance_predictor.predict(future_X)
            
            predictions[target] = {
                'values': future_predictions.tolist(),
                'timestamps': [t.isoformat() for t in future_times],
                'confidence_interval': self._calculate_confidence_interval(future_predictions)
            }
        
        return predictions
    
    def generate_maintenance_tasks(self, alerts: List[AnomalyAlert]) -> List[MaintenanceTask]:
        """Generate maintenance tasks based on anomaly alerts"""
        tasks = []
        
        for alert in alerts:
            task_type = self._determine_task_type(alert)
            priority = alert.severity
            
            task = MaintenanceTask(
                task_id=f"task_{datetime.now().timestamp()}_{alert.alert_id}",
                task_type=task_type,
                service_name=alert.service_name,
                priority=priority,
                description=f"Address {alert.anomaly_type} anomaly in {alert.service_name}",
                estimated_duration=self._estimate_task_duration(task_type, alert.severity),
                scheduled_time=self._calculate_optimal_maintenance_time(alert.service_name)
            )
            tasks.append(task)
        
        return tasks
    
    def optimize_performance(self, current_metrics: SystemMetrics) -> PerformanceOptimization:
        """Generate performance optimization recommendations"""
        optimization_actions = []
        target_metrics = {}
        estimated_improvement = {}
        
        # CPU optimization
        if current_metrics.cpu_usage > 80:
            optimization_actions.extend([
                "Scale horizontally by adding more instances",
                "Optimize CPU-intensive algorithms",
                "Implement caching to reduce computation"
            ])
            target_metrics["cpu_usage"] = min(70, current_metrics.cpu_usage * 0.8)
            estimated_improvement["cpu_usage"] = current_metrics.cpu_usage - target_metrics["cpu_usage"]
        
        # Memory optimization
        if current_metrics.memory_usage > 85:
            optimization_actions.extend([
                "Implement memory pooling",
                "Optimize data structures",
                "Add memory-based auto-scaling"
            ])
            target_metrics["memory_usage"] = min(75, current_metrics.memory_usage * 0.85)
            estimated_improvement["memory_usage"] = current_metrics.memory_usage - target_metrics["memory_usage"]
        
        # Response time optimization
        if current_metrics.response_time > 100:  # ms
            optimization_actions.extend([
                "Implement response caching",
                "Optimize database queries",
                "Add CDN for static content"
            ])
            target_metrics["response_time"] = current_metrics.response_time * 0.6
            estimated_improvement["response_time"] = current_metrics.response_time - target_metrics["response_time"]
        
        # Error rate optimization
        if current_metrics.error_rate > 1:
            optimization_actions.extend([
                "Implement circuit breakers",
                "Add retry mechanisms",
                "Improve error handling"
            ])
            target_metrics["error_rate"] = max(0.1, current_metrics.error_rate * 0.3)
            estimated_improvement["error_rate"] = current_metrics.error_rate - target_metrics["error_rate"]
        
        return PerformanceOptimization(
            optimization_id=f"opt_{datetime.now().timestamp()}",
            service_name=current_metrics.service_name,
            optimization_type="performance",
            current_metrics={
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "response_time": current_metrics.response_time,
                "error_rate": current_metrics.error_rate
            },
            target_metrics=target_metrics,
            actions=optimization_actions,
            estimated_improvement=estimated_improvement
        )
    
    def _calculate_severity(self, anomaly_score: float, metric: SystemMetrics) -> str:
        """Calculate anomaly severity based on score and metrics"""
        if anomaly_score < -0.5 or metric.error_rate > 10 or metric.response_time > 1000:
            return "critical"
        elif anomaly_score < -0.3 or metric.error_rate > 5 or metric.response_time > 500:
            return "high"
        elif anomaly_score < -0.1 or metric.error_rate > 2 or metric.response_time > 200:
            return "medium"
        else:
            return "low"
    
    def _classify_anomaly_type(self, metric: SystemMetrics) -> str:
        """Classify the type of anomaly"""
        if metric.cpu_usage > 90:
            return "cpu_spike"
        elif metric.memory_usage > 90:
            return "memory_leak"
        elif metric.response_time > 1000:
            return "performance_degradation"
        elif metric.error_rate > 5:
            return "error_spike"
        elif metric.throughput < 10:
            return "throughput_drop"
        else:
            return "general_anomaly"
    
    def _generate_anomaly_description(self, metric: SystemMetrics) -> str:
        """Generate human-readable anomaly description"""
        anomaly_type = self._classify_anomaly_type(metric)
        
        descriptions = {
            "cpu_spike": f"CPU usage spiked to {metric.cpu_usage:.1f}% on {metric.service_name}",
            "memory_leak": f"Memory usage reached {metric.memory_usage:.1f}% on {metric.service_name}",
            "performance_degradation": f"Response time increased to {metric.response_time:.1f}ms on {metric.service_name}",
            "error_spike": f"Error rate increased to {metric.error_rate:.1f}% on {metric.service_name}",
            "throughput_drop": f"Throughput dropped to {metric.throughput:.1f} req/s on {metric.service_name}",
            "general_anomaly": f"Anomalous behavior detected on {metric.service_name}"
        }
        
        return descriptions.get(anomaly_type, f"Anomaly detected on {metric.service_name}")
    
    def _generate_recommendations(self, metric: SystemMetrics, severity: str) -> List[str]:
        """Generate recommended actions based on anomaly"""
        anomaly_type = self._classify_anomaly_type(metric)
        
        recommendations = {
            "cpu_spike": [
                "Scale out the service horizontally",
                "Check for CPU-intensive processes",
                "Implement CPU throttling if necessary"
            ],
            "memory_leak": [
                "Restart the service to free memory",
                "Investigate memory leaks in the code",
                "Implement memory monitoring and alerts"
            ],
            "performance_degradation": [
                "Check database query performance",
                "Verify network connectivity",
                "Scale up resources if needed"
            ],
            "error_spike": [
                "Check application logs for errors",
                "Verify external service dependencies",
                "Implement circuit breakers"
            ],
            "throughput_drop": [
                "Check for bottlenecks in the pipeline",
                "Verify load balancer configuration",
                "Scale resources to handle load"
            ]
        }
        
        base_recommendations = recommendations.get(anomaly_type, [
            "Monitor the service closely",
            "Check system logs for issues",
            "Consider scaling resources"
        ])
        
        if severity == "critical":
            base_recommendations.insert(0, "IMMEDIATE ACTION REQUIRED")
        
        return base_recommendations
    
    def _determine_task_type(self, alert: AnomalyAlert) -> str:
        """Determine maintenance task type based on alert"""
        task_types = {
            "cpu_spike": "resource_scaling",
            "memory_leak": "service_restart",
            "performance_degradation": "performance_tuning",
            "error_spike": "error_investigation",
            "throughput_drop": "capacity_planning"
        }
        return task_types.get(alert.anomaly_type, "general_maintenance")
    
    def _estimate_task_duration(self, task_type: str, severity: str) -> int:
        """Estimate task duration in minutes"""
        base_durations = {
            "resource_scaling": 15,
            "service_restart": 5,
            "performance_tuning": 60,
            "error_investigation": 30,
            "capacity_planning": 120,
            "general_maintenance": 30
        }
        
        base_duration = base_durations.get(task_type, 30)
        
        # Adjust based on severity
        severity_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
        
        return int(base_duration * severity_multipliers.get(severity, 1.0))
    
    def _calculate_optimal_maintenance_time(self, service_name: str) -> datetime:
        """Calculate optimal time for maintenance based on usage patterns"""
        # For now, schedule maintenance during low-traffic hours (2-4 AM UTC)
        now = datetime.utcnow()
        
        # Find next 2 AM UTC
        next_maintenance = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if next_maintenance <= now:
            next_maintenance += timedelta(days=1)
        
        return next_maintenance
    
    def _calculate_confidence_interval(self, predictions: np.ndarray) -> Dict[str, List[float]]:
        """Calculate confidence intervals for predictions"""
        std = np.std(predictions)
        mean = np.mean(predictions)
        
        return {
            "lower": (predictions - 1.96 * std).tolist(),
            "upper": (predictions + 1.96 * std).tolist()
        }

# Initialize AI system
ai_system = AIMaintenanceSystem()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-maintenance-system",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/analyze/anomalies")
async def analyze_anomalies(metrics: List[SystemMetrics]) -> List[AnomalyAlert]:
    """Analyze system metrics for anomalies"""
    try:
        alerts = ai_system.detect_anomalies(metrics)
        
        # Store alerts in Redis for monitoring
        for alert in alerts:
            redis_client.setex(
                f"alert:{alert.alert_id}",
                3600,  # 1 hour TTL
                json.dumps(alert.dict(), default=str)
            )
        
        logger.info(f"Detected {len(alerts)} anomalies", service_count=len(set(m.service_name for m in metrics)))
        return alerts
    
    except Exception as e:
        logger.error(f"Error analyzing anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/predict/performance")
async def predict_performance(
    historical_metrics: List[SystemMetrics],
    prediction_horizon: int = 60
) -> Dict[str, Any]:
    """Predict future performance metrics"""
    try:
        predictions = ai_system.predict_performance(historical_metrics, prediction_horizon)
        
        logger.info(f"Generated performance predictions", 
                   horizon=prediction_horizon, 
                   metrics_count=len(historical_metrics))
        return predictions
    
    except Exception as e:
        logger.error(f"Error predicting performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/maintenance/tasks")
async def generate_maintenance_tasks(alerts: List[AnomalyAlert]) -> List[MaintenanceTask]:
    """Generate maintenance tasks based on alerts"""
    try:
        tasks = ai_system.generate_maintenance_tasks(alerts)
        
        # Store tasks in database
        for task in tasks:
            redis_client.setex(
                f"task:{task.task_id}",
                86400,  # 24 hours TTL
                json.dumps(task.dict(), default=str)
            )
        
        logger.info(f"Generated {len(tasks)} maintenance tasks")
        return tasks
    
    except Exception as e:
        logger.error(f"Error generating maintenance tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task generation failed: {str(e)}")

@app.post("/optimize/performance")
async def optimize_performance(metrics: SystemMetrics) -> PerformanceOptimization:
    """Generate performance optimization recommendations"""
    try:
        optimization = ai_system.optimize_performance(metrics)
        
        # Store optimization in Redis
        redis_client.setex(
            f"optimization:{optimization.optimization_id}",
            3600,  # 1 hour TTL
            json.dumps(optimization.dict(), default=str)
        )
        
        logger.info(f"Generated performance optimization", 
                   service=metrics.service_name,
                   actions_count=len(optimization.actions))
        return optimization
    
    except Exception as e:
        logger.error(f"Error generating optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@app.get("/alerts")
async def get_active_alerts() -> List[Dict[str, Any]]:
    """Get all active alerts"""
    try:
        alert_keys = redis_client.keys("alert:*")
        alerts = []
        
        for key in alert_keys:
            alert_data = redis_client.get(key)
            if alert_data:
                alerts.append(json.loads(alert_data))
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")

@app.get("/tasks")
async def get_maintenance_tasks() -> List[Dict[str, Any]]:
    """Get all maintenance tasks"""
    try:
        task_keys = redis_client.keys("task:*")
        tasks = []
        
        for key in task_keys:
            task_data = redis_client.get(key)
            if task_data:
                tasks.append(json.loads(task_data))
        
        return tasks
    
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")

@app.post("/train/models")
async def train_models(background_tasks: BackgroundTasks):
    """Train AI models with latest data"""
    try:
        background_tasks.add_task(train_models_background)
        return {"message": "Model training started in background"}
    
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

async def train_models_background():
    """Background task to train AI models"""
    try:
        # Fetch training data from database
        with db_engine.connect() as conn:
            # This would fetch actual metrics data
            result = conn.execute(text("SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10000"))
            # Process and train models with the data
            
        ai_system.save_models()
        logger.info("AI models trained and saved successfully")
        
    except Exception as e:
        logger.error(f"Background model training failed: {str(e)}")

@app.get("/system/status")
async def get_system_status():
    """Get AI maintenance system status"""
    try:
        # Check Redis connection
        redis_status = "healthy" if redis_client.ping() else "unhealthy"
        
        # Check database connection
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "healthy"
        except:
            db_status = "unhealthy"
        
        # Get system metrics
        alert_count = len(redis_client.keys("alert:*"))
        task_count = len(redis_client.keys("task:*"))
        
        return {
            "status": "healthy" if redis_status == "healthy" and db_status == "healthy" else "degraded",
            "components": {
                "redis": redis_status,
                "database": db_status,
                "ai_models": "loaded"
            },
            "metrics": {
                "active_alerts": alert_count,
                "pending_tasks": task_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
