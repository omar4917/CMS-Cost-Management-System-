const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const EmailLog = sequelize.define('EmailLog', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    templateId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    recipients: {
        type: DataTypes.TEXT,
        allowNull: false,
        get() {
            const val = this.getDataValue('recipients');
            return val ? JSON.parse(val) : [];
        },
        set(val) {
            this.setDataValue('recipients', JSON.stringify(val));
        },
    },
    subject: {
        type: DataTypes.STRING(500),
        allowNull: false,
    },
    body: {
        type: DataTypes.TEXT('long'),
        allowNull: true,
    },
    status: {
        type: DataTypes.ENUM('pending', 'sent', 'failed'),
        defaultValue: 'pending',
    },
    sentAt: {
        type: DataTypes.DATE,
        allowNull: true,
    },
    error: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    sentBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    triggerType: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
}, {
    tableName: 'email_logs',
});

module.exports = EmailLog;
