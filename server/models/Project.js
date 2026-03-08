const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Project = sequelize.define('Project', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(200),
        allowNull: false,
    },
    description: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    location: {
        type: DataTypes.STRING(300),
        allowNull: true,
    },
    type: {
        type: DataTypes.ENUM('residential', 'commercial', 'mixed', 'industrial', 'land_development', 'renovation'),
        defaultValue: 'residential',
    },
    status: {
        type: DataTypes.ENUM('planning', 'active', 'paused', 'completed', 'cancelled'),
        defaultValue: 'planning',
    },
    startDate: {
        type: DataTypes.DATEONLY,
        allowNull: true,
    },
    estimatedEndDate: {
        type: DataTypes.DATEONLY,
        allowNull: true,
    },
    actualEndDate: {
        type: DataTypes.DATEONLY,
        allowNull: true,
    },
    totalBudget: {
        type: DataTypes.DECIMAL(15, 2),
        defaultValue: 0,
    },
    progress: {
        type: DataTypes.DECIMAL(5, 2),
        defaultValue: 0,
        validate: { min: 0, max: 100 },
    },
    totalFloors: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    totalUnits: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    landArea: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    buildingArea: {
        type: DataTypes.STRING(100),
        allowNull: true,
    },
    createdBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
}, {
    tableName: 'projects',
});

module.exports = Project;
