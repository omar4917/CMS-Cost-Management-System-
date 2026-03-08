const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const EmailTemplate = sequelize.define('EmailTemplate', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(200),
        allowNull: false,
    },
    subject: {
        type: DataTypes.STRING(500),
        allowNull: false,
    },
    bodyHtml: {
        type: DataTypes.TEXT('long'),
        allowNull: false,
    },
    triggerType: {
        type: DataTypes.ENUM(
            'manual',
            'investment_received',
            'milestone_reached',
            'payment_reminder',
            'payment_overdue',
            'plan_changed',
            'cost_increased',
            'cost_decreased',
            'project_completed',
            'investor_welcome',
            'progress_update'
        ),
        defaultValue: 'manual',
    },
    variables: {
        type: DataTypes.TEXT,
        allowNull: true,
        get() {
            const val = this.getDataValue('variables');
            return val ? JSON.parse(val) : [];
        },
        set(val) {
            this.setDataValue('variables', JSON.stringify(val));
        },
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        defaultValue: true,
    },
}, {
    tableName: 'email_templates',
});

module.exports = EmailTemplate;
