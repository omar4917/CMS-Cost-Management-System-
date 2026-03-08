const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const CostItem = sequelize.define('CostItem', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(300),
        allowNull: false,
    },
    projectId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    categoryId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    description: {
        type: DataTypes.STRING(500),
        allowNull: true,
    },
    quantity: {
        type: DataTypes.DECIMAL(15, 2),
        defaultValue: 0,
    },
    unit: {
        type: DataTypes.STRING(50),
        defaultValue: 'pcs',
    },
    unitPrice: {
        type: DataTypes.DECIMAL(15, 2),
        defaultValue: 0,
    },
    estimatedAmount: {
        type: DataTypes.DECIMAL(15, 2),
        defaultValue: 0,
    },
    actualAmount: {
        type: DataTypes.DECIMAL(15, 2),
        defaultValue: 0,
    },
    currency: {
        type: DataTypes.STRING(10),
        defaultValue: 'BDT',
    },
    date: {
        type: DataTypes.DATEONLY,
        allowNull: true,
    },
    vendor: {
        type: DataTypes.STRING(200),
        allowNull: true,
    },
    invoiceNo: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    status: {
        type: DataTypes.ENUM('pending', 'approved', 'purchased', 'delivered', 'paid', 'rejected', 'cancelled'),
        defaultValue: 'pending',
    },
    notes: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    createdBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    approvedBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
}, {
    tableName: 'cost_items',
});

module.exports = CostItem;
