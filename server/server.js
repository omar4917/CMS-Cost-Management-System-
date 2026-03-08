const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { sequelize } = require('./models');

const app = express();

// Security
app.use(helmet({ contentSecurityPolicy: false, crossOriginEmbedderPolicy: false }));
app.use(cors({
    origin: process.env.NODE_ENV === 'production' ? false : '*',
    credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 1000,
    message: { message: 'Too many requests. Please try again later.' },
});
app.use('/api/', limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Static files (uploads)
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// ==================== API ROUTES ====================
app.use('/api/auth', require('./routes/auth'));
app.use('/api/dashboard', require('./routes/dashboard'));
app.use('/api/projects', require('./routes/projects'));
app.use('/api/cost-categories', require('./routes/costCategories'));
app.use('/api/investors', require('./routes/investors'));
app.use('/api/investor-types', require('./routes/investorTypes'));
app.use('/api/investments', require('./routes/investments'));
app.use('/api/payment-schedules', require('./routes/paymentSchedules'));
app.use('/api/contractors', require('./routes/contractors'));
app.use('/api/currencies', require('./routes/currencies'));
app.use('/api/documents', require('./routes/documents'));
app.use('/api/emails', require('./routes/emails'));
app.use('/api/audit-logs', require('./routes/auditLogs'));
app.use('/api/notes', require('./routes/notes'));
app.use('/api/settings', require('./routes/settings'));
app.use('/api/reports', require('./routes/reports'));
app.use('/api/backup', require('./routes/backup'));
app.use('/api/investor-portal', require('./routes/investorPortal'));

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Serve React app in production
if (process.env.NODE_ENV === 'production') {
    app.use(express.static(path.join(__dirname, '../client/dist')));
    app.get('*', (req, res) => {
        res.sendFile(path.join(__dirname, '../client/dist/index.html'));
    });
}

// Error handling middleware (must be last)
app.use(require('./middleware/errorHandler'));

const PORT = process.env.PORT || 5000;

// Sync database and start server
sequelize.sync({ alter: process.env.NODE_ENV === 'development' })
    .then(() => {
        console.log('✅ Database synced successfully');
        app.listen(PORT, '0.0.0.0', () => {
            console.log(`\n🚀 CMS Server running on port ${PORT}`);
            console.log(`📡 Local:   http://localhost:${PORT}`);
            console.log(`📡 Network: http://0.0.0.0:${PORT}`);
            console.log(`\n💡 API Health: http://localhost:${PORT}/api/health`);

            // Start email automation cron
            try {
                const { startEmailCron } = require('./services/emailCron');
                startEmailCron();
            } catch (e) {
                console.warn('⚠️  Email cron not started:', e.message);
            }
        });
    })
    .catch(err => {
        console.error('❌ Database connection failed:', err.message);
        console.error('💡 Make sure MySQL is running and the database "cms_db" exists.');
        process.exit(1);
    });

module.exports = app;
