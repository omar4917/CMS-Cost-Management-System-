const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const ContractorPayment = sequelize.define('ContractorPayment', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    contractorId: {
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
    description: {
        type: DataTypes.STRING(500),
        allowNull: true,
    },
    invoiceNo: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    status: {
        type: DataTypes.ENUM('pending', 'approved', 'paid'),
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
}, {
    tableName: 'contractor_payments',
});

module.exports = ContractorPayment;
