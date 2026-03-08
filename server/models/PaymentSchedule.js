const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const PaymentSchedule = sequelize.define('PaymentSchedule', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    investorId: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    projectId: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    installmentNo: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    amount: {
        type: DataTypes.DECIMAL(15, 2),
        allowNull: false,
    },
    dueDate: {
        type: DataTypes.DATEONLY,
        allowNull: false,
    },
    paidDate: {
        type: DataTypes.DATEONLY,
        allowNull: true,
    },
    paidAmount: {
        type: DataTypes.DECIMAL(15, 2),
        defaultValue: 0,
    },
    status: {
        type: DataTypes.ENUM('pending', 'paid', 'overdue', 'partial'),
        defaultValue: 'pending',
    },
    reminderSent: {
        type: DataTypes.BOOLEAN,
        defaultValue: false,
    },
    notes: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
}, {
    tableName: 'payment_schedules',
});

module.exports = PaymentSchedule;
