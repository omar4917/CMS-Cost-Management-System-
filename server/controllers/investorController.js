const { Op } = require('sequelize');
const {
    Investor, InvestorType, Investment, PaymentSchedule, Project, AuditLog, sequelize,
} = require('../models');

const investorController = {
    // GET /api/investors
    getAll: async (req, res, next) => {
        try {
            const { typeId, isActive, search, page = 1, limit = 20 } = req.query;
            const where = {};

            if (typeId) where.typeId = typeId;
            if (isActive !== undefined) where.isActive = isActive === 'true';
            if (search) {
                where[Op.or] = [
                    { name: { [Op.like]: `%${search}%` } },
                    { email: { [Op.like]: `%${search}%` } },
                    { company: { [Op.like]: `%${search}%` } },
                    { phone: { [Op.like]: `%${search}%` } },
                ];
            }

            const offset = (parseInt(page) - 1) * parseInt(limit);
            const { count, rows: investors } = await Investor.findAndCountAll({
                where,
                include: [{ model: InvestorType, as: 'type', attributes: ['name', 'color'] }],
                order: [['createdAt', 'DESC']],
                limit: parseInt(limit),
                offset,
            });

            res.json({
                investors,
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

    // GET /api/investors/:id
    getById: async (req, res, next) => {
        try {
            const investor = await Investor.findByPk(req.params.id, {
                include: [{ model: InvestorType, as: 'type' }],
            });

            if (!investor) {
                return res.status(404).json({ message: 'Investor not found.' });
            }

            // Get investment summary
            const totalInvested = await Investment.sum('amount', { where: { investorId: investor.id } }) || 0;
            const totalScheduled = await PaymentSchedule.sum('amount', { where: { investorId: investor.id } }) || 0;
            const totalPaid = await PaymentSchedule.sum('paidAmount', { where: { investorId: investor.id } }) || 0;
            const pendingPayments = await PaymentSchedule.count({
                where: { investorId: investor.id, status: { [Op.in]: ['pending', 'overdue'] } },
            });
            const overduePayments = await PaymentSchedule.count({
                where: { investorId: investor.id, status: 'overdue' },
            });

            // Investments by project
            const investments = await Investment.findAll({
                where: { investorId: investor.id },
                include: [{ model: Project, as: 'project', attributes: ['id', 'name', 'status', 'progress'] }],
                order: [['date', 'DESC']],
            });

            // Payment schedules
            const schedules = await PaymentSchedule.findAll({
                where: { investorId: investor.id },
                include: [{ model: Project, as: 'project', attributes: ['id', 'name'] }],
                order: [['dueDate', 'ASC']],
            });

            res.json({
                investor,
                summary: {
                    totalInvested: parseFloat(totalInvested),
                    totalScheduled: parseFloat(totalScheduled),
                    totalPaid: parseFloat(totalPaid),
                    unpaid: parseFloat(totalScheduled) - parseFloat(totalPaid),
                    pendingPayments,
                    overduePayments,
                },
                investments,
                schedules,
            });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/investors
    create: async (req, res, next) => {
        try {
            const investor = await Investor.create(req.body);

            await AuditLog.create({
                userId: req.user.id,
                action: 'create',
                entityType: 'investor',
                entityId: investor.id,
                description: `Created investor "${investor.name}"`,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.status(201).json({ message: 'Investor created successfully', investor });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/investors/:id
    update: async (req, res, next) => {
        try {
            const investor = await Investor.findByPk(req.params.id);
            if (!investor) {
                return res.status(404).json({ message: 'Investor not found.' });
            }

            const oldValues = investor.toJSON();
            await investor.update(req.body);

            await AuditLog.create({
                userId: req.user.id,
                action: 'update',
                entityType: 'investor',
                entityId: investor.id,
                description: `Updated investor "${investor.name}"`,
                oldValues,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.json({ message: 'Investor updated successfully', investor });
        } catch (error) {
            next(error);
        }
    },

    // DELETE /api/investors/:id
    delete: async (req, res, next) => {
        try {
            const investor = await Investor.findByPk(req.params.id);
            if (!investor) {
                return res.status(404).json({ message: 'Investor not found.' });
            }

            await investor.destroy();

            await AuditLog.create({
                userId: req.user.id,
                action: 'delete',
                entityType: 'investor',
                entityId: req.params.id,
                description: `Deleted investor "${investor.name}"`,
                ipAddress: req.ip,
            });

            res.json({ message: 'Investor deleted successfully.' });
        } catch (error) {
            next(error);
        }
    },
};

module.exports = investorController;
