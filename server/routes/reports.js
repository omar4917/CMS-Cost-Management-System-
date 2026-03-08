/**
 * Reports & Export Routes
 * Generates CSV exports for projects, investors, costs, and investments.
 */

const router = require('express').Router();
const { auth } = require('../middleware/auth');
const { Project, Investor, Investment, CostItem, CostCategory, PaymentSchedule, InvestorType } = require('../models');

router.use(auth);

/**
 * Helper: Convert array of objects to CSV string
 */
function toCSV(data, columns) {
    if (!data.length) return '';
    const header = columns.map(c => c.label).join(',');
    const rows = data.map(row =>
        columns.map(c => {
            let val = c.key.split('.').reduce((obj, key) => obj?.[key], row);
            if (val === null || val === undefined) val = '';
            val = String(val).replace(/"/g, '""');
            if (val.includes(',') || val.includes('"') || val.includes('\n')) val = `"${val}"`;
            return val;
        }).join(',')
    );
    return [header, ...rows].join('\n');
}

function sendCSV(res, csv, filename) {
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.send(csv);
}

// ============ PROJECT REPORT ============
router.get('/project/:id', async (req, res) => {
    try {
        const project = await Project.findByPk(req.params.id, {
            include: [
                { model: CostItem, as: 'costItems', include: [{ model: CostCategory, as: 'category' }] },
                { model: Investment, as: 'investments', include: [{ model: Investor, as: 'investor' }] },
            ],
        });
        if (!project) return res.status(404).json({ message: 'Project not found' });

        const data = {
            project: project.toJSON(),
            totalBudget: parseFloat(project.totalBudget || 0),
            totalEstimated: project.costItems?.reduce((s, i) => s + parseFloat(i.estimatedAmount || 0), 0) || 0,
            totalActual: project.costItems?.reduce((s, i) => s + parseFloat(i.actualAmount || 0), 0) || 0,
            totalInvested: project.investments?.reduce((s, i) => s + parseFloat(i.amount || 0), 0) || 0,
            costItems: project.costItems?.length || 0,
            investors: project.investments?.length || 0,
        };

        res.json(data);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// ============ INVESTOR STATEMENT ============
router.get('/investor/:id', async (req, res) => {
    try {
        const investor = await Investor.findByPk(req.params.id, {
            include: [
                { model: InvestorType, as: 'investorType' },
                { model: Investment, as: 'investments', include: [{ model: Project, as: 'project' }] },
                { model: PaymentSchedule, as: 'paymentSchedules', include: [{ model: Project, as: 'project' }] },
            ],
        });
        if (!investor) return res.status(404).json({ message: 'Investor not found' });

        const inv = investor.toJSON();
        res.json({
            investor: inv,
            totalInvested: inv.investments?.reduce((s, i) => s + parseFloat(i.amount || 0), 0) || 0,
            totalPaid: inv.paymentSchedules?.filter(p => p.status === 'paid').reduce((s, i) => s + parseFloat(i.amount || 0), 0) || 0,
            pendingPayments: inv.paymentSchedules?.filter(p => p.status === 'pending').length || 0,
        });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// ============ CSV EXPORTS ============

// Export all projects
router.get('/export/projects', async (req, res) => {
    try {
        const projects = await Project.findAll({ order: [['createdAt', 'DESC']] });
        const csv = toCSV(projects.map(p => p.toJSON()), [
            { label: 'ID', key: 'id' },
            { label: 'Name', key: 'name' },
            { label: 'Status', key: 'status' },
            { label: 'Location', key: 'location' },
            { label: 'Total Budget', key: 'totalBudget' },
            { label: 'Spent Amount', key: 'spentAmount' },
            { label: 'Progress %', key: 'progress' },
            { label: 'Start Date', key: 'startDate' },
            { label: 'End Date', key: 'expectedEndDate' },
            { label: 'Total Floors', key: 'totalFloors' },
            { label: 'Total Units', key: 'totalUnits' },
            { label: 'Created', key: 'createdAt' },
        ]);
        sendCSV(res, csv, `projects_export_${Date.now()}.csv`);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Export all investors
router.get('/export/investors', async (req, res) => {
    try {
        const investors = await Investor.findAll({
            include: [{ model: InvestorType, as: 'investorType' }],
            order: [['name', 'ASC']],
        });
        const csv = toCSV(investors.map(i => i.toJSON()), [
            { label: 'ID', key: 'id' },
            { label: 'Name', key: 'name' },
            { label: 'Email', key: 'email' },
            { label: 'Phone', key: 'phone' },
            { label: 'Company', key: 'company' },
            { label: 'Type', key: 'investorType.name' },
            { label: 'National ID', key: 'nationalId' },
            { label: 'Bank Name', key: 'bankName' },
            { label: 'Bank Account', key: 'bankAccount' },
            { label: 'Active', key: 'isActive' },
            { label: 'Created', key: 'createdAt' },
        ]);
        sendCSV(res, csv, `investors_export_${Date.now()}.csv`);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Export all costs
router.get('/export/costs', async (req, res) => {
    try {
        const items = await CostItem.findAll({
            include: [
                { model: CostCategory, as: 'category' },
                { model: Project, as: 'project' },
            ],
            order: [['createdAt', 'DESC']],
        });
        const csv = toCSV(items.map(i => i.toJSON()), [
            { label: 'ID', key: 'id' },
            { label: 'Name', key: 'name' },
            { label: 'Category', key: 'category.name' },
            { label: 'Project', key: 'project.name' },
            { label: 'Quantity', key: 'quantity' },
            { label: 'Unit', key: 'unit' },
            { label: 'Unit Price', key: 'unitPrice' },
            { label: 'Estimated', key: 'estimatedAmount' },
            { label: 'Actual', key: 'actualAmount' },
            { label: 'Vendor', key: 'vendor' },
            { label: 'Status', key: 'status' },
            { label: 'Date', key: 'date' },
            { label: 'Invoice No', key: 'invoiceNo' },
        ]);
        sendCSV(res, csv, `costs_export_${Date.now()}.csv`);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Export all investments
router.get('/export/investments', async (req, res) => {
    try {
        const investments = await Investment.findAll({
            include: [
                { model: Investor, as: 'investor' },
                { model: Project, as: 'project' },
            ],
            order: [['date', 'DESC']],
        });
        const csv = toCSV(investments.map(i => i.toJSON()), [
            { label: 'ID', key: 'id' },
            { label: 'Investor', key: 'investor.name' },
            { label: 'Project', key: 'project.name' },
            { label: 'Amount', key: 'amount' },
            { label: 'Date', key: 'date' },
            { label: 'Payment Method', key: 'paymentMethod' },
            { label: 'Reference No', key: 'referenceNo' },
            { label: 'Status', key: 'status' },
        ]);
        sendCSV(res, csv, `investments_export_${Date.now()}.csv`);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Export payment schedules
router.get('/export/payment-schedules', async (req, res) => {
    try {
        const schedules = await PaymentSchedule.findAll({
            include: [
                { model: Investor, as: 'investor' },
                { model: Project, as: 'project' },
            ],
            order: [['dueDate', 'ASC']],
        });
        const csv = toCSV(schedules.map(s => s.toJSON()), [
            { label: 'ID', key: 'id' },
            { label: 'Investor', key: 'investor.name' },
            { label: 'Project', key: 'project.name' },
            { label: 'Amount', key: 'amount' },
            { label: 'Due Date', key: 'dueDate' },
            { label: 'Status', key: 'status' },
            { label: 'Paid Date', key: 'paidDate' },
            { label: 'Notes', key: 'notes' },
        ]);
        sendCSV(res, csv, `payment_schedules_export_${Date.now()}.csv`);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

module.exports = router;
