const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Investment = sequelize.define('Investment', {
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
    amount: {
        type: DataTypes.DECIMAL(15, 2),
        allowNull: false,
    },
    currency: {
        type: DataTypes.STRING(10),
        defaultValue: 'BDT',
    },
    date: {
        type: DataTypes.DATEONLY,
        allowNull: false,
    },
    paymentMethod: {
        type: DataTypes.ENUM('cash', 'bank_transfer', 'cheque', 'online', 'other'),
        defaultValue: 'bank_transfer',
    },
    referenceNo: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    notes: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    status: {
        type: DataTypes.ENUM('pending', 'confirmed', 'cancelled'),
        defaultValue: 'confirmed',
    },
    createdBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
}, {
    tableName: 'investments',
});

module.exports = Investment;
