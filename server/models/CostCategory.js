const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const CostCategory = sequelize.define('CostCategory', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(150),
        allowNull: false,
    },
    icon: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
    description: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    isDefault: {
        type: DataTypes.BOOLEAN,
        defaultValue: false,
    },
    parentId: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    sortOrder: {
        type: DataTypes.INTEGER,
        defaultValue: 0,
    },
}, {
    tableName: 'cost_categories',
});

module.exports = CostCategory;
