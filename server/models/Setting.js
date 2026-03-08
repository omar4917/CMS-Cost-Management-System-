const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Setting = sequelize.define('Setting', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    key: {
        type: DataTypes.STRING(100),
        allowNull: false,
        unique: true,
    },
    value: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    category: {
        type: DataTypes.STRING(50),
        defaultValue: 'general',
    },
    description: {
        type: DataTypes.STRING(300),
        allowNull: true,
    },
}, {
    tableName: 'settings',
});

module.exports = Setting;
