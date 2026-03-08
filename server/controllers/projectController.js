const { Op } = require('sequelize');
const {
    Project, ProjectMilestone, CostItem, Investment, PaymentSchedule,
    ContractorPayment, CostCategory, Investor, User, AuditLog, sequelize,
} = require('../models');

const projectController = {
    // GET /api/projects
    getAll: async (req, res, next) => {
        try {
            const { status, type, search, page = 1, limit = 20 } = req.query;
            const where = {};

            if (status) where.status = status;
            if (type) where.type = type;
            if (search) {
                where[Op.or] = [
                    { name: { [Op.like]: `%${search}%` } },
                    { location: { [Op.like]: `%${search}%` } },
                    { description: { [Op.like]: `%${search}%` } },
                ];
            }

            const offset = (parseInt(page) - 1) * parseInt(limit);
            const { count, rows: projects } = await Project.findAndCountAll({
                where,
                include: [
                    { model: User, as: 'creator', attributes: ['username', 'firstName', 'lastName'] },
                ],
                order: [['createdAt', 'DESC']],
                limit: parseInt(limit),
                offset,
            });

            res.json({
                projects,
                pagination: {
                    total: count,
                    page: parseInt(page),
                    limit: parseInt(limit),
                    totalPages: Math.ceil(count / parseInt(limit)),
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/projects/:id
    getById: async (req, res, next) => {
        try {
            const project = await Project.findByPk(req.params.id, {
                include: [
                    { model: User, as: 'creator', attributes: ['username', 'firstName', 'lastName'] },
                    { model: ProjectMilestone, as: 'milestones', order: [['targetPercentage', 'ASC']] },
                ],
            });

            if (!project) {
                return res.status(404).json({ message: 'Project not found.' });
            }

            // Get financial summary for this project
            const totalEstimated = await CostItem.sum('estimatedAmount', { where: { projectId: project.id } }) || 0;
            const totalActual = await CostItem.sum('actualAmount', { where: { projectId: project.id } }) || 0;
            const totalInvested = await Investment.sum('amount', { where: { projectId: project.id } }) || 0;
            const totalContractorPaid = await ContractorPayment.sum('amount', {
                where: { projectId: project.id, status: 'paid' },
            }) || 0;

            res.json({
                project,
                financials: {
                    totalEstimated: parseFloat(totalEstimated),
                    totalActual: parseFloat(totalActual),
                    totalInvested: parseFloat(totalInvested),
                    totalContractorPaid: parseFloat(totalContractorPaid),
                    budgetRemaining: parseFloat(project.totalBudget) - parseFloat(totalActual),
                    variance: parseFloat(totalEstimated) - parseFloat(totalActual),
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/projects
    create: async (req, res, next) => {
        try {
            const projectData = { ...req.body, createdBy: req.user.id };
            const project = await Project.create(projectData);

            await AuditLog.create({
                userId: req.user.id,
                action: 'create',
                entityType: 'project',
                entityId: project.id,
                description: `Created project "${project.name}"`,
                newValues: projectData,
                ipAddress: req.ip,
            });

            res.status(201).json({ message: 'Project created successfully', project });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/projects/:id
    update: async (req, res, next) => {
        try {
            const project = await Project.findByPk(req.params.id);
            if (!project) {
                return res.status(404).json({ message: 'Project not found.' });
            }

            const oldValues = project.toJSON();
            await project.update(req.body);

            await AuditLog.create({
                userId: req.user.id,
                action: 'update',
                entityType: 'project',
                entityId: project.id,
                description: `Updated project "${project.name}"`,
                oldValues,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.json({ message: 'Project updated successfully', project });
        } catch (error) {
            next(error);
        }
    },

    // DELETE /api/projects/:id
    delete: async (req, res, next) => {
        try {
            const project = await Project.findByPk(req.params.id);
            if (!project) {
                return res.status(404).json({ message: 'Project not found.' });
            }

            const projectName = project.name;
            await project.destroy();

            await AuditLog.create({
                userId: req.user.id,
                action: 'delete',
                entityType: 'project',
                entityId: req.params.id,
                description: `Deleted project "${projectName}"`,
                ipAddress: req.ip,
            });

            res.json({ message: 'Project deleted successfully.' });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/projects/:id/milestones
    addMilestone: async (req, res, next) => {
        try {
            const project = await Project.findByPk(req.params.id);
            if (!project) {
                return res.status(404).json({ message: 'Project not found.' });
            }

            const milestone = await ProjectMilestone.create({
                ...req.body,
                projectId: project.id,
            });

            res.status(201).json({ message: 'Milestone added', milestone });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/projects/:projectId/milestones/:id
    updateMilestone: async (req, res, next) => {
        try {
            const milestone = await ProjectMilestone.findOne({
                where: { id: req.params.id, projectId: req.params.projectId },
            });

            if (!milestone) {
                return res.status(404).json({ message: 'Milestone not found.' });
            }

            await milestone.update(req.body);

            // If milestone completed, check if we should update project progress
            if (req.body.status === 'completed' && !milestone.completedAt) {
                await milestone.update({ completedAt: new Date() });
            }

            res.json({ message: 'Milestone updated', milestone });
        } catch (error) {
            next(error);
        }
    },

    // DELETE /api/projects/:projectId/milestones/:id
    deleteMilestone: async (req, res, next) => {
        try {
            const milestone = await ProjectMilestone.findOne({
                where: { id: req.params.id, projectId: req.params.projectId },
            });

            if (!milestone) {
                return res.status(404).json({ message: 'Milestone not found.' });
            }

            await milestone.destroy();
            res.json({ message: 'Milestone deleted.' });
        } catch (error) {
            next(error);
        }
    },
};

module.exports = projectController;
