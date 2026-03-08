const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Document = sequelize.define('Document', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    name: {
        type: DataTypes.STRING(255),
        allowNull: false,
    },
    originalName: {
        type: DataTypes.STRING(255),
        allowNull: false,
    },
    filePath: {
        type: DataTypes.STRING(500),
        allowNull: false,
    },
    fileType: {
        type: DataTypes.STRING(50),
        allowNull: true,
    },
    fileSize: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    entityType: {
        type: DataTypes.ENUM('project', 'investor', 'contractor', 'cost_item', 'investment'),
        allowNull: false,
    },
    entityId: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    uploadedBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    notes: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
}, {
    tableName: 'documents',
});

module.exports = Document;
