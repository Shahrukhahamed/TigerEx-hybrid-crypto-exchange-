/**
 * TigerEx Notification Service
 * Advanced Node.js microservice for real-time notifications, alerts, and communication
 * Supports push notifications, email, SMS, WebSocket, and in-app notifications
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const compression = require('compression');
const morgan = require('morgan');
const winston = require('winston');
const Redis = require('ioredis');
const { Kafka } = require('kafkajs');
const nodemailer = require('nodemailer');
const twilio = require('twilio');
const webpush = require('web-push');
const admin = require('firebase-admin');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { Pool } = require('pg');
const mongoose = require('mongoose');
const Bull = require('bull');
const cron = require('node-cron');
const WebSocket = require('ws');
const EventEmitter = require('events');

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
        methods: ['GET', 'POST'],
        credentials: true
    }
});

// Configuration
const config = {
    port: process.env.PORT || 3001,
    redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379,
        password: process.env.REDIS_PASSWORD
    },
    kafka: {
        brokers: process.env.KAFKA_BROKERS?.split(',') || ['localhost:9092'],
        clientId: 'notification-service'
    },
    database: {
        postgres: process.env.DATABASE_URL || 'postgresql://postgres:password@localhost:5432/tigerex',
        mongodb: process.env.MONGODB_URL || 'mongodb://localhost:27017/tigerex'
    },
    email: {
        host: process.env.SMTP_HOST || 'smtp.gmail.com',
        port: process.env.SMTP_PORT || 587,
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
    },
    sms: {
        accountSid: process.env.TWILIO_ACCOUNT_SID,
        authToken: process.env.TWILIO_AUTH_TOKEN,
        fromNumber: process.env.TWILIO_FROM_NUMBER
    },
    push: {
        vapidPublicKey: process.env.VAPID_PUBLIC_KEY,
        vapidPrivateKey: process.env.VAPID_PRIVATE_KEY,
        vapidEmail: process.env.VAPID_EMAIL
    },
    firebase: {
        projectId: process.env.FIREBASE_PROJECT_ID,
        privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
        clientEmail: process.env.FIREBASE_CLIENT_EMAIL
    },
    jwt: {
        secret: process.env.JWT_SECRET || 'your-secret-key',
        expiresIn: '24h'
    }
};

// Logger setup
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'notification-service' },
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// Redis client
const redis = new Redis(config.redis);

// PostgreSQL client
const pgPool = new Pool({
    connectionString: config.database.postgres,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

// MongoDB connection
mongoose.connect(config.database.mongodb, {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// Kafka setup
const kafka = new Kafka(config.kafka);
const producer = kafka.producer();
const consumer = kafka.consumer({ groupId: 'notification-group' });

// Email transporter
const emailTransporter = nodemailer.createTransporter({
    host: config.email.host,
    port: config.email.port,
    secure: false,
    auth: {
        user: config.email.user,
        pass: config.email.pass
    }
});

// SMS client
const smsClient = twilio(config.sms.accountSid, config.sms.authToken);

// Web Push setup
webpush.setVapidDetails(
    `mailto:${config.push.vapidEmail}`,
    config.push.vapidPublicKey,
    config.push.vapidPrivateKey
);

// Firebase Admin setup
if (config.firebase.projectId) {
    admin.initializeApp({
        credential: admin.credential.cert({
            projectId: config.firebase.projectId,
            privateKey: config.firebase.privateKey,
            clientEmail: config.firebase.clientEmail
        })
    });
}

// Bull queues for background jobs
const emailQueue = new Bull('email queue', { redis: config.redis });
const smsQueue = new Bull('sms queue', { redis: config.redis });
const pushQueue = new Bull('push queue', { redis: config.redis });
const alertQueue = new Bull('alert queue', { redis: config.redis });

// Middleware
app.use(helmet());
app.use(compression());
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// MongoDB Schemas
const NotificationSchema = new mongoose.Schema({
    userId: { type: String, required: true, index: true },
    type: { type: String, required: true, enum: ['email', 'sms', 'push', 'in-app', 'websocket'] },
    channel: { type: String, required: true },
    title: { type: String, required: true },
    message: { type: String, required: true },
    data: { type: Object, default: {} },
    status: { type: String, default: 'pending', enum: ['pending', 'sent', 'delivered', 'failed', 'read'] },
    priority: { type: String, default: 'normal', enum: ['low', 'normal', 'high', 'urgent'] },
    scheduledAt: { type: Date },
    sentAt: { type: Date },
    readAt: { type: Date },
    metadata: { type: Object, default: {} },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
});

const AlertRuleSchema = new mongoose.Schema({
    userId: { type: String, required: true, index: true },
    name: { type: String, required: true },
    type: { type: String, required: true, enum: ['price', 'volume', 'pnl', 'balance', 'order', 'position'] },
    symbol: { type: String },
    condition: {
        operator: { type: String, required: true, enum: ['>', '<', '>=', '<=', '==', '!='] },
        value: { type: Number, required: true }
    },
    channels: [{ type: String, enum: ['email', 'sms', 'push', 'in-app'] }],
    isActive: { type: Boolean, default: true },
    triggeredCount: { type: Number, default: 0 },
    lastTriggered: { type: Date },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
});

const SubscriptionSchema = new mongoose.Schema({
    userId: { type: String, required: true, index: true },
    type: { type: String, required: true, enum: ['web-push', 'fcm'] },
    endpoint: { type: String, required: true },
    keys: {
        p256dh: { type: String },
        auth: { type: String }
    },
    token: { type: String }, // FCM token
    isActive: { type: Boolean, default: true },
    createdAt: { type: Date, default: Date.now }
});

const Notification = mongoose.model('Notification', NotificationSchema);
const AlertRule = mongoose.model('AlertRule', AlertRuleSchema);
const Subscription = mongoose.model('Subscription', SubscriptionSchema);

// Notification Service Class
class NotificationService extends EventEmitter {
    constructor() {
        super();
        this.connectedUsers = new Map();
        this.setupKafkaConsumer();
        this.setupQueueProcessors();
        this.setupCronJobs();
    }

    async setupKafkaConsumer() {
        await consumer.connect();
        await consumer.subscribe({ 
            topics: [
                'user-events',
                'trading-events', 
                'price-alerts',
                'order-updates',
                'balance-updates',
                'security-alerts'
            ] 
        });

        await consumer.run({
            eachMessage: async ({ topic, partition, message }) => {
                try {
                    const data = JSON.parse(message.value.toString());
                    await this.handleKafkaMessage(topic, data);
                } catch (error) {
                    logger.error('Error processing Kafka message:', error);
                }
            }
        });
    }

    async handleKafkaMessage(topic, data) {
        switch (topic) {
            case 'user-events':
                await this.handleUserEvent(data);
                break;
            case 'trading-events':
                await this.handleTradingEvent(data);
                break;
            case 'price-alerts':
                await this.handlePriceAlert(data);
                break;
            case 'order-updates':
                await this.handleOrderUpdate(data);
                break;
            case 'balance-updates':
                await this.handleBalanceUpdate(data);
                break;
            case 'security-alerts':
                await this.handleSecurityAlert(data);
                break;
        }
    }

    async handleUserEvent(data) {
        const { userId, event, details } = data;
        
        switch (event) {
            case 'login':
                await this.sendNotification({
                    userId,
                    type: 'in-app',
                    title: 'Login Detected',
                    message: `Login from ${details.location} at ${new Date().toLocaleString()}`,
                    priority: 'normal'
                });
                break;
            case 'suspicious_activity':
                await this.sendNotification({
                    userId,
                    type: 'email',
                    title: 'Security Alert',
                    message: 'Suspicious activity detected on your account. Please review your recent activity.',
                    priority: 'urgent'
                });
                break;
            case 'kyc_approved':
                await this.sendNotification({
                    userId,
                    type: 'email',
                    title: 'KYC Verification Approved',
                    message: 'Your identity verification has been approved. You can now access all trading features.',
                    priority: 'high'
                });
                break;
        }
    }

    async handleTradingEvent(data) {
        const { userId, event, details } = data;
        
        switch (event) {
            case 'order_filled':
                await this.sendNotification({
                    userId,
                    type: 'push',
                    title: 'Order Filled',
                    message: `Your ${details.side} order for ${details.quantity} ${details.symbol} has been filled at $${details.price}`,
                    data: details,
                    priority: 'high'
                });
                break;
            case 'position_liquidated':
                await this.sendNotification({
                    userId,
                    type: 'push',
                    title: 'Position Liquidated',
                    message: `Your ${details.side} position in ${details.symbol} has been liquidated`,
                    data: details,
                    priority: 'urgent'
                });
                break;
            case 'margin_call':
                await this.sendNotification({
                    userId,
                    type: 'sms',
                    title: 'Margin Call',
                    message: `Margin call: Please add funds to avoid liquidation. Current margin ratio: ${details.marginRatio}%`,
                    priority: 'urgent'
                });
                break;
        }
    }

    async handlePriceAlert(data) {
        const { userId, symbol, price, condition, alertId } = data;
        
        await this.sendNotification({
            userId,
            type: 'push',
            title: 'Price Alert',
            message: `${symbol} has ${condition} $${price}`,
            data: { symbol, price, alertId },
            priority: 'normal'
        });

        // Update alert rule
        await AlertRule.findByIdAndUpdate(alertId, {
            triggeredCount: { $inc: 1 },
            lastTriggered: new Date()
        });
    }

    async handleOrderUpdate(data) {
        const { userId, orderId, status, details } = data;
        
        if (status === 'FILLED' || status === 'PARTIALLY_FILLED' || status === 'CANCELED') {
            await this.sendNotification({
                userId,
                type: 'websocket',
                title: 'Order Update',
                message: `Order ${orderId} status: ${status}`,
                data: details,
                priority: 'normal'
            });
        }
    }

    async handleBalanceUpdate(data) {
        const { userId, asset, change, newBalance } = data;
        
        if (Math.abs(change) > 1000) { // Significant balance change
            await this.sendNotification({
                userId,
                type: 'in-app',
                title: 'Balance Update',
                message: `Your ${asset} balance has changed by ${change > 0 ? '+' : ''}${change}. New balance: ${newBalance}`,
                priority: 'normal'
            });
        }
    }

    async handleSecurityAlert(data) {
        const { userId, alertType, details } = data;
        
        await this.sendNotification({
            userId,
            type: 'email',
            title: 'Security Alert',
            message: `Security alert: ${alertType}. ${details.message}`,
            data: details,
            priority: 'urgent'
        });
    }

    async sendNotification(notificationData) {
        try {
            // Save notification to database
            const notification = new Notification(notificationData);
            await notification.save();

            // Add to appropriate queue based on type
            switch (notificationData.type) {
                case 'email':
                    await emailQueue.add('send-email', { notificationId: notification._id });
                    break;
                case 'sms':
                    await smsQueue.add('send-sms', { notificationId: notification._id });
                    break;
                case 'push':
                    await pushQueue.add('send-push', { notificationId: notification._id });
                    break;
                case 'in-app':
                case 'websocket':
                    await this.sendRealTimeNotification(notificationData);
                    break;
            }

            this.emit('notification-sent', notification);
            return notification;
        } catch (error) {
            logger.error('Error sending notification:', error);
            throw error;
        }
    }

    async sendRealTimeNotification(notificationData) {
        const { userId } = notificationData;
        
        // Send via WebSocket if user is connected
        if (this.connectedUsers.has(userId)) {
            const socket = this.connectedUsers.get(userId);
            socket.emit('notification', notificationData);
        }

        // Store in Redis for when user comes online
        await redis.lpush(`notifications:${userId}`, JSON.stringify(notificationData));
        await redis.expire(`notifications:${userId}`, 86400); // 24 hours
    }

    setupQueueProcessors() {
        // Email queue processor
        emailQueue.process('send-email', async (job) => {
            const { notificationId } = job.data;
            const notification = await Notification.findById(notificationId);
            
            if (!notification) return;

            try {
                // Get user email from database
                const userResult = await pgPool.query('SELECT email FROM users WHERE id = $1', [notification.userId]);
                if (userResult.rows.length === 0) return;

                const userEmail = userResult.rows[0].email;

                await emailTransporter.sendMail({
                    from: config.email.user,
                    to: userEmail,
                    subject: notification.title,
                    html: this.generateEmailTemplate(notification)
                });

                await Notification.findByIdAndUpdate(notificationId, {
                    status: 'sent',
                    sentAt: new Date()
                });

                logger.info(`Email sent to ${userEmail} for notification ${notificationId}`);
            } catch (error) {
                await Notification.findByIdAndUpdate(notificationId, { status: 'failed' });
                logger.error('Error sending email:', error);
                throw error;
            }
        });

        // SMS queue processor
        smsQueue.process('send-sms', async (job) => {
            const { notificationId } = job.data;
            const notification = await Notification.findById(notificationId);
            
            if (!notification) return;

            try {
                // Get user phone from database
                const userResult = await pgPool.query('SELECT phone FROM users WHERE id = $1', [notification.userId]);
                if (userResult.rows.length === 0 || !userResult.rows[0].phone) return;

                const userPhone = userResult.rows[0].phone;

                await smsClient.messages.create({
                    body: `${notification.title}: ${notification.message}`,
                    from: config.sms.fromNumber,
                    to: userPhone
                });

                await Notification.findByIdAndUpdate(notificationId, {
                    status: 'sent',
                    sentAt: new Date()
                });

                logger.info(`SMS sent to ${userPhone} for notification ${notificationId}`);
            } catch (error) {
                await Notification.findByIdAndUpdate(notificationId, { status: 'failed' });
                logger.error('Error sending SMS:', error);
                throw error;
            }
        });

        // Push notification queue processor
        pushQueue.process('send-push', async (job) => {
            const { notificationId } = job.data;
            const notification = await Notification.findById(notificationId);
            
            if (!notification) return;

            try {
                // Get user subscriptions
                const subscriptions = await Subscription.find({ 
                    userId: notification.userId, 
                    isActive: true 
                });

                const pushPromises = subscriptions.map(async (subscription) => {
                    try {
                        if (subscription.type === 'web-push') {
                            await webpush.sendNotification(
                                {
                                    endpoint: subscription.endpoint,
                                    keys: subscription.keys
                                },
                                JSON.stringify({
                                    title: notification.title,
                                    body: notification.message,
                                    data: notification.data,
                                    icon: '/icon-192x192.png',
                                    badge: '/badge-72x72.png'
                                })
                            );
                        } else if (subscription.type === 'fcm' && subscription.token) {
                            await admin.messaging().send({
                                token: subscription.token,
                                notification: {
                                    title: notification.title,
                                    body: notification.message
                                },
                                data: notification.data
                            });
                        }
                    } catch (error) {
                        if (error.statusCode === 410) {
                            // Subscription expired, remove it
                            await Subscription.findByIdAndUpdate(subscription._id, { isActive: false });
                        }
                        logger.error('Error sending push notification:', error);
                    }
                });

                await Promise.allSettled(pushPromises);

                await Notification.findByIdAndUpdate(notificationId, {
                    status: 'sent',
                    sentAt: new Date()
                });

                logger.info(`Push notifications sent for notification ${notificationId}`);
            } catch (error) {
                await Notification.findByIdAndUpdate(notificationId, { status: 'failed' });
                logger.error('Error sending push notifications:', error);
                throw error;
            }
        });
    }

    setupCronJobs() {
        // Check for scheduled notifications every minute
        cron.schedule('* * * * *', async () => {
            try {
                const scheduledNotifications = await Notification.find({
                    status: 'pending',
                    scheduledAt: { $lte: new Date() }
                });

                for (const notification of scheduledNotifications) {
                    await this.sendNotification(notification.toObject());
                }
            } catch (error) {
                logger.error('Error processing scheduled notifications:', error);
            }
        });

        // Clean up old notifications every day at midnight
        cron.schedule('0 0 * * *', async () => {
            try {
                const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
                await Notification.deleteMany({ createdAt: { $lt: thirtyDaysAgo } });
                logger.info('Cleaned up old notifications');
            } catch (error) {
                logger.error('Error cleaning up notifications:', error);
            }
        });
    }

    generateEmailTemplate(notification) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>${notification.title}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
                    .header { background-color: #ff6b35; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                    .content { padding: 20px; }
                    .footer { background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>TigerEx</h1>
                    </div>
                    <div class="content">
                        <h2>${notification.title}</h2>
                        <p>${notification.message}</p>
                        ${notification.data ? `<pre>${JSON.stringify(notification.data, null, 2)}</pre>` : ''}
                    </div>
                    <div class="footer">
                        <p>© 2024 TigerEx. All rights reserved.</p>
                        <p><a href="https://tigerex.com/unsubscribe">Unsubscribe</a></p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }
}

// Initialize notification service
const notificationService = new NotificationService();

// Authentication middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'Access token required' });
    }

    jwt.verify(token, config.jwt.secret, (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid token' });
        }
        req.user = user;
        next();
    });
};

// Socket.IO connection handling
io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    if (!token) {
        return next(new Error('Authentication error'));
    }

    jwt.verify(token, config.jwt.secret, (err, user) => {
        if (err) {
            return next(new Error('Authentication error'));
        }
        socket.user = user;
        next();
    });
});

io.on('connection', (socket) => {
    const userId = socket.user.id;
    notificationService.connectedUsers.set(userId, socket);
    
    logger.info(`User ${userId} connected via WebSocket`);

    // Send pending notifications
    redis.lrange(`notifications:${userId}`, 0, -1).then(notifications => {
        notifications.forEach(notification => {
            socket.emit('notification', JSON.parse(notification));
        });
        redis.del(`notifications:${userId}`);
    });

    socket.on('mark-read', async (notificationId) => {
        try {
            await Notification.findByIdAndUpdate(notificationId, {
                status: 'read',
                readAt: new Date()
            });
        } catch (error) {
            logger.error('Error marking notification as read:', error);
        }
    });

    socket.on('disconnect', () => {
        notificationService.connectedUsers.delete(userId);
        logger.info(`User ${userId} disconnected from WebSocket`);
    });
});

// API Routes

// Get user notifications
app.get('/api/notifications', authenticateToken, async (req, res) => {
    try {
        const { page = 1, limit = 20, status, type } = req.query;
        const userId = req.user.id;

        const filter = { userId };
        if (status) filter.status = status;
        if (type) filter.type = type;

        const notifications = await Notification.find(filter)
            .sort({ createdAt: -1 })
            .limit(limit * 1)
            .skip((page - 1) * limit);

        const total = await Notification.countDocuments(filter);

        res.json({
            notifications,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                total,
                pages: Math.ceil(total / limit)
            }
        });
    } catch (error) {
        logger.error('Error fetching notifications:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Mark notification as read
app.patch('/api/notifications/:id/read', authenticateToken, async (req, res) => {
    try {
        const notificationId = req.params.id;
        const userId = req.user.id;

        const notification = await Notification.findOneAndUpdate(
            { _id: notificationId, userId },
            { status: 'read', readAt: new Date() },
            { new: true }
        );

        if (!notification) {
            return res.status(404).json({ error: 'Notification not found' });
        }

        res.json(notification);
    } catch (error) {
        logger.error('Error marking notification as read:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Send custom notification
app.post('/api/notifications/send', authenticateToken, async (req, res) => {
    try {
        const { userId, type, title, message, data, priority, scheduledAt } = req.body;
        
        // Only admins can send notifications to other users
        if (userId !== req.user.id && req.user.role !== 'admin') {
            return res.status(403).json({ error: 'Insufficient permissions' });
        }

        const notification = await notificationService.sendNotification({
            userId: userId || req.user.id,
            type,
            title,
            message,
            data,
            priority,
            scheduledAt: scheduledAt ? new Date(scheduledAt) : undefined
        });

        res.json(notification);
    } catch (error) {
        logger.error('Error sending notification:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Create alert rule
app.post('/api/alerts', authenticateToken, async (req, res) => {
    try {
        const { name, type, symbol, condition, channels } = req.body;
        const userId = req.user.id;

        const alertRule = new AlertRule({
            userId,
            name,
            type,
            symbol,
            condition,
            channels
        });

        await alertRule.save();
        res.json(alertRule);
    } catch (error) {
        logger.error('Error creating alert rule:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get user alert rules
app.get('/api/alerts', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.id;
        const alertRules = await AlertRule.find({ userId }).sort({ createdAt: -1 });
        res.json(alertRules);
    } catch (error) {
        logger.error('Error fetching alert rules:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Update alert rule
app.patch('/api/alerts/:id', authenticateToken, async (req, res) => {
    try {
        const alertId = req.params.id;
        const userId = req.user.id;
        const updates = req.body;

        const alertRule = await AlertRule.findOneAndUpdate(
            { _id: alertId, userId },
            { ...updates, updatedAt: new Date() },
            { new: true }
        );

        if (!alertRule) {
            return res.status(404).json({ error: 'Alert rule not found' });
        }

        res.json(alertRule);
    } catch (error) {
        logger.error('Error updating alert rule:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Delete alert rule
app.delete('/api/alerts/:id', authenticateToken, async (req, res) => {
    try {
        const alertId = req.params.id;
        const userId = req.user.id;

        const alertRule = await AlertRule.findOneAndDelete({ _id: alertId, userId });

        if (!alertRule) {
            return res.status(404).json({ error: 'Alert rule not found' });
        }

        res.json({ message: 'Alert rule deleted successfully' });
    } catch (error) {
        logger.error('Error deleting alert rule:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Subscribe to push notifications
app.post('/api/push/subscribe', authenticateToken, async (req, res) => {
    try {
        const { endpoint, keys, token, type } = req.body;
        const userId = req.user.id;

        // Remove existing subscription for this user and endpoint
        await Subscription.deleteMany({ userId, endpoint });

        const subscription = new Subscription({
            userId,
            type,
            endpoint,
            keys,
            token
        });

        await subscription.save();
        res.json({ message: 'Subscription saved successfully' });
    } catch (error) {
        logger.error('Error saving push subscription:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Unsubscribe from push notifications
app.post('/api/push/unsubscribe', authenticateToken, async (req, res) => {
    try {
        const { endpoint } = req.body;
        const userId = req.user.id;

        await Subscription.findOneAndUpdate(
            { userId, endpoint },
            { isActive: false }
        );

        res.json({ message: 'Unsubscribed successfully' });
    } catch (error) {
        logger.error('Error unsubscribing:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        connections: notificationService.connectedUsers.size
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    logger.error('Unhandled error:', error);
    res.status(500).json({ error: 'Internal server error' });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    logger.info('SIGTERM received, shutting down gracefully');
    
    server.close(() => {
        logger.info('HTTP server closed');
    });
    
    await consumer.disconnect();
    await producer.disconnect();
    await redis.disconnect();
    await pgPool.end();
    await mongoose.connection.close();
    
    process.exit(0);
});

// Start server
const startServer = async () => {
    try {
        await producer.connect();
        logger.info('Kafka producer connected');
        
        server.listen(config.port, () => {
            logger.info(`TigerEx Notification Service running on port ${config.port}`);
        });
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
};

startServer();