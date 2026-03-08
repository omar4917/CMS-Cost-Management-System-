const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Contractor = sequelize.define('Contractor', {
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
    },
    phone: {
        type: DataTypes.STRING(30),
        allowNull: true,
    },
    company: {
        type: DataTypes.STRING(200),
        allowNull: true,
    },
    specialization: {
        type: DataTypes.STRING(200),
        allowNull: true,
    },
    address: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        defaultValue: true,
    },
    rating: {
        type: DataTypes.DECIMAL(3, 1),
        allowNull: true,
        validate: { min: 0, max: 5 },
    },
    notes: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
}, {
    tableName: 'contractors',
});

module.exports = Contractor;
