const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const ProjectMilestone = sequelize.define('ProjectMilestone', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    },
    projectId: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    title: {
        type: DataTypes.STRING(200),
        allowNull: false,
    },
    description: {
        type: DataTypes.TEXT,
        allowNull: true,
    },
    targetPercentage: {
        type: DataTypes.DECIMAL(5, 2),
        allowNull: true,
    },
    targetDate: {
        type: DataTypes.DATEONLY,
        allowNull: true,
    },
    completedAt: {
        type: DataTypes.DATE,
        allowNull: true,
    },
    status: {
        type: DataTypes.ENUM('pending', 'in_progress', 'completed'),
        defaultValue: 'pending',
    },
}, {
    tableName: 'project_milestones',
});

module.exports = ProjectMilestone;
