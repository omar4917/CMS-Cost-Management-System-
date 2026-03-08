const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const InvestorType = sequelize.define('InvestorType', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(100),
        allowNull: false,
        unique: true,
    },
    description: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    color: {
        type: DataTypes.STRING(20),
        defaultValue: '#3b82f6',
    },
}, {
    tableName: 'investor_types',
});

module.exports = InvestorType;
