const { Op } = require('sequelize');
const {
    CostItem, CostCategory, Project, User, AuditLog, Investment,
    InvestorType, Investor, PaymentSchedule, Contractor, ContractorPayment,
    Currency, Setting, sequelize,
} = require('../models');

const costController = {
    // GET /api/cost-categories
    getCategories: async (req, res, next) => {
        try {
            const categories = await CostCategory.findAll({
                where: { parentId: null },
                include: [{ model: CostCategory, as: 'children' }],
                order: [['sortOrder', 'ASC'], ['name', 'ASC']],
            });
            res.json({ categories });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/cost-categories
    createCategory: async (req, res, next) => {
        try {
            const category = await CostCategory.create(req.body);
            res.status(201).json({ message: 'Category created', category });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/cost-categories/:id
    updateCategory: async (req, res, next) => {
        try {
            const category = await CostCategory.findByPk(req.params.id);
            if (!category) return res.status(404).json({ message: 'Category not found.' });
            await category.update(req.body);
            res.json({ message: 'Category updated', category });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/projects/:projectId/costs
    getProjectCosts: async (req, res, next) => {
        try {
            const { projectId } = req.params;
            const { categoryId, status, search } = req.query;
            const where = { projectId };

            if (categoryId) where.categoryId = categoryId;
            if (status) where.status = status;
            if (search) {
                where[Op.or] = [
                    { description: { [Op.like]: `%${search}%` } },
                    { vendor: { [Op.like]: `%${search}%` } },
                ];
            }

            const costItems = await CostItem.findAll({
                where,
                include: [
                    { model: CostCategory, as: 'category', attributes: ['name', 'icon'] },
                    { model: User, as: 'creator', attributes: ['username'] },
                ],
                order: [['date', 'DESC']],
            });

            // Summary by category
            const categoryBreakdown = await CostItem.findAll({
                where: { projectId },
                attributes: [
                    'categoryId',
                    [sequelize.fn('SUM', sequelize.col('estimated_amount')), 'totalEstimated'],
                    [sequelize.fn('SUM', sequelize.col('actual_amount')), 'totalActual'],
                    [sequelize.fn('COUNT', sequelize.col('CostItem.id')), 'itemCount'],
                ],
                include: [{ model: CostCategory, as: 'category', attributes: ['name', 'icon'] }],
                group: ['categoryId', 'category.id', 'category.name', 'category.icon'],
            });

            const totalEstimated = await CostItem.sum('estimatedAmount', { where: { projectId } }) || 0;
            const totalActual = await CostItem.sum('actualAmount', { where: { projectId } }) || 0;

            res.json({
                costItems,
                categoryBreakdown,
                totals: {
                    estimated: parseFloat(totalEstimated),
                    actual: parseFloat(totalActual),
                    variance: parseFloat(totalEstimated) - parseFloat(totalActual),
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/projects/:projectId/costs
    createCostItem: async (req, res, next) => {
        try {
            const costItem = await CostItem.create({
                ...req.body,
                projectId: req.params.projectId,
                createdBy: req.user.id,
            });

            await AuditLog.create({
                userId: req.user.id,
                action: 'create',
                entityType: 'cost_item',
                entityId: costItem.id,
                description: `Added cost item "${costItem.description}" to project`,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.status(201).json({ message: 'Cost item added', costItem });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/costs/:id
    updateCostItem: async (req, res, next) => {
        try {
            const costItem = await CostItem.findByPk(req.params.id);
            if (!costItem) return res.status(404).json({ message: 'Cost item not found.' });

            const oldValues = costItem.toJSON();
            await costItem.update(req.body);

            await AuditLog.create({
                userId: req.user.id,
                action: 'update',
                entityType: 'cost_item',
                entityId: costItem.id,
                description: `Updated cost item "${costItem.description}"`,
                oldValues,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.json({ message: 'Cost item updated', costItem });
        } catch (error) {
            next(error);
        }
    },

    // DELETE /api/costs/:id
    deleteCostItem: async (req, res, next) => {
        try {
            const costItem = await CostItem.findByPk(req.params.id);
            if (!costItem) return res.status(404).json({ message: 'Cost item not found.' });

            await costItem.destroy();

            await AuditLog.create({
                userId: req.user.id,
                action: 'delete',
                entityType: 'cost_item',
                entityId: req.params.id,
                description: `Deleted cost item`,
                ipAddress: req.ip,
            });

            res.json({ message: 'Cost item deleted.' });
        } catch (error) {
            next(error);
        }
    },

    // --- Investment CRUD ---

    // GET /api/investments
    getInvestments: async (req, res, next) => {
        try {
            const { investorId, projectId, page = 1, limit = 20 } = req.query;
            const where = {};
            if (investorId) where.investorId = investorId;
            if (projectId) where.projectId = projectId;

            const offset = (parseInt(page) - 1) * parseInt(limit);
            const { count, rows: investments } = await Investment.findAndCountAll({
                where,
                include: [
                    { model: Investor, as: 'investor', attributes: ['name', 'email'], include: [{ model: InvestorType, as: 'type', attributes: ['name', 'color'] }] },
                    { model: Project, as: 'project', attributes: ['name', 'status'] },
                    { model: User, as: 'creator', attributes: ['username'] },
                ],
                order: [['date', 'DESC']],
                limit: parseInt(limit),
                offset,
            });

            res.json({
                investments,
                pagination: { total: count, page: parseInt(page), limit: parseInt(limit), totalPages: Math.ceil(count / parseInt(limit)) },
            });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/investments
    createInvestment: async (req, res, next) => {
        try {
            const investment = await Investment.create({ ...req.body, createdBy: req.user.id });

            await AuditLog.create({
                userId: req.user.id,
                action: 'create',
                entityType: 'investment',
                entityId: investment.id,
                description: `New investment of ${investment.amount}`,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.status(201).json({ message: 'Investment recorded', investment });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/investments/:id
    updateInvestment: async (req, res, next) => {
        try {
            const investment = await Investment.findByPk(req.params.id);
            if (!investment) return res.status(404).json({ message: 'Investment not found.' });

            const oldValues = investment.toJSON();
            await investment.update(req.body);

            await AuditLog.create({
                userId: req.user.id,
                action: 'update',
                entityType: 'investment',
                entityId: investment.id,
                description: `Updated investment`,
                oldValues,
                newValues: req.body,
                ipAddress: req.ip,
            });

            res.json({ message: 'Investment updated', investment });
        } catch (error) {
            next(error);
        }
    },

    // DELETE /api/investments/:id
    deleteInvestment: async (req, res, next) => {
        try {
            const investment = await Investment.findByPk(req.params.id);
            if (!investment) return res.status(404).json({ message: 'Investment not found.' });
            await investment.destroy();
            res.json({ message: 'Investment deleted.' });
        } catch (error) {
            next(error);
        }
    },

    // --- Payment Schedules ---

    // GET /api/payment-schedules
    getPaymentSchedules: async (req, res, next) => {
        try {
            const { investorId, projectId, status } = req.query;
            const where = {};
            if (investorId) where.investorId = investorId;
            if (projectId) where.projectId = projectId;
            if (status) where.status = status;

            const schedules = await PaymentSchedule.findAll({
                where,
                include: [
                    { model: Investor, as: 'investor', attributes: ['name', 'email'] },
                    { model: Project, as: 'project', attributes: ['name'] },
                ],
                order: [['dueDate', 'ASC']],
            });

            res.json({ schedules });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/payment-schedules
    createPaymentSchedule: async (req, res, next) => {
        try {
            const schedule = await PaymentSchedule.create(req.body);
            res.status(201).json({ message: 'Payment schedule created', schedule });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/payment-schedules/:id
    updatePaymentSchedule: async (req, res, next) => {
        try {
            const schedule = await PaymentSchedule.findByPk(req.params.id);
            if (!schedule) return res.status(404).json({ message: 'Payment schedule not found.' });
            await schedule.update(req.body);
            res.json({ message: 'Payment schedule updated', schedule });
        } catch (error) {
            next(error);
        }
    },

    // --- Contractor CRUD ---

    // GET /api/contractors
    getContractors: async (req, res, next) => {
        try {
            const { search, isActive } = req.query;
            const where = {};
            if (isActive !== undefined) where.isActive = isActive === 'true';
            if (search) {
                where[Op.or] = [
                    { name: { [Op.like]: `%${search}%` } },
                    { company: { [Op.like]: `%${search}%` } },
                    { specialization: { [Op.like]: `%${search}%` } },
                ];
            }

            const contractors = await Contractor.findAll({ where, order: [['name', 'ASC']] });

            // Get payment summary for each contractor
            const contractorsWithPayments = await Promise.all(
                contractors.map(async (c) => {
                    const totalPaid = await ContractorPayment.sum('amount', { where: { contractorId: c.id, status: 'paid' } }) || 0;
                    const totalPending = await ContractorPayment.sum('amount', { where: { contractorId: c.id, status: { [Op.ne]: 'paid' } } }) || 0;
                    return { ...c.toJSON(), totalPaid: parseFloat(totalPaid), totalPending: parseFloat(totalPending) };
                })
            );

            res.json({ contractors: contractorsWithPayments });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/contractors
    createContractor: async (req, res, next) => {
        try {
            const contractor = await Contractor.create(req.body);
            res.status(201).json({ message: 'Contractor created', contractor });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/contractors/:id
    updateContractor: async (req, res, next) => {
        try {
            const contractor = await Contractor.findByPk(req.params.id);
            if (!contractor) return res.status(404).json({ message: 'Contractor not found.' });
            await contractor.update(req.body);
            res.json({ message: 'Contractor updated', contractor });
        } catch (error) {
            next(error);
        }
    },

    // DELETE /api/contractors/:id
    deleteContractor: async (req, res, next) => {
        try {
            const contractor = await Contractor.findByPk(req.params.id);
            if (!contractor) return res.status(404).json({ message: 'Contractor not found.' });
            await contractor.destroy();
            res.json({ message: 'Contractor deleted.' });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/contractors/:id/payments
    getContractorPayments: async (req, res, next) => {
        try {
            const payments = await ContractorPayment.findAll({
                where: { contractorId: req.params.id },
                include: [{ model: Project, as: 'project', attributes: ['name'] }],
                order: [['date', 'DESC']],
            });
            res.json({ payments });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/contractors/:id/payments
    createContractorPayment: async (req, res, next) => {
        try {
            const payment = await ContractorPayment.create({
                ...req.body,
                contractorId: req.params.id,
                createdBy: req.user.id,
            });
            res.status(201).json({ message: 'Payment recorded', payment });
        } catch (error) {
            next(error);
        }
    },

    // --- Currencies ---

    // GET /api/currencies
    getCurrencies: async (req, res, next) => {
        try {
            const currencies = await Currency.findAll({
                where: { isActive: true },
                order: [['isBase', 'DESC'], ['code', 'ASC']],
            });
            res.json({ currencies });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/currencies/:id
    updateCurrency: async (req, res, next) => {
        try {
            const currency = await Currency.findByPk(req.params.id);
            if (!currency) return res.status(404).json({ message: 'Currency not found.' });
            await currency.update(req.body);
            res.json({ message: 'Currency updated', currency });
        } catch (error) {
            next(error);
        }
    },

    // --- Investor Types ---

    // GET /api/investor-types
    getInvestorTypes: async (req, res, next) => {
        try {
            const types = await InvestorType.findAll({ order: [['name', 'ASC']] });
            res.json({ types });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/investor-types
    createInvestorType: async (req, res, next) => {
        try {
            const type = await InvestorType.create(req.body);
            res.status(201).json({ message: 'Investor type created', type });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/investor-types/:id
    updateInvestorType: async (req, res, next) => {
        try {
            const type = await InvestorType.findByPk(req.params.id);
            if (!type) return res.status(404).json({ message: 'Type not found.' });
            await type.update(req.body);
            res.json({ message: 'Investor type updated', type });
        } catch (error) {
            next(error);
        }
    },

    // --- Settings ---

    // GET /api/settings
    getSettings: async (req, res, next) => {
        try {
            const { category } = req.query;
            const where = {};
            if (category) where.category = category;
            const settings = await Setting.findAll({ where, order: [['category', 'ASC'], ['key', 'ASC']] });
            res.json({ settings });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/settings
    updateSettings: async (req, res, next) => {
        try {
            const { settings } = req.body; // Array of { key, value }
            for (const s of settings) {
                await Setting.upsert({ key: s.key, value: s.value, category: s.category, description: s.description });
            }
            res.json({ message: 'Settings updated successfully.' });
        } catch (error) {
            next(error);
        }
    },

    // --- Audit Logs ---

    // GET /api/audit-logs
    getAuditLogs: async (req, res, next) => {
        try {
            const { User } = require('../models');
            const { entityType, action, userId, page = 1, limit = 50 } = req.query;
            const where = {};
            if (entityType) where.entityType = entityType;
            if (action) where.action = action;
            if (userId) where.userId = userId;

            const offset = (parseInt(page) - 1) * parseInt(limit);
            const { count, rows: logs } = await AuditLog.findAndCountAll({
                where,
                include: [{ model: User, as: 'user', attributes: ['username', 'firstName', 'lastName'] }],
                order: [['createdAt', 'DESC']],
                limit: parseInt(limit),
                offset,
            });

            res.json({
                logs,
                pagination: { total: count, page: parseInt(page), limit: parseInt(limit), totalPages: Math.ceil(count / parseInt(limit)) },
            });
        } catch (error) {
            next(error);
        }
    },

    // --- Notes ---

    // GET /api/notes?entityType=project&entityId=1
    getNotes: async (req, res, next) => {
        try {
            const { User } = require('../models');
            const { entityType, entityId } = req.query;
            const where = {};
            if (entityType) where.entityType = entityType;
            if (entityId) where.entityId = entityId;

            const { Note } = require('../models');
            const notes = await Note.findAll({
                where,
                include: [{ model: User, as: 'author', attributes: ['username', 'firstName', 'lastName'] }],
                order: [['createdAt', 'DESC']],
            });

            res.json({ notes });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/notes
    createNote: async (req, res, next) => {
        try {
            const { Note } = require('../models');
            const note = await Note.create({ ...req.body, createdBy: req.user.id });
            res.status(201).json({ message: 'Note added', note });
        } catch (error) {
            next(error);
        }
    },
};

module.exports = costController;
