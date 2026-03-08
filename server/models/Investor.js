const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Investor = sequelize.define('Investor', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(200),
        allowNull: false,
    },
    email: {
        type: DataTypes.STRING(100),
        allowNull: true,
        validate: { isEmail: true },
    },
    phone: {
        type: DataTypes.STRING(30),
        allowNull: true,
    },
    address: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    typeId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    company: {
        type: DataTypes.STRING(200),
        allowNull: true,
    },
    nationalId: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
    bankAccount: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    bankName: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        defaultValue: true,
    },
    notes: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
}, {
    tableName: 'investors',
});

module.exports = Investor;
