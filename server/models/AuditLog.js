const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const AuditLog = sequelize.define('AuditLog', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    userId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    action: {
        type: DataTypes.ENUM('create', 'update', 'delete', 'login', 'logout', 'export', 'email_sent', 'backup'),
        allowNull: false,
    },
    entityType: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
    entityId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    description: {
        type: DataTypes.STRING(500),
        allowNull: true,
    },
    oldValues: {
        type: DataTypes.TEXT('long'),
        allowNull: true,
        get() {
            const val = this.getDataValue('oldValues');
            return val ? JSON.parse(val) : null;
        },
        set(val) {
            this.setDataValue('oldValues', val ? JSON.stringify(val) : null);
        },
    },
    newValues: {
        type: DataTypes.TEXT('long'),
        allowNull: true,
        get() {
            const val = this.getDataValue('newValues');
            return val ? JSON.parse(val) : null;
        },
        set(val) {
            this.setDataValue('newValues', val ? JSON.stringify(val) : null);
        },
    },
    ipAddress: {
        type: DataTypes.STRING(45),
        allowNull: true,
    },
}, {
    tableName: 'audit_logs',
    updatedAt: false,
});

module.exports = AuditLog;
