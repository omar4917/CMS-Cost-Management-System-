const { Op } = require('sequelize');
const {
    sequelize, Project, CostItem, Investment, Investor, InvestorType,
    PaymentSchedule, Contractor, ContractorPayment, ProjectMilestone, CostCategory
} = require('../models');

const dashboardController = {
    // GET /api/dashboard/summary
    getSummary: async (req, res, next) => {
        try {
            // Project stats
            const totalProjects = await Project.count();
            const activeProjects = await Project.count({ where: { status: 'active' } });
            const completedProjects = await Project.count({ where: { status: 'completed' } });

            // Financial stats
            const totalBudget = await Project.sum('totalBudget') || 0;
            const totalEstimatedCosts = await CostItem.sum('estimatedAmount') || 0;
            const totalActualCosts = await CostItem.sum('actualAmount') || 0;
            const totalInvestments = await Investment.sum('amount') || 0;

            // Investor stats
            const totalInvestors = await Investor.count({ where: { isActive: true } });
            const totalContractors = await Contractor.count({ where: { isActive: true } });

            // Payment stats
            const overduePayments = await PaymentSchedule.count({
                where: { status: 'overdue' },
            });
            const pendingPayments = await PaymentSchedule.count({
                where: { status: 'pending' },
            });
            const totalContractorPaid = await ContractorPayment.sum('amount', {
                where: { status: 'paid' },
            }) || 0;

            // Cash position
            const cashInflow = totalInvestments;
            const cashOutflow = totalActualCosts + totalContractorPaid;
            const cashBalance = cashInflow - cashOutflow;

            res.json({
                projects: {
                    total: totalProjects,
                    active: activeProjects,
                    completed: completedProjects,
                },
                financials: {
                    totalBudget: parseFloat(totalBudget),
                    totalEstimatedCosts: parseFloat(totalEstimatedCosts),
                    totalActualCosts: parseFloat(totalActualCosts),
                    totalInvestments: parseFloat(totalInvestments),
                    budgetVariance: parseFloat(totalBudget) - parseFloat(totalActualCosts),
                    cashBalance: parseFloat(cashBalance),
                },
                people: {
                    totalInvestors,
                    totalContractors,
                },
                payments: {
                    overduePayments,
                    pendingPayments,
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/dashboard/recent-activity
    getRecentActivity: async (req, res, next) => {
        try {
            const { AuditLog, User } = require('../models');
            const logs = await AuditLog.findAll({
                include: [{ model: User, as: 'user', attributes: ['username', 'firstName', 'lastName'] }],
                order: [['createdAt', 'DESC']],
                limit: 20,
            });
            res.json({ activities: logs });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/dashboard/project-progress
    getProjectProgress: async (req, res, next) => {
        try {
            const projects = await Project.findAll({
                where: { status: { [Op.in]: ['active', 'planning'] } },
                attributes: ['id', 'name', 'progress', 'status', 'totalBudget', 'startDate', 'estimatedEndDate'],
                order: [['progress', 'DESC']],
                limit: 10,
            });
            res.json({ projects });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/dashboard/cost-breakdown
    getCostBreakdown: async (req, res, next) => {
        try {
            const breakdown = await CostItem.findAll({
                attributes: [
                    'categoryId',
                    [sequelize.fn('SUM', sequelize.col('actual_amount')), 'totalActual'],
                    [sequelize.fn('SUM', sequelize.col('estimated_amount')), 'totalEstimated'],
                    [sequelize.fn('COUNT', sequelize.col('CostItem.id')), 'count'],
                ],
                include: [{ model: CostCategory, as: 'category', attributes: ['name', 'icon'] }],
                group: ['categoryId', 'category.id', 'category.name', 'category.icon'],
                order: [[sequelize.fn('SUM', sequelize.col('actual_amount')), 'DESC']],
            });
            res.json({ breakdown });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/dashboard/investment-overview
    getInvestmentOverview: async (req, res, next) => {
        try {
            const byType = await Investment.findAll({
                attributes: [
                    [sequelize.fn('SUM', sequelize.col('Investment.amount')), 'totalAmount'],
                    [sequelize.fn('COUNT', sequelize.col('Investment.id')), 'count'],
                ],
                include: [{
                    model: Investor,
                    as: 'investor',
                    attributes: [],
                    include: [{ model: InvestorType, as: 'type', attributes: ['name', 'color'] }],
                }],
                group: ['investor.type.id', 'investor.type.name', 'investor.type.color'],
                raw: true,
                nest: true,
            });

            const recentInvestments = await Investment.findAll({
                include: [
                    { model: Investor, as: 'investor', attributes: ['name'] },
                    { model: Project, as: 'project', attributes: ['name'] },
                ],
                order: [['date', 'DESC']],
                limit: 10,
            });

            res.json({ byType, recentInvestments });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/dashboard/upcoming-payments
    getUpcomingPayments: async (req, res, next) => {
        try {
            const thirtyDaysFromNow = new Date();
            thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

            const payments = await PaymentSchedule.findAll({
                where: {
                    status: { [Op.in]: ['pending', 'overdue'] },
                    dueDate: { [Op.lte]: thirtyDaysFromNow },
                },
                include: [
                    { model: Investor, as: 'investor', attributes: ['name', 'email'] },
                    { model: Project, as: 'project', attributes: ['name'] },
                ],
                order: [['dueDate', 'ASC']],
                limit: 15,
            });

            res.json({ payments });
        } catch (error) {
            next(error);
        }
    },
};

module.exports = dashboardController;
