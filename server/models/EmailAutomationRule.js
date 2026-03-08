const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const EmailAutomationRule = sequelize.define('EmailAutomationRule', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(200),
        allowNull: false,
    },
    triggerEvent: {
        type: DataTypes.ENUM(
            'investment_received',
            'milestone_reached',
            'payment_due_reminder',
            'payment_overdue',
            'plan_changed',
            'cost_increased',
            'cost_decreased',
            'project_completed',
            'progress_update'
        ),
        allowNull: false,
    },
    templateId: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    recipientFilter: {
        type: DataTypes.TEXT,
        allowNull: true,
        get() {
            const val = this.getDataValue('recipientFilter');
            return val ? JSON.parse(val) : {};
        },
        set(val) {
            this.setDataValue('recipientFilter', JSON.stringify(val));
        },
    },
    conditions: {
        type: DataTypes.TEXT,
        allowNull: true,
        get() {
            const val = this.getDataValue('conditions');
            return val ? JSON.parse(val) : {};
        },
        set(val) {
            this.setDataValue('conditions', JSON.stringify(val));
        },
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        defaultValue: true,
    },
}, {
    tableName: 'email_automation_rules',
});

module.exports = EmailAutomationRule;
