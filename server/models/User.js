const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const User = sequelize.define('User', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    username: {
        type: DataTypes.STRING(50),
        allowNull: false,
        unique: true,
    },
    email: {
        type: DataTypes.STRING(100),
        allowNull: false,
        unique: true,
        validate: { isEmail: true },
    },
    password: {
        type: DataTypes.STRING(255),
        allowNull: false,
    },
    firstName: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
    lastName: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
    role: {
        type: DataTypes.ENUM('admin', 'superadmin', 'investor'),
        defaultValue: 'admin',
    },
    investorId: {
        type: DataTypes.INTEGER,
        allowNull: true,
        references: {
            model: 'investors',
            key: 'id',
        },
    },
    avatar: {
        type: DataTypes.STRING(255),
        allowNull: true,
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        defaultValue: true,
    },
    lastLogin: {
        type: DataTypes.DATE,
        allowNull: true,
    },
}, {
    tableName: 'users',
});

module.exports = User;
