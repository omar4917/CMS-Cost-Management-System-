const { Op } = require('sequelize');
const {
    Investor, Investment, PaymentSchedule, Project, ProjectMilestone, CostItem,
} = require('../models');

const investorPortalController = {
    // GET /api/investor-portal/dashboard
    getDashboard: async (req, res, next) => {
        try {
            const investorId = req.user.investorId;
            if (!investorId) {
                return res.status(403).json({ message: 'User is not linked to any investor profile.' });
            }

            const investor = await Investor.findByPk(investorId);

            // Stats
            const totalInvested = await Investment.sum('amount', { where: { investorId } }) || 0;
            const totalScheduled = await PaymentSchedule.sum('amount', { where: { investorId } }) || 0;
            const totalPaid = await PaymentSchedule.sum('paidAmount', { where: { investorId } }) || 0;

            // Latest Investments
            const latestInvestments = await Investment.findAll({
                where: { investorId },
                include: [{ model: Project, as: 'project', attributes: ['name'] }],
                limit: 5,
                order: [['date', 'DESC']]
            });

            // Upcoming Payments
            const upcomingPayments = await PaymentSchedule.findAll({
                where: {
                    investorId,
                    status: { [Op.in]: ['pending', 'overdue'] }
                },
                include: [{ model: Project, as: 'project', attributes: ['name'] }],
                limit: 5,
                order: [['dueDate', 'ASC']]
            });

            res.json({
                investor,
                summary: {
                    totalInvested: parseFloat(totalInvested),
                    totalPaid: parseFloat(totalPaid),
                    unpaid: parseFloat(totalScheduled) - parseFloat(totalPaid),
                },
                latestInvestments,
                upcomingPayments
            });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/investor-portal/investments
    getInvestments: async (req, res, next) => {
        try {
            const investments = await Investment.findAll({
                where: { investorId: req.user.investorId },
                include: [{ model: Project, as: 'project', attributes: ['id', 'name', 'status', 'progress', 'location'] }],
                order: [['date', 'DESC']]
            });
            res.json(investments);
        } catch (error) {
            next(error);
        }
    },

    // GET /api/investor-portal/payments
    getPayments: async (req, res, next) => {
        try {
            const payments = await PaymentSchedule.findAll({
                where: { investorId: req.user.investorId },
                include: [{ model: Project, as: 'project', attributes: ['id', 'name'] }],
                order: [['dueDate', 'ASC']]
            });
            res.json(payments);
        } catch (error) {
            next(error);
        }
    },

    // GET /api/investor-portal/projects/:id
    getProjectDetail: async (req, res, next) => {
        try {
            const { id } = req.params;
            const investorId = req.user.investorId;

            // First check if they have invested in this project
            const hasInvestment = await Investment.findOne({
                where: { projectId: id, investorId }
            });

            if (!hasInvestment && req.user.role !== 'admin') {
                return res.status(403).json({ message: 'Access denied to this project.' });
            }

            const project = await Project.findByPk(id, {
                include: [
                    { model: ProjectMilestone, as: 'milestones' }
                ]
            });

            if (!project) return res.status(404).json({ message: 'Project not found' });

            // Their specific financial status in this project
            const totalInvested = await Investment.sum('amount', { where: { projectId: id, investorId } }) || 0;
            const totalPaid = await PaymentSchedule.sum('paidAmount', { where: { projectId: id, investorId } }) || 0;
            const totalScheduled = await PaymentSchedule.sum('amount', { where: { projectId: id, investorId } }) || 0;

            res.json({
                project,
                myStats: {
                    invested: parseFloat(totalInvested),
                    paid: parseFloat(totalPaid),
                    pending: parseFloat(totalScheduled) - parseFloat(totalPaid)
                }
            });
        } catch (error) {
            next(error);
        }
    }
};

module.exports = investorPortalController;
